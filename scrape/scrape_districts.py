import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scraper_utils import scrape_table_with_pagination, save_to_csv

START_PROVINCE_ID = 1
END_PROVINCE_ID = 38
TABLE_INDEX = 2
BASE_URL_TEMPLATE = "https://simkopdes.go.id/pers/dashboard/district/{id}"
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "scraped_districts.csv")

def main():
    print("[+] Memulai Scraping Data Kota/Kabupaten ID 1-38 via Playwright...")
    print(f"[*] Output CSV : {OUTPUT_CSV}")
    start_time = time.time()

    global_headers = []
    combined_rows = []
    seen_combined = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        for prov_id in range(START_PROVINCE_ID, END_PROVINCE_ID + 1):
            target_url = BASE_URL_TEMPLATE.format(id=prov_id)
            print(f"[*] [{prov_id}/{END_PROVINCE_ID}] Navigasi -> {target_url}...", end=" ", flush=True)

            try:
                headers, rows = scrape_table_with_pagination(page, target_url, TABLE_INDEX)

                if not global_headers and headers:
                    global_headers = ['Province_ID'] + headers

                prov_count = 0
                for r in rows:
                    row_with_id = [prov_id] + r
                    t = tuple(row_with_id)
                    if t not in seen_combined:
                        seen_combined.add(t)
                        combined_rows.append(row_with_id)
                        prov_count += 1

                print(f"[OK] ({prov_count} baris baru).")

                # Perbarui CSV secara instan per provinsi selesai di folder data/raw/
                save_to_csv(OUTPUT_CSV, global_headers, combined_rows)

            except Exception as e:
                print(f"[ERROR] {str(e)}")

        browser.close()

    elapsed = time.time() - start_time
    print(f"\n[DONE] Scraping selesai! Total {len(combined_rows)} baris kota/kabupaten dalam {elapsed:.2f} detik.")
    print(f"[SAVED] File CSV akhir -> {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
