import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA

from config import (
    SCALED_FEATURES_CSV,
    CLUSTERED_REGENCIES_CSV,
    MODEL_METRICS_JSON,
    CLUSTERING_REPORT_MD,
    REPORTS_DIR,
    FIGURES_DIR
)
from utils.plot_utils import generate_base64_plot, save_plot_to_file
from utils.log_utils import get_logger

logger = get_logger("evaluate")

def main():
    logger.info("Memulai Stage Evaluasi Model Clustering yang Dikembangkan...")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    if not os.path.exists(CLUSTERED_REGENCIES_CSV) or not os.path.exists(SCALED_FEATURES_CSV):
        logger.error("File model clustering atau scaled features tidak ditemukan. Jalankan pipeline model terlebih dahulu.")
        sys.exit(1)

    df_clustered = pd.read_csv(CLUSTERED_REGENCIES_CSV)
    df_scaled = pd.read_csv(SCALED_FEATURES_CSV)
    X_scaled = df_scaled.values
    labels = df_clustered['cluster_label'].values

    # 1. Menghitung Evaluasi Performa Klaster
    sil_score = round(float(silhouette_score(X_scaled, labels)), 4)
    ch_score = round(float(calinski_harabasz_score(X_scaled, labels)), 2)
    db_score = round(float(davies_bouldin_score(X_scaled, labels)), 4)

    logger.info(f"Silhouette Score        : {sil_score}")
    logger.info(f"Calinski-Harabasz Index : {ch_score}")
    logger.info(f"Davies-Bouldin Index    : {db_score}")

    # 2. Simpan DVC Metrics JSON
    metrics = {
        "clustering_metrics": {
            "silhouette_score": sil_score,
            "calinski_harabasz_score": ch_score,
            "davies_bouldin_score": db_score,
            "number_of_clusters": int(len(set(labels)))
        }
    }
    with open(MODEL_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"DVC Model Metrics -> {MODEL_METRICS_JSON}")

    # 3. Profiling Klaster (Rata-rata per klaster)
    cluster_profile = df_clustered.groupby('cluster_label').agg({
        'jumlah_koperasi': 'mean',
        'koperasi_nib': 'mean',
        'koperasi_npwp': 'mean',
        'koperasi_rat': 'mean',
        'nilai_transaksi': 'mean'
    }).round(2)

    # Generate Visualizations using standard seaborn defaults
    sns.set_theme()

    # Plot 1: 2D PCA Projection
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    df_pca = pd.DataFrame(X_pca, columns=['PCA1', 'PCA2'])
    df_pca['cluster'] = labels

    fig1, ax1 = plt.subplots(figsize=(8, 6))
    sns.scatterplot(x='PCA1', y='PCA2', hue='cluster', data=df_pca, palette='tab10', ax=ax1)

    ax1.set_title('Proyeksi 2D Hasil Clustering KMeans (Metode PCA)')
    ax1.set_xlabel('Principal Component 1')
    ax1.set_ylabel('Principal Component 2')
    ax1.legend(title='Klaster')
    fig1.tight_layout()
    save_plot_to_file(fig1, os.path.join(FIGURES_DIR, "eval_pca_projection.png"))
    img_pca_b64 = generate_base64_plot(fig1)

    # Plot 2: Cluster Membership Counts
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    cluster_counts = df_clustered['cluster_label'].value_counts().sort_index()
    sns.barplot(x=cluster_counts.index.map(lambda x: f"Klaster {x}"), y=cluster_counts.values, ax=ax2)
    ax2.set_title('Distribusi Jumlah Kabupaten/Kota per Klaster')
    ax2.set_ylabel('Jumlah Kabupaten/Kota')
    fig2.tight_layout()
    save_plot_to_file(fig2, os.path.join(FIGURES_DIR, "eval_cluster_distribution.png"))
    img_dist_b64 = generate_base64_plot(fig2)

    # Plot 3: Average Transaction Value per Cluster
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    sns.barplot(x=cluster_profile.index.map(lambda x: f"Klaster {x}"), y=cluster_profile['nilai_transaksi'] / 1e6, ax=ax3)
    ax3.set_title('Rata-Rata Nilai Transaksi per Klaster (Juta Rp)')
    ax3.set_ylabel('Nilai Transaksi (Juta Rp)')
    fig3.tight_layout()
    save_plot_to_file(fig3, os.path.join(FIGURES_DIR, "eval_avg_transaction.png"))
    img_trans_b64 = generate_base64_plot(fig3)

    # 4. Laporan Markdown Evaluasi Formal
    md_content = f"""# Laporan Evaluasi Pengelompokan (Clustering) KMeans SIMKOPDES

Laporan ini menyajikan hasil evaluasi kuantitatif dan analisis profil klaster kabupaten/kota berbasis algoritma KMeans.

## 1. Evaluasi Kinerja Pengelompokan

| Metrik Evaluasi | Nilai Kinerja | Keterangan |
| :--- | :--- | :--- |
| **Silhouette Score** | **{sil_score}** | Mengukur seberapa serupa objek dengan klasternya sendiri dibandingkan klaster lain (Range: -1 s.d. +1, semakin tinggi semakin baik) |
| **Calinski-Harabasz Index** | **{ch_score}** | Rasio dispersi antar-klaster terhadap dalam-klaster (semakin tinggi semakin baik) |
| **Davies-Bouldin Index** | **{db_score}** | Mengukur rata-rata kesamaan tiap klaster dengan klaster paling serupa (semakin rendah semakin baik) |
| **Jumlah Klaster Terbentuk** | **{len(set(labels))}** | Hasil optimasi dari KElbowVisualizer |

## 2. Visualisasi Pengelompokan dan Kinerja

### A. Proyeksi 2D Klaster (PCA)
<img src="data:image/png;base64,{img_pca_b64}" alt="Proyeksi PCA 2D" width="300">

### B. Distribusi Anggota Klaster
<img src="data:image/png;base64,{img_dist_b64}" alt="Distribusi Anggota" width="300">

### C. Rata-Rata Nilai Transaksi Keuangan per Klaster
<img src="data:image/png;base64,{img_trans_b64}" alt="Rata-rata Nilai Transaksi" width="300">

## 3. Profil Rata-Rata per Klaster

| Klaster | Rata-rata Jumlah Koperasi | Rata-rata Koperasi NIB | Rata-rata Koperasi NPWP | Rata-rata Koperasi RAT | Rata-rata Nilai Transaksi (Rp) |
| :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for cluster_id, row in cluster_profile.iterrows():
        md_content += f"| **Klaster {cluster_id}** | {row['jumlah_koperasi']:,} | {row['koperasi_nib']:,} | {row['koperasi_npwp']:,} | {row['koperasi_rat']:,} | Rp {row['nilai_transaksi']:,} |\n"

    md_content += "\n\n## 4. Distribusi Anggota Klaster\n\n"
    for cluster_id, count in cluster_counts.items():
        md_content += f"- **Klaster {cluster_id}**: {count} Kabupaten/Kota\n"

    with open(CLUSTERING_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info(f"Laporan Markdown Clustering -> {CLUSTERING_REPORT_MD}")

    logger.info("Stage Evaluasi selesai.")

if __name__ == "__main__":
    main()
