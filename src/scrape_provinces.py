import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.scraper_utils import scrape_table_with_pagination, save_to_csv

TARGET_URL = "https://simkopdes.go.id/pers/dashboard"
TABLE_INDEX = 2
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "scraped_provinces.csv")

def main():
    print("[+] Memulai Scraping Data Provinsi via Playwright...")
    print(f"[*] Target URL : {TARGET_URL}")
    print(f"[*] Tabel Ke   : {TABLE_INDEX}")
    print(f"[*] Output CSV : {OUTPUT_CSV}")

    start_time = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        headers, clean_rows = scrape_table_with_pagination(page, TARGET_URL, TABLE_INDEX)
        browser.close()

    elapsed = time.time() - start_time
    print(f"[OK] Berhasil mengekstrak {len(clean_rows)} baris provinsi dalam {elapsed:.2f} detik.")

    save_to_csv(OUTPUT_CSV, headers, clean_rows)
    print("[DONE] Scraping provinsi selesai.")

if __name__ == "__main__":
    main()
