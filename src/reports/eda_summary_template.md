# Exploratory Data Analysis

Laporan ini dihasilkan secara otomatis oleh pipeline analisis data SIMKOPDES berbasis Data Version Control (DVC).

## Ringkasan Statistik Nasional

| Indikator Kinerja | Jumlah | Persentase |
| :--- | :--- | :--- |
| Jumlah Provinsi | {{total_provinces}} | 100% |
| Jumlah Kabupaten/Kota | {{total_regencies}} | 100% |
| Total Koperasi Terdaftar | {{total_koperasi}} | 100% |
| Koperasi Memiliki NIB | {{total_nib}} | {{pct_nib}}% |
| Koperasi Memiliki NPWP | {{total_npwp}} | {{pct_npwp}}% |
| Koperasi Telah Melaksanakan RAT (2025) | {{total_rat}} | {{pct_rat}}% |
| Total Simpanan Pokok | Rp {{simpanan_pokok}} | - |
| Total Simpanan Wajib | Rp {{simpanan_wajib}} | - |
| Total Nilai Transaksi | Rp {{total_nilai_transaksi}} | - |

## Visualisasi Analisis Eksplorasi Data

### 1. Distribusi Koperasi di Tingkat Provinsi
<img src="figures/eda_top_provinces.png" alt="10 Provinsi dengan Koperasi Terbanyak" width="300">

### 2. Nilai Transaksi di Tingkat Kabupaten/Kota
<img src="figures/eda_top_regencies_transaksi.png" alt="10 Kabupaten/Kota dengan Nilai Transaksi Tertinggi" width="300">

## Statistik Deskriptif Tingkat Provinsi
Laporan statistik deskriptif berikut dihitung untuk seluruh indikator di tingkat Provinsi:

{{desc_prov_markdown}}

## Statistik Deskriptif Tingkat Kabupaten/Kota
Laporan statistik deskriptif berikut dihitung untuk seluruh indikator di tingkat Kabupaten/Kota:

{{desc_reg_markdown}}

## Provinsi Teratas dengan Jumlah Koperasi Terbanyak
{{top_provinces_list}}

## Kabupaten/Kota Teratas dengan Jumlah Koperasi Terbanyak
{{top_regencies_koperasi_list}}

## Kabupaten/Kota Teratas dengan Nilai Transaksi Tertinggi
{{top_regencies_transaksi_list}}
