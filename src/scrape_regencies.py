import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (
    RAW_PROVINCES_CSV,
    RAW_REGENCIES_CSV
)
from scrape_util import (
    SCRAPE_MAX_WORKERS,
    load_scraped_province_ids,
    scrape_single_regency
)

print("=== Scraping Data Tingkat Kabupaten/Kota ===")

# Ambil daftar ID / nomor urut provinsi dari file CSV hasil scraping provinsi
province_ids = load_scraped_province_ids(RAW_PROVINCES_CSV)

# Validasi ketersediaan data ID provinsi
if not province_ids:
    print("Tidak ada ID provinsi yang ditemukan. Pastikan data provinsi telah discrape terlebih dahulu.")
else:
    print(f"Memulai scraping {len(province_ids)} kabupaten/kota dengan {SCRAPE_MAX_WORKERS} worker threads...")

    all_regencies_rows = []
    final_table_headers = []

    # Jalankan proses scraping secara paralel menggunakan ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=SCRAPE_MAX_WORKERS) as executor:
        
        # Daftarkan setiap task scraping ke executor secara eksplisit
        active_futures = {}
        for province_id in province_ids:
            future_task = executor.submit(scrape_single_regency, province_id)
            active_futures[future_task] = province_id

        # Kumpulkan hasil scraping dari task yang selesai
        for future_task in as_completed(active_futures):
            province_id = active_futures[future_task]
            try:
                table_headers, table_rows = future_task.result()

                # Tetapkan header tabel jika belum diatur
                if table_headers and not final_table_headers:
                    final_table_headers = ["province_id"] + table_headers

                all_regencies_rows.extend(table_rows)
                print(f"Provinsi ID {province_id}: Berhasil mengekstrak {len(table_rows)} baris kabupaten/kota.")

            except Exception as error_message:
                print(f"Provinsi ID {province_id} gagal diekstrak: {error_message}")

    # Simpan hasil akhir ke file CSV
    if final_table_headers and all_regencies_rows:
        regencies_dataframe = pd.DataFrame(all_regencies_rows, columns=final_table_headers)
        regencies_dataframe.to_csv(RAW_REGENCIES_CSV, index=False)
        print(f"Ekstraksi data kabupaten/kota selesai ({len(regencies_dataframe)} entri).")
    else:
        print("Tidak ada data kabupaten/kota yang berhasil diekstrak.")
