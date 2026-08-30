import pandas as pd
from playwright.sync_api import sync_playwright
from config import RAW_PROVINCES_CSV
from scrape_util import (
    SCRAPE_TARGET_URL,
    SCRAPE_TABLE_INDEX,
    scrape_table_with_pagination,
    save_raw_dataframe
)

print("=== Scraping Data Tingkat Provinsi ===")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    headers, rows = scrape_table_with_pagination(page, SCRAPE_TARGET_URL, target_table_index=SCRAPE_TABLE_INDEX)
    browser.close()

if headers and rows:
    df_prov = pd.DataFrame(rows, columns=headers)
    save_raw_dataframe(df_prov, RAW_PROVINCES_CSV)
    print(f"Ekstraksi data provinsi selesai ({len(df_prov)} entri).")
else:
    print("Tidak ada data provinsi yang berhasil diekstrak.")
