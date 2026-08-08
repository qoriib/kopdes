import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import RAW_PROVINCES_CSV, get_params
from utils.scraper_utils import scrape_table_with_pagination, save_to_csv

params = get_params('scrape')

TARGET_URL = params.get('target_url', "https://simkopdes.go.id/pers/dashboard")
TABLE_INDEX = params.get('table_index', 2)
OUTPUT_CSV = RAW_PROVINCES_CSV

def main():
    print("[+] Memulai Scraping Data Provinsi via Playwright...")
    print(f"[*] Target URL : {TARGET_URL}")
    print(f"[*] Tabel Ke   : {TABLE_INDEX}")
    print(f"[*] Output CSV : {OUTPUT_CSV}")

    start_time = time.time()

    playwright_config = params.get('playwright', {})
    headless = playwright_config.get('headless', True)
    width = playwright_config.get('width', 1280)
    height = playwright_config.get('height', 800)
    user_agent = playwright_config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(
            viewport={'width': width, 'height': height},
            user_agent=user_agent
        )

        headers, clean_rows = scrape_table_with_pagination(page, TARGET_URL, TABLE_INDEX)
        browser.close()

    elapsed = time.time() - start_time
    print(f"[OK] Berhasil mengekstrak {len(clean_rows)} baris provinsi dalam {elapsed:.2f} detik.")

    save_to_csv(OUTPUT_CSV, headers, clean_rows)
    print("[DONE] Scraping provinsi selesai.")

if __name__ == "__main__":
    main()
