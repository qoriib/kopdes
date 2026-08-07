import os
import sys
import json
import base64
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Set matplotlib to run without GUI (headless)
import matplotlib
matplotlib.use('Agg')

PREPROCESS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "preprocess")
DATA_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "model")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

SCALED_FEATURES_CSV = os.path.join(PREPROCESS_DIR, "scaled_features.csv")
CLUSTERED_REGENCIES_CSV = os.path.join(DATA_MODEL_DIR, "clustered_regencies.csv")

MODEL_METRICS_JSON = os.path.join(REPORTS_DIR, "evaluate_metrics.json")
CLUSTERING_REPORT_MD = os.path.join(REPORTS_DIR, "evaluate_report.md")

FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")

def generate_base64_plot(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def save_plot_to_file(fig, filepath):
    """Save a matplotlib figure to a PNG file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, format='png', dpi=120, bbox_inches='tight')
    print(f"[SAVED] Plot -> {filepath}")

def main():
    print("[+] Memulai Stage Evaluasi Model Clustering yang Dikembangkan...")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    if not os.path.exists(CLUSTERED_REGENCIES_CSV) or not os.path.exists(SCALED_FEATURES_CSV):
        print("[-] File model clustering atau scaled features tidak ditemukan. Jalankan pipeline model terlebih dahulu.")
        sys.exit(1)

    df_clustered = pd.read_csv(CLUSTERED_REGENCIES_CSV)
    df_scaled = pd.read_csv(SCALED_FEATURES_CSV)
    X_scaled = df_scaled.values
    labels = df_clustered['cluster_label'].values

    # 1. Menghitung Evaluasi Performa Klaster
    sil_score = round(float(silhouette_score(X_scaled, labels)), 4)
    ch_score = round(float(calinski_harabasz_score(X_scaled, labels)), 2)
    db_score = round(float(davies_bouldin_score(X_scaled, labels)), 4)

    print(f"[*] Silhouette Score        : {sil_score}")
    print(f"[*] Calinski-Harabasz Index : {ch_score}")
    print(f"[*] Davies-Bouldin Index    : {db_score}")

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
    print(f"[SAVED] DVC Model Metrics -> {MODEL_METRICS_JSON}")

    # 3. Profiling Klaster (Rata-rata per klaster)
    cluster_profile = df_clustered.groupby('cluster_label').agg({
        'jumlah_koperasi': 'mean',
        'koperasi_nib': 'mean',
        'koperasi_npwp': 'mean',
        'koperasi_rat': 'mean',
        'nilai_transaksi': 'mean'
    }).round(2)

    # 4. Generate Visualizations
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    # Plot 1: 2D PCA Projection
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    df_pca = pd.DataFrame(X_pca, columns=['PCA1', 'PCA2'])
    df_pca['cluster'] = labels

    fig1, ax1 = plt.subplots(figsize=(8, 6))
    unique_labels = np.unique(labels)
    colors = matplotlib.colormaps['tab10']
    
    for i, cluster in enumerate(unique_labels):
        c_data = df_pca[df_pca['cluster'] == cluster]
        ax1.scatter(c_data['PCA1'], c_data['PCA2'], label=f'Klaster {cluster}', color=colors(i), alpha=0.7, edgecolors='w', s=50)

    ax1.set_title('Proyeksi 2D Hasil Clustering KMeans (Metode PCA)', fontsize=14, pad=15, fontweight='bold', color='#2c3e50')
    ax1.set_xlabel('Principal Component 1', fontsize=11, fontweight='bold', color='#2c3e50')
    ax1.set_ylabel('Principal Component 2', fontsize=11, fontweight='bold', color='#2c3e50')
    ax1.legend(loc='best', frameon=True, facecolor='white', edgecolor='none')
    fig1.tight_layout()
    save_plot_to_file(fig1, os.path.join(FIGURES_DIR, "eval_pca_projection.png"))
    img_pca_b64 = generate_base64_plot(fig1)

    # Plot 2: Cluster Membership Counts
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    cluster_counts = df_clustered['cluster_label'].value_counts().sort_index()
    colors2 = matplotlib.colormaps['Set2']
    bars2 = ax2.bar(cluster_counts.index.map(lambda x: f"Klaster {x}"), cluster_counts.values, color=colors2(np.arange(len(unique_labels))), edgecolor='none', width=0.5)
    ax2.set_title('Distribusi Jumlah Kabupaten/Kota per Klaster', fontsize=14, pad=15, fontweight='bold', color='#2c3e50')
    ax2.set_ylabel('Jumlah Kabupaten/Kota', fontsize=11, fontweight='bold', color='#2c3e50')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color('#cccccc')
    ax2.spines['bottom'].set_color('#cccccc')
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, height + (height * 0.01) + 1, f"{int(height)}", 
                 va='bottom', ha='center', fontsize=10, fontweight='bold', color='#34495e')
    fig2.tight_layout()
    save_plot_to_file(fig2, os.path.join(FIGURES_DIR, "eval_cluster_distribution.png"))
    img_dist_b64 = generate_base64_plot(fig2)

    # Plot 3: Average Transaction Value per Cluster
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    colors3 = matplotlib.colormaps['Accent']
    bars3 = ax3.bar(cluster_profile.index.map(lambda x: f"Klaster {x}"), cluster_profile['nilai_transaksi'] / 1e6, color=colors3(np.arange(len(unique_labels))), edgecolor='none', width=0.5)
    ax3.set_title('Rata-Rata Nilai Transaksi per Klaster (Juta Rp)', fontsize=14, pad=15, fontweight='bold', color='#2c3e50')
    ax3.set_ylabel('Nilai Transaksi (Juta Rp)', fontsize=11, fontweight='bold', color='#2c3e50')
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_color('#cccccc')
    ax3.spines['bottom'].set_color('#cccccc')
    for bar in bars3:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2, height + (height * 0.01), f"{height:,.2f}", 
                 va='bottom', ha='center', fontsize=10, fontweight='bold', color='#34495e')
    fig3.tight_layout()
    save_plot_to_file(fig3, os.path.join(FIGURES_DIR, "eval_avg_transaction.png"))
    img_trans_b64 = generate_base64_plot(fig3)

    # 4. Laporan Markdown Evaluasi Formal
    md_content = f"""# Laporan Evaluasi Pengelompokan (Clustering) KMeans SIMKOPDES

Laporan ini menyajikan hasil evaluasi kuantitatif dan analisis profil klaster kabupaten/kota berbasis algoritma KMeans.

---

## 1. Evaluasi Kinerja Pengelompokan

| Metrik Evaluasi | Nilai Kinerja | Keterangan |
| :--- | :--- | :--- |
| **Silhouette Score** | **{sil_score}** | Mengukur seberapa serupa objek dengan klasternya sendiri dibandingkan klaster lain (Range: -1 s.d. +1, semakin tinggi semakin baik) |
| **Calinski-Harabasz Index** | **{ch_score}** | Rasio dispersi antar-klaster terhadap dalam-klaster (semakin tinggi semakin baik) |
| **Davies-Bouldin Index** | **{db_score}** | Mengukur rata-rata kesamaan tiap klaster dengan klaster paling serupa (semakin rendah semakin baik) |
| **Jumlah Klaster Terbentuk** | **{len(set(labels))}** | Hasil optimasi dari KElbowVisualizer |

---

## 2. Visualisasi Pengelompokan dan Kinerja

### A. Proyeksi 2D Klaster (PCA)
![Proyeksi PCA 2D](data:image/png;base64,{img_pca_b64})

### B. Distribusi Anggota Klaster
![Distribusi Anggota](data:image/png;base64,{img_dist_b64})

### C. Rata-Rata Nilai Transaksi Keuangan per Klaster
![Rata-rata Nilai Transaksi](data:image/png;base64,{img_trans_b64})

---

## 3. Profil Rata-Rata per Klaster

| Klaster | Rata-rata Jumlah Koperasi | Rata-rata Koperasi NIB | Rata-rata Koperasi NPWP | Rata-rata Koperasi RAT | Rata-rata Nilai Transaksi (Rp) |
| :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for cluster_id, row in cluster_profile.iterrows():
        md_content += f"| **Klaster {cluster_id}** | {row['jumlah_koperasi']:,} | {row['koperasi_nib']:,} | {row['koperasi_npwp']:,} | {row['koperasi_rat']:,} | Rp {row['nilai_transaksi']:,} |\n"

    md_content += "\n---\n\n## 4. Distribusi Anggota Klaster\n\n"
    for cluster_id, count in cluster_counts.items():
        md_content += f"- **Klaster {cluster_id}**: {count} Kabupaten/Kota\n"

    with open(CLUSTERING_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[SAVED] Laporan Markdown Clustering -> {CLUSTERING_REPORT_MD}")

    print("[DONE] Stage Evaluasi selesai.")

if __name__ == "__main__":
    main()
