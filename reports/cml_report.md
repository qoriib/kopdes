# Laporan Pemrosesan Data & Machine Learning SIMKOPDES

# Laporan Analisis Eksplorasi Data SIMKOPDES

Laporan ini dihasilkan secara otomatis oleh pipeline analisis data SIMKOPDES berbasis Data Version Control (DVC).

---

## Ringkasan Statistik Nasional

| Indikator Kinerja | Jumlah | Persentase |
| :--- | :--- | :--- |
| Jumlah Provinsi | 38 | 100% |
| Jumlah Kabupaten/Kota | 514 | 100% |
| Total Koperasi Terdaftar | 83,382 | 100% |
| Koperasi Memiliki NIB | 60,809 | 72.93% |
| Koperasi Memiliki NPWP | 80,978 | 97.12% |
| Koperasi Telah Melaksanakan RAT (2025) | 50,182 | 60.18% |
| Total Simpanan Pokok | Rp 29,469,736,015 | - |
| Total Simpanan Wajib | Rp 10,670,405,950 | - |
| Total Nilai Transaksi | Rp 179,612,834,516 | - |

---

## Lima Provinsi dengan Jumlah Koperasi Terbanyak

1. JAWA TENGAH: 8,524 Koperasi (NIB: 8,153, RAT: 6,831)
2. JAWA TIMUR: 8,494 Koperasi (NIB: 7,882, RAT: 6,366)
3. ACEH: 6,534 Koperasi (NIB: 4,451, RAT: 4,474)
4. SUMATERA UTARA: 6,102 Koperasi (NIB: 4,818, RAT: 2,730)
5. JAWA BARAT: 5,970 Koperasi (NIB: 5,264, RAT: 3,495)

---

## Lima Kabupaten/Kota dengan Jumlah Koperasi Terbanyak

1. KAB. ACEH UTARA: 852 Koperasi
2. KAB. PIDIE: 751 Koperasi
3. KAB. BIREUEN: 610 Koperasi
4. KAB. ACEH BESAR: 603 Koperasi
5. KAB. TOLIKARA: 545 Koperasi

---

## Lima Kabupaten/Kota dengan Nilai Transaksi Tertinggi

1. KAB. NGANJUK: Rp 15,194,190,260
2. KAB. TUBAN: Rp 10,973,201,496
3. KOTA KUPANG: Rp 6,617,144,400
4. KOTA PALEMBANG: Rp 6,044,820,800
5. KOTA PROBOLINGGO: Rp 5,324,153,500

# Laporan Evaluasi Pengelompokan (Clustering) KMeans SIMKOPDES

Laporan ini menyajikan hasil evaluasi kuantitatif dan analisis profil klaster kabupaten/kota berbasis algoritma KMeans.

---

## 1. Evaluasi Kinerja Pengelompokan

| Metrik Evaluasi | Nilai Kinerja | Keterangan |
| :--- | :--- | :--- |
| **Silhouette Score** | **0.2211** | Mengukur seberapa serupa objek dengan klasternya sendiri dibandingkan klaster lain (Range: -1 s.d. +1, semakin tinggi semakin baik) |
| **Calinski-Harabasz Index** | **136.38** | Rasio dispersi antar-klaster terhadap dalam-klaster (semakin tinggi semakin baik) |
| **Davies-Bouldin Index** | **1.1603** | Mengukur rata-rata kesamaan tiap klaster dengan klaster paling serupa (semakin rendah semakin baik) |
| **Jumlah Klaster Terbentuk** | **6** | Hasil optimasi dari KElbowVisualizer |

---

## 2. Profil Rata-Rata per Klaster

| Klaster | Rata-rata Jumlah Koperasi | Rata-rata Koperasi NIB | Rata-rata Koperasi NPWP | Rata-rata Koperasi RAT | Rata-rata Nilai Transaksi (Rp) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **Klaster 0** | 112.93 | 81.73 | 112.67 | 64.64 | Rp 157,032,262.77 |
| **Klaster 1** | 252.36 | 205.59 | 250.58 | 165.38 | Rp 535,384,663.69 |
| **Klaster 2** | 314.5 | 226.5 | 314.5 | 195.0 | Rp 100,131,850.0 |
| **Klaster 3** | 107.79 | 59.89 | 98.3 | 53.23 | Rp 160,038,866.82 |
| **Klaster 4** | 292.0 | 262.33 | 292.0 | 181.33 | Rp 9,656,287,118.67 |
| **Klaster 5** | 423.97 | 365.28 | 423.69 | 304.19 | Rp 1,015,428,109.12 |

---

## 3. Distribusi Anggota Klaster

- **Klaster 0**: 137 Kabupaten/Kota
- **Klaster 1**: 112 Kabupaten/Kota
- **Klaster 2**: 2 Kabupaten/Kota
- **Klaster 3**: 228 Kabupaten/Kota
- **Klaster 4**: 3 Kabupaten/Kota
- **Klaster 5**: 32 Kabupaten/Kota

