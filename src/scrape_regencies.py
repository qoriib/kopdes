import os
import time
import csv
import dvc.api
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from utils.scraper_utils import scrape_table_with_pagination, save_to_csv
from utils.log_utils import get_logger
from config import RAW_REGENCIES_CSV, RAW_PROVINCES_CSV

logger = get_logger("scrape_regencies")
params = dvc.api.params_show().get('scrape', {})

MAX_WORKERS = params.get('max_workers', 4)
TABLE_INDEX = params.get('table_index', 2)
BASE_URL_TEMPLATE = params.get('base_url_template', "https://simkopdes.go.id/pers/dashboard/district/{id}")

def load_scraped_province_ids():
    prov_ids = []
    from config import GEO_PROVINCES_JSON
    import json
    
    geo_id_map = {}
    if os.path.exists(GEO_PROVINCES_JSON):
        try:
            with open(GEO_PROVINCES_JSON, encoding='utf-8') as f:
                prov_data = json.load(f)
                geo_id_map = {p['name'].strip().upper(): int(p['province_id']) for p in prov_data if 'name' in p}
        except Exception as e:
            logger.error(f"Gagal memuat province.json untuk resolusi ID: {e}")

    if os.path.exists(RAW_PROVINCES_CSV):
        try:
            with open(RAW_PROVINCES_CSV, encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                for row in reader:
                    if not row or len(row) < 2:
                        continue
                    name = row[1].strip().upper()
                    if name.lower() == "no data":
                        continue
                    geo_id = geo_id_map.get(name)
                    if geo_id is not None:
                        prov_ids.append(geo_id)
                    else:
                        logger.warning(f"Province name '{name}' dari scraped_provinces.csv tidak ditemukan di province.json!")
        except Exception as e:
            logger.error(f"Gagal membaca province IDs dari {RAW_PROVINCES_CSV}: {e}")
    return prov_ids

def scrape_single_province(prov_id):
    target_url = BASE_URL_TEMPLATE.format(id=prov_id)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            headers, rows = scrape_table_with_pagination(page, target_url, TABLE_INDEX)
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

    logger.info(f"Memulai Scraping Data Kabupaten/Kota untuk ID: {prov_ids} Parallel ({MAX_WORKERS} Workers)...")
    logger.info(f"Output CSV : {RAW_REGENCIES_CSV}")
    start_time = time.time()

    global_headers = []
    prov_results = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
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
