import os
import sys
import time
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.scraper_utils import scrape_table_with_pagination, save_to_csv

PARAMS_FILE = os.path.join(os.path.dirname(__file__), "..", "params.yaml")
params = {}
if os.path.exists(PARAMS_FILE):
    try:
        with open(PARAMS_FILE, encoding='utf-8') as f:
            params = yaml.safe_load(f).get('scrape', {})
    except Exception:
        pass

MAX_WORKERS = params.get('max_workers', 4)
START_PROVINCE_ID = params.get('start_province_id', 1)
END_PROVINCE_ID = params.get('end_province_id', 38)
TABLE_INDEX = 2
BASE_URL_TEMPLATE = "https://simkopdes.go.id/pers/dashboard/district/{id}"
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "scraped_regencies.csv")

def scrape_single_province(prov_id):
    target_url = BASE_URL_TEMPLATE.format(id=prov_id)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        try:
            headers, rows = scrape_table_with_pagination(page, target_url, TABLE_INDEX)
            browser.close()
            return prov_id, headers, rows
        except Exception as e:
            browser.close()
            raise e

def main():
    print(f"[+] Memulai Scraping Data Kabupaten/Kota ID {START_PROVINCE_ID}-{END_PROVINCE_ID} Parallel ({MAX_WORKERS} Workers)...")
    print(f"[*] Output CSV : {OUTPUT_CSV}")
    start_time = time.time()

    global_headers = []
    prov_results = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(scrape_single_province, prov_id): prov_id
            for prov_id in range(START_PROVINCE_ID, END_PROVINCE_ID + 1)
        }

        for future in as_completed(futures):
            prov_id = futures[future]
            try:
                p_id, headers, rows = future.result()
                if not global_headers and headers:
                    global_headers = ['Province_ID'] + headers
                prov_results[p_id] = rows
                print(f"[*] [{p_id}/{END_PROVINCE_ID}] Selesai -> ({len(rows)} baris).")
            except Exception as e:
                print(f"[*] [{prov_id}/{END_PROVINCE_ID}] Error: {str(e)}")

    combined_rows = []
    seen_combined = set()
    for prov_id in range(START_PROVINCE_ID, END_PROVINCE_ID + 1):
        rows = prov_results.get(prov_id, [])
        for r in rows:
            row_with_id = [prov_id] + r
            t = tuple(row_with_id)
            if t not in seen_combined:
                seen_combined.add(t)
                combined_rows.append(row_with_id)

    save_to_csv(OUTPUT_CSV, global_headers, combined_rows)

    elapsed = time.time() - start_time
    print(f"\n[DONE] Parallel Scraping selesai! Total {len(combined_rows)} baris kabupaten/kota dalam {elapsed:.2f} detik.")
    print(f"[SAVED] File CSV akhir -> {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
