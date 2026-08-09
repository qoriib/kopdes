# Laporan Preprocessing

Laporan ini menyajikan hasil standarisasi fitur dan pencarian nilai klaster optimal (K) menggunakan metode Elbow.

## 1. Parameter Penentuan K Optimal (Kneedle Algorithm)

- **K Terbaik Terdeteksi**: **K = {{optimal_k}}**
- **Metode Pendeteksian**: KneeLocator (`kneed`)
- **Jenis Standarisasi**: StandardScaler

## 2. Nilai WCSS (Within-Cluster Sum of Squares)

| Nilai K | Nilai Inertia (WCSS) |
| :---: | :---: |
{{wcss_table_rows}}

## 3. Kurva Elbow Visualisasi
<img src="figures/preprocess_elbow_curve.png" alt="Kurva Elbow" width="300">
