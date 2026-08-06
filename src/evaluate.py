import os
import sys
import json
import pandas as pd
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PREPROCESS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "preprocess")
DATA_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "model")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

SCALED_FEATURES_CSV = os.path.join(PREPROCESS_DIR, "scaled_features.csv")
CLUSTERED_REGENCIES_CSV = os.path.join(DATA_MODEL_DIR, "clustered_regencies.csv")

MODEL_METRICS_JSON = os.path.join(REPORTS_DIR, "model_metrics.json")
CLUSTERING_REPORT_MD = os.path.join(REPORTS_DIR, "clustering_report.md")

def main():
    print("[+] Memulai Stage Evaluasi Model Clustering...")
    os.makedirs(REPORTS_DIR, exist_ok=True)

    df_clustered = pd.read_csv(CLUSTERED_REGENCIES_CSV)
    X_scaled = pd.read_csv(SCALED_FEATURES_CSV).values
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

## 2. Profil Rata-Rata per Klaster

| Klaster | Rata-rata Jumlah Koperasi | Rata-rata Koperasi NIB | Rata-rata Koperasi NPWP | Rata-rata Koperasi RAT | Rata-rata Nilai Transaksi (Rp) |
| :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for cluster_id, row in cluster_profile.iterrows():
        md_content += f"| **Klaster {cluster_id}** | {row['jumlah_koperasi']:,} | {row['koperasi_nib']:,} | {row['koperasi_npwp']:,} | {row['koperasi_rat']:,} | Rp {row['nilai_transaksi']:,} |\n"

    md_content += "\n---\n\n## 3. Distribusi Anggota Klaster\n\n"
    cluster_counts = df_clustered['cluster_label'].value_counts().sort_index()
    for cluster_id, count in cluster_counts.items():
        md_content += f"- **Klaster {cluster_id}**: {count} Kabupaten/Kota\n"

    with open(CLUSTERING_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[SAVED] Laporan Markdown Clustering -> {CLUSTERING_REPORT_MD}")

    print("[DONE] Stage Evaluasi selesai.")

if __name__ == "__main__":
    main()
