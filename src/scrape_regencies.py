import pandas as pd
from playwright.sync_api import sync_playwright
from config import RAW_PROVINCES_CSV, RAW_REGENCIES_CSV
from scrape_util import (
    SCRAPE_BASE_URL_TEMPLATE,
    SCRAPE_TABLE_INDEX,
    load_scraped_province_ids,
    scrape_table_with_pagination,
)

print("=== Scraping Data Tingkat Kabupaten/Kota ===")

# Ambil daftar ID provinsi dari file CSV hasil scraping provinsi
province_ids = load_scraped_province_ids(RAW_PROVINCES_CSV)

if not province_ids:
    print("Tidak ada ID provinsi yang ditemukan. Pastikan data provinsi telah discrape terlebih dahulu.")
else:
    print(f"Memulai scraping {len(province_ids)} provinsi secara berurutan...")

    all_regencies_rows = []
    final_table_headers = []

    with sync_playwright() as playwright_instance:
        browser = playwright_instance.chromium.launch(headless=True)
        page = browser.new_page()

        for province_id in province_ids:
            target_district_url = SCRAPE_BASE_URL_TEMPLATE.format(id=province_id)
            table_headers, table_rows = scrape_table_with_pagination(
                page,
                target_district_url,
                target_table_index=SCRAPE_TABLE_INDEX
            )

            if table_headers and not final_table_headers:
                final_table_headers = ["province_id"] + table_headers

            for row_data in table_rows:
                row_with_id = [province_id] + row_data
                all_regencies_rows.append(row_with_id)

            print(f"Provinsi ID {province_id}: Berhasil mengekstrak {len(table_rows)} baris kabupaten/kota.")

        browser.close()

    # Simpan hasil akhir ke file CSV
    if final_table_headers and all_regencies_rows:
        regencies_dataframe = pd.DataFrame(all_regencies_rows, columns=final_table_headers)
        regencies_dataframe.to_csv(RAW_REGENCIES_CSV, index=False)
        print(f"Ekstraksi data kabupaten/kota selesai ({len(regencies_dataframe)} entri).")
    else:
        print("Tidak ada data kabupaten/kota yang berhasil diekstrak.")
