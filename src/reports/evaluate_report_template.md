# Laporan Evaluasi Pengelompokan (Clustering) KMeans SIMKOPDES

Laporan ini menyajikan hasil evaluasi kuantitatif dan analisis profil klaster kabupaten/kota berbasis algoritma KMeans.

## 1. Evaluasi Kinerja Pengelompokan

| Metrik Evaluasi | Nilai Kinerja | Keterangan |
| :--- | :--- | :--- |
| **Silhouette Score** | **{{sil_score}}** | Mengukur seberapa serupa objek dengan klasternya sendiri dibandingkan klaster lain (Range: -1 s.d. +1, semakin tinggi semakin baik) |
| **Calinski-Harabasz Index** | **{{ch_score}}** | Rasio dispersi antar-klaster terhadap dalam-klaster (semakin tinggi semakin baik) |
| **Davies-Bouldin Index** | **{{db_score}}** | Mengukur rata-rata kesamaan tiap klaster dengan klaster paling serupa (semakin rendah semakin baik) |
| **Jumlah Klaster Terbentuk** | **{{num_clusters}}** | Hasil optimasi dari KElbowVisualizer |

## 2. Visualisasi Pengelompokan dan Kinerja

### A. Proyeksi 2D Klaster (PCA)
<img src="figures/eval_pca_projection.png" alt="Proyeksi PCA 2D" width="300">

### B. Distribusi Anggota Klaster
<img src="figures/eval_cluster_distribution.png" alt="Distribusi Anggota" width="300">

### C. Rata-Rata Nilai Transaksi Keuangan per Klaster
<img src="figures/eval_avg_transaction.png" alt="Rata-rata Nilai Transaksi" width="300">

## 3. Profil Rata-Rata per Klaster

| Klaster | Rata-rata Jumlah Koperasi | Rata-rata Koperasi NIB | Rata-rata Koperasi NPWP | Rata-rata Koperasi RAT | Rata-rata Nilai Transaksi (Rp) |
| :---: | :---: | :---: | :---: | :---: | :---: |
{{cluster_profile_rows}}

## 4. Distribusi Anggota Klaster

{{cluster_distribution_rows}}
