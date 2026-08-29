import os
import json
import dvc.api
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA
from utils.plot_utils import save_plot_to_file
from utils.log_utils import get_logger
from utils.report_utils import generate_report_from_template
from config import (
    SCALED_FEATURES_CSV,
    CLUSTERED_REGENCIES_CSV,
    MODEL_METRICS_JSON,
    CLUSTERING_REPORT_MD,
    CLUSTERING_REPORT_TEMPLATE_MD,
    FIGURES_DIR
)

logger = get_logger("evaluate")
params = dvc.api.params_show().get('model', {})

SELECTED_FEATURES = params.get('selected_features', [])
IGNORED_FEATURES = ['cluster_label', 'regency_name', 'province_name', 'No', 'Province_ID']

def generate_cluster_profile(df_clustered: pd.DataFrame, active_features: list) -> pd.DataFrame:
    """
    Menghitung profil statistik deskriptif per klaster secara dinamis.
    - Fitur Numerik  : Menggunakan Rata-Rata (mean)
    - Fitur Kategorik: Menggunakan Modus (mode)
    """
    num_cols = df_clustered[active_features].select_dtypes(include=['number']).columns.tolist()
    cat_cols = df_clustered[active_features].select_dtypes(include=['object', 'category']).columns.tolist()

    # Hitung rata-rata untuk fitur numerik
    if num_cols:
        profile_num = df_clustered.groupby('cluster_label')[num_cols].mean().round(2)
    else:
        profile_num = pd.DataFrame(index=sorted(df_clustered['cluster_label'].unique()))

    # Hitung modus untuk fitur kategorik
    if cat_cols:
        profile_cat = df_clustered.groupby('cluster_label')[cat_cols].agg(
            lambda x: x.mode()[0] if not x.mode().empty else "N/A"
        )
        return pd.concat([profile_num, profile_cat], axis=1)

    return profile_num

def build_markdown_table(cluster_profile: pd.DataFrame) -> str:
    """
    Membangun string tabel Markdown lengkap (header, separator, dan baris data)
    berdasarkan DataFrame profil klaster.
    """
    headers = ["Klaster"] + [col.replace("_", " ").title() for col in cluster_profile.columns]
    header_row = "| " + " | ".join(headers) + " |\n"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |\n"
    
    body_rows = ""
    for cluster_id, row in cluster_profile.iterrows():
        formatted_vals = []
        for val in row.values:
            if isinstance(val, (int, float)):
                formatted_vals.append(f"{val:,.2f}" if isinstance(val, float) else f"{val:,}")
            else:
                formatted_vals.append(str(val))
        body_rows += f"| **Klaster {cluster_id}** | " + " | ".join(formatted_vals) + " |\n"

    return header_row + separator_row + body_rows

def main():
    logger.info("Memulai Stage Evaluasi Model Clustering yang Dikembangkan...")

    df_clustered = pd.read_csv(CLUSTERED_REGENCIES_CSV)
    df_scaled = pd.read_csv(SCALED_FEATURES_CSV)
    
    # 1. Menentukan Fitur Terpilih untuk Scaling & Profiling
    if SELECTED_FEATURES:
        scaled_cols = [f"scaled_{col}" for col in SELECTED_FEATURES if f"scaled_{col}" in df_scaled.columns]
        if not scaled_cols:
            logger.warning("Fitur terukur tidak ditemukan. Menggunakan seluruh fitur scaled.")
            X_scaled = df_scaled.values
        else:
            X_scaled = df_scaled[scaled_cols].values
        active_features = [col for col in SELECTED_FEATURES if col in df_clustered.columns]
    else:
        X_scaled = df_scaled.values
        active_features = [col for col in df_clustered.columns if col not in IGNORED_FEATURES]

    labels = df_clustered['cluster_label'].values

    # 2. Menghitung Metrik Performa Clustering
    sil_score = round(float(silhouette_score(X_scaled, labels)), 4)
    ch_score = round(float(calinski_harabasz_score(X_scaled, labels)), 2)
    db_score = round(float(davies_bouldin_score(X_scaled, labels)), 4)

    logger.info(f"Silhouette Score        : {sil_score}")
    logger.info(f"Calinski-Harabasz Index : {ch_score}")
    logger.info(f"Davies-Bouldin Index    : {db_score}")

    # 3. Simpan DVC Metrics JSON
    metrics = {
        "clustering_metrics": {
            "silhouette_score": sil_score,
            "calinski_harabasz_score": ch_score,
            "davies_bouldin_score": db_score,
        }
    }

    with open(MODEL_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    logger.info(f"DVC Model Metrics -> {MODEL_METRICS_JSON}")

    # 4. Profiling Klaster (Rata-rata per klaster)
    cluster_profile = generate_cluster_profile(df_clustered, active_features)

    # 5. Pembuatan Visualisasi Plot
    # Plot 1: 2D PCA Projection
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    df_pca = pd.DataFrame(X_pca, columns=['PCA1', 'PCA2'])
    df_pca['cluster'] = labels

    plt.figure(figsize=(8, 6))
    sns.scatterplot(x='PCA1', y='PCA2', hue='cluster', data=df_pca, palette='tab10')
    plt.title('Proyeksi 2D Hasil Clustering KMeans (Metode PCA)')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.legend(title='Klaster')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "eval_pca_projection.png"))
    plt.close()

    # Plot 2: Cluster Membership Counts
    cluster_counts = df_clustered['cluster_label'].value_counts().sort_index()
    
    plt.figure(figsize=(8, 4))
    sns.barplot(x=cluster_counts.index.map(lambda x: f"Klaster {x}"), y=cluster_counts.values)
    plt.title('Distribusi Jumlah Kabupaten/Kota per Klaster')
    plt.ylabel('Jumlah Kabupaten/Kota')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "eval_cluster_distribution.png"))
    plt.close()

    # Plot 3: Chart Fitur Utama
    num_cols = df_clustered[active_features].select_dtypes(include=['number']).columns.tolist()
    if num_cols:
        target_chart_col = 'nilai_transaksi' if 'nilai_transaksi' in num_cols else num_cols[0]
        plt.figure(figsize=(8, 4))
        sns.barplot(x=cluster_profile.index.map(lambda x: f"Klaster {x}"), y=cluster_profile[target_chart_col])
        plt.title(f'Rata-Rata {target_chart_col.replace("_", " ").title()} per Klaster')
        plt.ylabel(target_chart_col.replace("_", " ").title())
        plt.tight_layout()
        plt.savefig(os.path.join(FIGURES_DIR, "eval_avg_transaction.png"))
        plt.close()

    # 6. Menyusun String Tabel Markdown Menggunakan Fungsi Terpisah
    cluster_profile_rows = build_markdown_table(cluster_profile)

    cluster_distribution_rows = ""
    for cluster_id, count in cluster_counts.items():
        cluster_distribution_rows += f"- **Klaster {cluster_id}**: {count} Kabupaten/Kota\n"

    replacements = {
        "{{sil_score}}": str(sil_score),
        "{{ch_score}}": str(ch_score),
        "{{db_score}}": str(db_score),
        "{{cluster_profile_rows}}": cluster_profile_rows,
        "{{cluster_distribution_rows}}": cluster_distribution_rows,
    }
    
    generate_report_from_template(CLUSTERING_REPORT_TEMPLATE_MD, CLUSTERING_REPORT_MD, replacements)

    logger.info("Stage Evaluasi selesai.")

if __name__ == "__main__":
    main()
