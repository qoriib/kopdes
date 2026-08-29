# Laporan Pengumpulan Data Awal (*Initial Data Collection Report*)

Dokumen ini merupakan laporan luaran dari tugas generik **Collect Initial Data** pada kerangka kerja **CRISP-DM 1.0 (Chapman et al., 2000)** dalam penelitian klasterisasi kinerja Koperasi Desa Merah Putih (KDMP) berbasis data SIMKOPDES.

---

## 1. Identifikasi Sumber dan Aksesibilitas Data

- **Sumber Data**: Portal Resmi Sistem Informasi Koperasi Desa (SIMKOPDES)
- **Tahun Data**: 2026
- **Karakter Data**: Data Sekunder Terbuka (*Open Secondary Data*)
- **URL Target**: `https://simkopdes.go.id/pers/dashboard`
- **Tingkat Agregasi Unit Observasi**: Tingkat Kabupaten/Kota di 38 Provinsi seluruh Indonesia
- **Mekanisme Penarikan**: Ekstraksi otomatis berbasis *web scraping* mandiri (`src/scraper/`) dengan Playwright/HTTP scraping.
- **Pelacakan Versi (*Data Versioning*)**: Git dan Data Version Control (DVC) dengan penyimpanan awan Cloudflare R2 Remote Storage.

---

## 2. Cakupan dan Volume Data yang Dikumpulkan

| Parameter Dataset | Keterangan / Nilai |
| :--- | :--- |
| **Total Observasi Kabupaten/Kota** | **{{total_regencies}} Kabupaten/Kota** |
| **Total Observasi Provinsi** | **{{total_provinces}} Provinsi** |
| **Jumlah Variabel/Atribut Mentah** | **{{total_columns}} Atribut** |
| **Status Kelengkapan Wilayah** | 100% Teragregasi Nasional (38 Provinsi) |
| **Lokasi File Mentah Lokal** | `data/raw/scraped_regencies.csv` & `data/raw/scraped_provinces.csv` |

---

## 3. Struktur Berkas Data Mentah Awal

### A. Dataset Kabupaten/Kota (`scraped_regencies.csv`)
{{regencies_schema_table}}

### B. Dataset Provinsi (`scraped_provinces.csv`)
{{provinces_schema_table}}

---

## 4. Kesimpulan Pengumpulan Data Awal

Pengumpulan data sekunder awal telah berhasil mencakup seluruh 514 kabupaten/kota dan 38 provinsi di Indonesia tanpa *loss* wilayah. Seluruh data mentah telah tersimpan dan terlacak dalam repositori DVC, siap untuk dilakukan tahapan **Describe Data** dan **Verify Data Quality**.
