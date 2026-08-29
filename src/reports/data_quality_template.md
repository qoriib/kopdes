# Laporan Verifikasi Kualitas Data (*Data Quality Report*)

Dokumen ini merupakan laporan luaran dari tugas generik **Verify Data Quality** pada kerangka kerja **CRISP-DM 1.0 (Chapman et al., 2000)** dan metodologi jaminan kualitas **CRISP-ML(Q) (Studer et al., 2020)**.

---

## 1. Pengujian Kelengkapan (*Completeness Check*)

- **Total Observasi**: {{total_samples}} baris data kabupaten/kota.
- **Deteksi Missing Values (NaN/Null)**:
{{missing_values_table}}

- **Evaluasi Kelengkapan**: Seluruh baris data memiliki representasi nilai terstruktur. Nilai kosong/nol pada transaksi dan simpanan merepresentasikan ketiadaan aktivitas usaha pada wilayah terkait.

---

## 2. Pengujian Keunikan & Duplikasi (*Uniqueness Check*)

- **Duplikasi Observasi Baris**: **{{duplicate_rows_count}}** baris duplikat ditemukan.
- **Keunikan Identitas Wilayah (Province ID + Regency No)**: **{{duplicate_keys_count}}** duplikasi kunci ditemukan (100% unik).

---

## 3. Pengujian Konsistensi Format Penulisan Wilayah (*Consistency Check*)

- **Status Standardisasi Huruf Kapital**: **{{naming_consistency_status}}**
- **Cakupan Spasial Geografis**: Seluruh 514 kabupaten/kota terpetakan pada 38 provinsi di Indonesia.

---

## 4. Pengujian Distribusi, Kemiringan (*Skewness*), dan Deteksi Pencilan (*Outlier Check*)

Deteksi nilai pencilan dilakukan menggunakan metode statistik **Interquartile Range (IQR)** dengan batas $Q_1 - 1.5 \times IQR$ dan $Q_3 + 1.5 \times IQR$:

{{outlier_summary_table}}

---

## 5. Matriks Rekomendasi Penanganan Kualitas Data (*Actionable Recommendations for Data Preparation*)

Berdasarkan temuan verifikasi kualitas data, strategi berikut ditetapkan untuk dieksekusi pada tahap **Data Preparation**:

| Masalah Kualitas Data | Dampak pada K-Means | Strategi Penanganan pada *Data Preparation* |
| :--- | :--- | :--- |
| **Pemisahan Metadata Identitas** | Distorsi perhitungan jarak Euclidean | Memisahkan `province_id`, `regency_no`, `regency_name`, `latitude`, `longitude` sebagai metadata |
| **Nilai Kosong / Nol Lokal** | Bias estimasi statistik | Imputasi nilai kosong berbasis **median lokal per provinsi** |
| **Kemiringan Distribusi Ekstrem (*Skewness > 1.0*)** | Klaster didominasi oleh segelintir pencilan | **Transformasi Logaritmik Natural ($\ln(1+x)$)** pada fitur finansial |
| **Perbedaan Skala & Magnitudo Variabel** | Fitur bernilai triliunan mendominasi fitur rasio persentase | **Standarisasi Z-Score (`StandardScaler`)** sehingga $\mu=0, \sigma=1$ |
