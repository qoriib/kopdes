from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from config import (
    RAW_PROVINCES_CSV,
    RAW_REGENCIES_CSV,
    GEO_PROVINCES_JSON
)
from scrape_util import (
    SCRAPE_BASE_URL_TEMPLATE,
    SCRAPE_TABLE_INDEX,
    SCRAPE_MAX_WORKERS,
    load_scraped_province_ids,
    scrape_single_regency
)

print("=== Scraping Data Tingkat Kabupaten/Kota ===")
prov_ids = load_scraped_province_ids(GEO_PROVINCES_JSON, RAW_PROVINCES_CSV)

if not prov_ids:
    print("Tidak ada ID provinsi yang ditemukan. Pastikan data provinsi telah discrape terlebih dahulu.")
else:
    print(f"Memulai scraping {len(prov_ids)} kabupaten/kota dengan {SCRAPE_MAX_WORKERS} worker threads...")
    all_rows = []
    final_headers = []

    with ThreadPoolExecutor(max_workers=SCRAPE_MAX_WORKERS) as executor:
        futures = {
            executor.submit(scrape_single_regency, pid, SCRAPE_BASE_URL_TEMPLATE, SCRAPE_TABLE_INDEX): pid
            for pid in prov_ids
        }
        for future in as_completed(futures):
            pid = futures[future]
            try:
                h, r = future.result()
                if h and not final_headers:
                    # Prepend province_id to raw table headers
                    final_headers = ['province_id'] + h
                all_rows.extend(r)
                print(f"Provinsi ID {pid}: Berhasil mengekstrak {len(r)} baris kabupaten/kota.")
            except Exception as e:
                print(f"Provinsi ID {pid} gagal diekstrak: {e}")

    if final_headers and all_rows:
        df_reg = pd.DataFrame(all_rows, columns=final_headers)
        df_reg.to_csv(RAW_REGENCIES_CSV, index=False)
        print(f"Ekstraksi data kabupaten/kota selesai ({len(df_reg)} entri).")
    else:
        print("Tidak ada data kabupaten/kota yang berhasil diekstrak.")
