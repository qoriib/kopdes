# Laporan Eksplorasi Data (*Data Exploration Report / EDA*)

Dokumen ini merupakan laporan luaran dari tugas generik **Explore Data** pada kerangka kerja **CRISP-DM 1.0 (Chapman et al., 2000)** untuk menjawab tujuan analitis terkait sebaran indikator kinerja KDMP, korelasi antar-variabel, dan pola disparitas wilayah antar-kabupaten/kota di Indonesia.

---

## 1. Ringkasan Indikator Kinerja Nasional

| Indikator Nasional | Nilai Agregat | Persentase Kepatuhan / Keterangan |
| :--- | :--- | :--- |
| **Total Kabupaten/Kota** | **{{total_regencies}} Wilayah** | 38 Provinsi |
| **Total Koperasi Terdaftar** | **{{total_koperasi}} Unit** | 100% |
| **Kepemilikan NIB** | **{{total_nib}} Unit** | **{{pct_nib}}%** |
| **Kepemilikan NPWP** | **{{total_npwp}} Unit** | **{{pct_npwp}}%** |
| **Penyelenggaraan RAT (2025)** | **{{total_rat}} Unit** | **{{pct_rat}}%** |
| **Total Simpanan Pokok** | **Rp {{simpanan_pokok}}** | Akumulasi Nasional |
| **Total Simpanan Wajib** | **Rp {{simpanan_wajib}}** | Akumulasi Nasional |
| **Total Nilai Transaksi** | **Rp {{total_nilai_transaksi}}** | Akumulasi Nasional |

---

## 2. Analisis Matriks Korelasi Antar-Variabel

Korelasi Pearson dihitung untuk mengamati hubungan linier antar-indikator kelembagaan, transaksi, dan permodalan koperasi:

<img src="figures/eda_correlation_matrix.png" alt="Matriks Korelasi Pearson" width="550">

### Interpretasi Korelasi:
- **Korelasi Simpanan & Transaksi**: Hubungan antara `simpanan_wajib` dan `nilai_transaksi` menunjukkan tingkat keterikatan modal kerja terhadap perputaran usaha koperasi daerah.
- **Korelasi Kelembagaan (NIB/NPWP/RAT)**: Kepatuhan perizinan dasar (NIB) berkorelasi positif kuat dengan jumlah unit koperasi aktif, namun kepatuhan RAT memerlukan pembinaan lebih lanjut.

---

## 3. Disparitas dan Pola Sebaran Spasial Wilayah

### A. 10 Provinsi dengan Jumlah Koperasi Terbanyak
<img src="figures/eda_top_provinces.png" alt="Top 10 Provinsi" width="550">

{{top_provinces_list}}

### B. 10 Kabupaten/Kota dengan Nilai Transaksi Tertinggi
<img src="figures/eda_top_regencies_transaksi.png" alt="Top 10 Kabupaten Transaksi" width="550">

{{top_regencies_transaksi_list}}

---

## 4. Distribusi Frekuensi dan Kemiringan Data

<img src="figures/eda_feature_distributions.png" alt="Distribusi Fitur Numerik" width="550">

Distribusi data pada variabel moneter menunjukkan kemiringan positif (*right-skewed / positive skew*), memperkuat perlunya perlakuan *log transformation* pada *Data Preparation*.
