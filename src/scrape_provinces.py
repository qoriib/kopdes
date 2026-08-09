import time
from playwright.sync_api import sync_playwright
from utils.scraper_utils import scrape_table_with_pagination, save_to_csv
from utils.log_utils import get_logger
from config import RAW_PROVINCES_CSV, SCRAPE_TARGET_URL, SCRAPE_TABLE_INDEX

logger = get_logger("scrape_provinces")

TARGET_URL = SCRAPE_TARGET_URL
TABLE_INDEX = SCRAPE_TABLE_INDEX

def main():
    logger.info("Memulai Scraping Data Provinsi via Playwright...")
    logger.info(f"Target URL : {TARGET_URL}")
    logger.info(f"Tabel Ke   : {TABLE_INDEX}")
    logger.info(f"Output CSV : {RAW_PROVINCES_CSV}")

    start_time = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        headers, clean_rows = scrape_table_with_pagination(page, TARGET_URL, TABLE_INDEX)
        browser.close()

    elapsed = time.time() - start_time
    logger.info(f"Berhasil mengekstrak {len(clean_rows)} baris provinsi dalam {elapsed:.2f} detik.")

    save_to_csv(RAW_PROVINCES_CSV, headers, clean_rows)
    logger.info("Scraping provinsi selesai.")

if __name__ == "__main__":
    main()
