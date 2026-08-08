import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import RAW_PROVINCES_CSV, get_params
from utils.scraper_utils import scrape_table_with_pagination, save_to_csv
from utils.log_utils import get_logger

logger = get_logger("scrape_provinces")
params = get_params('scrape')

TARGET_URL = params.get('target_url', "https://simkopdes.go.id/pers/dashboard")
TABLE_INDEX = params.get('table_index', 2)

def main():
    logger.info("Memulai Scraping Data Provinsi via Playwright...")
    logger.info(f"Target URL : {TARGET_URL}")
    logger.info(f"Tabel Ke   : {TABLE_INDEX}")
    logger.info(f"Output CSV : {RAW_PROVINCES_CSV}")

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
    logger.info(f"Berhasil mengekstrak {len(clean_rows)} baris provinsi dalam {elapsed:.2f} detik.")

    save_to_csv(RAW_PROVINCES_CSV, headers, clean_rows)
    logger.info("Scraping provinsi selesai.")

if __name__ == "__main__":
    main()
