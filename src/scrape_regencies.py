import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from utils.scraper_utils import (
    scrape_table_with_pagination,
    save_to_csv,
    load_scraped_province_ids
)
from utils.log_utils import get_logger
from config import (
    RAW_REGENCIES_CSV,
    RAW_PROVINCES_CSV,
    SCRAPE_TABLE_INDEX,
    SCRAPE_MAX_WORKERS,
    SCRAPE_BASE_URL_TEMPLATE
)

logger = get_logger("scrape_regencies")

def scrape_single_province(prov_id):
    target_url = SCRAPE_BASE_URL_TEMPLATE.format(id=prov_id)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            headers, rows = scrape_table_with_pagination(page, target_url, SCRAPE_TABLE_INDEX)
            browser.close()
            return prov_id, headers, rows
        except Exception as e:
            browser.close()
            raise e

def main():
    prov_ids = load_scraped_province_ids()
    if not prov_ids:
        logger.warning("Tidak ada province ID yang terdeteksi untuk di-scrape.")
        save_to_csv(RAW_REGENCIES_CSV, [], [])
        return

    logger.info(f"Memulai Scraping Data Kabupaten/Kota untuk ID: {prov_ids} Parallel ({SCRAPE_MAX_WORKERS} Workers)...")
    logger.info(f"Output CSV : {RAW_REGENCIES_CSV}")
    start_time = time.time()

    global_headers = []
    prov_results = {}

    with ThreadPoolExecutor(max_workers=SCRAPE_MAX_WORKERS) as executor:
        futures = {
            executor.submit(scrape_single_province, prov_id): prov_id
            for prov_id in prov_ids
        }

        for future in as_completed(futures):
            prov_id = futures[future]
            try:
                p_id, headers, rows = future.result()
                if not global_headers and headers:
                    global_headers = ['Province_ID'] + headers
                prov_results[p_id] = rows
                logger.info(f"[{p_id}] Selesai -> ({len(rows)} baris).")
            except Exception as e:
                logger.error(f"[{prov_id}] Error: {str(e)}")

    combined_rows = []
    seen_combined = set()
    for prov_id in prov_ids:
        rows = prov_results.get(prov_id, [])
        for r in rows:
            row_with_id = [prov_id] + r
            t = tuple(row_with_id)
            if t not in seen_combined:
                seen_combined.add(t)
                combined_rows.append(row_with_id)

    save_to_csv(RAW_REGENCIES_CSV, global_headers, combined_rows)

    elapsed = time.time() - start_time
    logger.info(f"Parallel Scraping selesai! Total {len(combined_rows)} baris kabupaten/kota dalam {elapsed:.2f} detik.")
    logger.info(f"File CSV akhir -> {RAW_REGENCIES_CSV}")

if __name__ == "__main__":
    main()
