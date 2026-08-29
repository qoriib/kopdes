import os
import json
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA

from utils.log_utils import get_logger
from utils.config_utils import get_params
from utils.report_utils import generate_report_from_template
from config import (
    SCALED_FEATURES_CSV,
    CLUSTERED_REGENCIES_CSV,
    EVALUATE_METRICS_JSON,
    EVALUATE_REPORT_MD,
    EVALUATE_REPORT_TEMPLATE_MD,
    FIGURES_DIR,
    IGNORED_METADATA_COLUMNS
)

logger = get_logger("evaluation.metrics")

def generate_cluster_profile(df_clustered: pd.DataFrame, active_features: list) -> pd.DataFrame:
    num_cols = [c for c in active_features if c in df_clustered.columns and np.issubdtype(df_clustered[c].dtype, np.number)]
    if num_cols:
        return df_clustered.groupby('cluster_label')[num_cols].mean().round(2)
    return pd.DataFrame(index=sorted(df_clustered['cluster_label'].unique()))

def build_markdown_table(cluster_profile: pd.DataFrame) -> str:
    headers = ["Klaster"] + [col.replace("_", " ").title() for col in cluster_profile.columns]
    header_row = "| " + " | ".join(headers) + " |\n"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |\n"

    body_rows = ""
    for cluster_id, row in cluster_profile.iterrows():
        formatted_vals = []
        for col_name, val in row.items():
            if isinstance(val, (int, float)):
                if "nilai" in col_name or "simpanan" in col_name:
                    formatted_vals.append(f"Rp {val:,.2f}")
                elif "rasio" in col_name:
                    formatted_vals.append(f"{val:.2f}%")
                else:
                    formatted_vals.append(f"{val:,.2f}" if isinstance(val, float) else f"{val:,}")
            else:
                formatted_vals.append(str(val))
        body_rows += f"| **Klaster {cluster_id}** | " + " | ".join(formatted_vals) + " |\n"

    return header_row + separator_row + body_rows

def run_metrics():
    logger.info("Menjalankan CRISP-DM: Evaluation - Metrics Calculation & Visualizations...")

    m_params = get_params('modeling')
    e_params = get_params('evaluation')
    selected_features = m_params.get('selected_features', [])
    target_silhouette_min = e_params.get('target_silhouette_min', 0.50)

    if not os.path.exists(CLUSTERED_REGENCIES_CSV) or not os.path.exists(SCALED_FEATURES_CSV):
        raise FileNotFoundError("Data terklasterisasi atau scaled features tidak ditemukan.")

    df_clustered = pd.read_csv(CLUSTERED_REGENCIES_CSV)
    df_scaled = pd.read_csv(SCALED_FEATURES_CSV)

    if selected_features:
        scaled_cols = [f"scaled_{col}" for col in selected_features if f"scaled_{col}" in df_scaled.columns]
        if not scaled_cols:
            X_scaled = df_scaled.values
        else:
            X_scaled = df_scaled[scaled_cols].values
        active_features = [col for col in selected_features if col in df_clustered.columns]
    else:
        X_scaled = df_scaled.values
        active_features = [col for col in df_clustered.columns if col not in IGNORED_METADATA_COLUMNS]

    labels = df_clustered['cluster_label'].values

    # Perhitungan Metrik Evaluasi Internal
    sil_score = round(float(silhouette_score(X_scaled, labels)), 4)
    ch_score = round(float(calinski_harabasz_score(X_scaled, labels)), 2)
    db_score = round(float(davies_bouldin_score(X_scaled, labels)), 4)
    num_clusters = len(np.unique(labels))

    logger.info(f"Jumlah Klaster (K)       : {num_clusters}")
    logger.info(f"Silhouette Coefficient   : {sil_score} (Target: >={target_silhouette_min})")
    logger.info(f"Davies-Bouldin Index     : {db_score} (Mendekati 0)")
    logger.info(f"Calinski-Harabasz Index  : {ch_score} (Maksimal)")

    # Simpan Evaluasi Metrik JSON
    metrics = {
        "clustering_metrics": {
            "number_of_clusters": num_clusters,
            "silhouette_score": sil_score,
            "calinski_harabasz_score": ch_score,
            "davies_bouldin_score": db_score,
            "target_silhouette_achieved": bool(sil_score >= target_silhouette_min)
        }
    }

    os.makedirs(os.path.dirname(EVALUATE_METRICS_JSON), exist_ok=True)
    with open(EVALUATE_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Metrics JSON -> {EVALUATE_METRICS_JSON}")

    # Profiling Klaster
    cluster_profile = generate_cluster_profile(df_clustered, active_features)

    # Visualisasi
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # Plot 1: 2D PCA Projection
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    df_pca = pd.DataFrame(X_pca, columns=['PCA1', 'PCA2'])
    df_pca['cluster'] = [f"Klaster {lbl}" for lbl in labels]

    plt.figure(figsize=(8, 6))
    sns.scatterplot(x='PCA1', y='PCA2', hue='cluster', data=df_pca, palette='tab10', s=60, alpha=0.85)
    plt.title('Proyeksi 2D Klasterisasi Wilayah (Principal Component Analysis)')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.legend(title='Klaster')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "eval_pca_projection.png"))
    plt.close()

    # Plot 2: Cluster Membership Counts
    cluster_counts = df_clustered['cluster_label'].value_counts().sort_index()

    plt.figure(figsize=(8, 4.5))
    sns.barplot(x=cluster_counts.index.map(lambda x: f"Klaster {x}"), y=cluster_counts.values, palette='Blues_r')
    plt.title('Distribusi Jumlah Anggota Kabupaten/Kota per Klaster')
    plt.ylabel('Jumlah Kabupaten/Kota')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "eval_cluster_distribution.png"))
    plt.close()

    # Plot 3: Rata-rata Nilai Transaksi
    if 'nilai_transaksi' in cluster_profile.columns:
        plt.figure(figsize=(8, 4.5))
        sns.barplot(x=cluster_profile.index.map(lambda x: f"Klaster {x}"), y=cluster_profile['nilai_transaksi'] / 1e6, palette='viridis')
        plt.title('Rata-Rata Nilai Transaksi per Klaster (Juta Rp)')
        plt.ylabel('Nilai Transaksi (Juta Rp)')
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, "eval_avg_transaction.png"))
        plt.close()

    # Markdown Report
    cluster_profile_rows = build_markdown_table(cluster_profile)

    cluster_distribution_rows = ""
    for cluster_id, count in cluster_counts.items():
        pct = round((count / len(df_clustered)) * 100, 2)
        cluster_distribution_rows += f"- **Klaster {cluster_id}**: {count} Kabupaten/Kota ({pct}%)\n"

    replacements = {
        "{{sil_score}}": str(sil_score),
        "{{ch_score}}": str(ch_score),
        "{{db_score}}": str(db_score),
        "{{num_clusters}}": str(num_clusters),
        "{{cluster_profile_rows}}": cluster_profile_rows,
        "{{cluster_distribution_rows}}": cluster_distribution_rows,
    }

    generate_report_from_template(EVALUATE_REPORT_TEMPLATE_MD, EVALUATE_REPORT_MD, replacements)
    logger.info(f"Evaluation Report -> {EVALUATE_REPORT_MD}")

def main():
    run_metrics()

if __name__ == "__main__":
    main()
