# Laporan Deskripsi Data (*Data Description Report*)

Dokumen ini merupakan laporan luaran dari tugas generik **Describe Data** pada kerangka kerja **CRISP-DM 1.0 (Chapman et al., 2000)** untuk mendeskripsikan karakteristik permukaan (*gross properties*), tipe data, skala pengukuran, dan ringkasan statistik deskriptif awal data KDMP SIMKOPDES 2026.

---

## 1. Properti Permukaan Data (*Gross Properties*)

- **Jumlah Baris (Unit Observasi)**: **{{total_rows}}** Kabupaten/Kota
- **Jumlah Kolom (Atribut)**: **{{total_cols}}** Atribut
- **Format Penyimpanan**: Tabular CSV (`data/raw/scraped_regencies.csv`)

---

## 2. Kamus Data dan Skala Pengukuran (Tabel 3.1 Spesifikasi Penelitian)

| No | Nama Fitur | Tipe Data | Skala Pengukuran | Deskripsi Operasional |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `total_koperasi` | Integer | Rasio (Unit) | Jumlah unit KDMP terdaftar aktif di kabupaten/kota |
| 2 | `koperasi_nib` | Integer | Rasio (Unit) | Jumlah koperasi yang memiliki Nomor Induk Berusaha (NIB) |
| 3 | `koperasi_npwp` | Integer | Rasio (Unit) | Jumlah koperasi yang memiliki NPWP valid |
| 4 | `koperasi_rat` | Integer | Rasio (Unit) | Jumlah koperasi penyelenggara RAT tahun buku 2025 |
| 5 | `simpanan_pokok` | Numerik | Rupiah (IDR) | Total akumulasi simpanan pokok anggota |
| 6 | `simpanan_wajib` | Numerik | Rupiah (IDR) | Total akumulasi simpanan wajib anggota |
| 7 | `volume_transaksi` | Integer | Rasio (Frekuensi) | Total frekuensi transaksi operasional usaha |
| 8 | `nilai_transaksi` | Numerik | Rupiah (IDR) | Akumulasi perputaran nilai bruto transaksi |

---

## 3. Statistik Deskriptif Dasar Variabel Penelitian

Tabel berikut menyajikan statistik deskriptif dasar (*count, mean, median, standard deviation, minimum, maximum*) dari seluruh variabel observasi kabupaten/kota:

{{descriptive_stats_table}}

---

## 4. Evaluasi Awal Sebaran Data

- **Rentang Variasi Finansial**: Atribut `nilai_transaksi`, `simpanan_pokok`, dan `simpanan_wajib` memiliki rentang nilai nominal yang sangat lebar dan perbedaan magnitudo yang signifikan antar-wilayah.
- **Tindak Lanjut**: Data membutuhkan transformasi logaritmik dan standarisasi Z-score pada tahap Data Preparation agar terdistribusi normal standar sebelum pemodelan K-Means.
