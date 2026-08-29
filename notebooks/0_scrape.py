import os
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from config import (
    RAW_PROVINCES_CSV,
    RAW_REGENCIES_CSV,
    GEO_PROVINCES_JSON,
    NUMERIC_COLUMNS
)

# Scraping Parameters
SCRAPE_TABLE_INDEX = 2
SCRAPE_MAX_WORKERS = 5
SCRAPE_TARGET_URL = "https://simkopdes.go.id/pers/dashboard"
SCRAPE_BASE_URL_TEMPLATE = "https://simkopdes.go.id/pers/dashboard/district/{id}"

PROVINCE_COLUMN_MAPPING = {
    'No': 'no',
    'Provinsi': 'province_name',
    'Jumlah Koperasi': 'total_koperasi',
    'Koperasi Memiliki NIB': 'koperasi_nib',
    'Koperasi Memiliki NPWP': 'koperasi_npwp',
    'Koperasi Telah RAT (2025)': 'koperasi_rat',
    'Simpanan Pokok': 'simpanan_pokok',
    'Simpanan Wajib': 'simpanan_wajib',
    'Volume Transaksi (2026)': 'volume_transaksi',
    'Nilai Transaksi (2026)': 'nilai_transaksi',
    'Pemetahaan Lahan': 'pemetahaan_lahan',
    'Pemetahaan Lahan (%)': 'pemetahaan_lahan_pct',
    'Pembangunan Gerai (%)': 'pembangunan_gerai_pct'
}

REGENCY_COLUMN_MAPPING = {
    'Province_ID': 'province_id',
    'No': 'regency_no',
    'Kabupaten/Kota': 'regency_name',
    'Jumlah Koperasi': 'total_koperasi',
    'Koperasi Memiliki NIB': 'koperasi_nib',
    'Koperasi Memiliki NPWP': 'koperasi_npwp',
    'Koperasi Telah RAT (2025)': 'koperasi_rat',
    'Simpanan Pokok': 'simpanan_pokok',
    'Simpanan Wajib': 'simpanan_wajib',
    'Volume Transaksi (2026)': 'volume_transaksi',
    'Nilai Transaksi (2026)': 'nilai_transaksi'
}

def clean_number_col(series: pd.Series) -> pd.Series:
    def _clean_val(val):
        if pd.isna(val) or val is None:
            return 0
        s = str(val).strip()
        if not s or s.lower() in ("no data", "-", "nan", "null"):
            return 0
        s = s.replace(".", "").replace(",", ".").replace(" ", "")
        try:
            return float(s)
        except ValueError:
            return 0
    return series.apply(_clean_val)

def is_header_row(row: list) -> bool:
    if not row:
        return True
    c0 = str(row[0]).strip().lower()
    c1 = str(row[1]).strip().lower() if len(row) > 1 else ""
    return c0 == 'no' or c1 in ('provinsi', 'kabupaten/kota', 'kabupaten', 'kota') or 'provinsi' in c0

def map_column_headers(headers: list, mapping: dict) -> list:
    return [mapping.get(h.strip(), mapping.get(h, h.strip().lower().replace(" ", "_"))) for h in headers]

def parse_table_from_html(html: str, target_index: int = 2) -> tuple[list, list]:
    try:
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        if not tables:
            print("Peringatan: Tidak ada tabel (<table/>) yang ditemukan dalam HTML.")
            return [], []

        selected_idx = min(max(1, target_index), len(tables)) - 1
        table = tables[selected_idx]

        headers = []
        thead = table.find('thead')
        if thead:
            for th in thead.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))

        rows = []
        tbody = table.find('tbody') or table
        for tr in tbody.find_all('tr'):
            cols = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if cols and not is_header_row(cols):
                rows.append(cols)

        if not headers and rows:
            headers = rows[0]
            rows = rows[1:]

        return headers, rows
    except Exception as e:
        print(f"Gagal memparsing HTML tabel: {e}")
        return [], []

def change_page_size(page: Page) -> None:
    try:
        size_changer = page.query_selector('.ant-pagination-options-size-changer')
        if size_changer:
            size_changer.click()
            page.wait_for_timeout(500)
            option = page.query_selector(
                '.ant-select-item-option[title*="100"], .ant-select-item-option[title*="50"]'
            )
            if option:
                option.click()
                page.wait_for_timeout(1500)
    except Exception as e:
        print(f"Gagal mengubah page size: {e}")

def scrape_table_with_pagination(page: Page, target_url: str, target_table_index: int = 2) -> tuple[list, list]:
    print(f"Navigasi ke URL: {target_url}")
    try:
        page.goto(target_url, wait_until='networkidle', timeout=30000)
    except PlaywrightTimeoutError:
        print("Batas waktu navigasi utama habis. Melanjutkan...")

    try:
        page.wait_for_selector('table', timeout=20000)
    except PlaywrightTimeoutError:
        print("Gagal menemukan elemen <table> di halaman.")
        return [], []

    change_page_size(page)

    all_headers = []
    all_rows = []
    seen_rows = set()
    page_count = 1

    while True:
        try:
            html_content = page.content()
            headers, rows = parse_table_from_html(html_content, target_table_index)

            if not all_headers and headers:
                all_headers = headers

            new_entries = 0
            for r in rows:
                t = tuple(r)
                if t not in seen_rows:
                    seen_rows.add(t)
                    all_rows.append(r)
                    new_entries += 1

            next_li = page.query_selector('li.ant-pagination-next')
            if not next_li:
                break

            is_disabled = page.evaluate("""(li) => {
                return li.classList.contains('ant-pagination-disabled') || 
                       li.getAttribute('aria-disabled') === 'true';
            }""", next_li)

            if is_disabled:
                break

            next_btn = next_li.query_selector('button, a')
            if not next_btn:
                break

            next_btn.click()
            page_count += 1
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Selesai atau kendala paginasi pada Halaman {page_count}: {e}")
            break

    return all_headers, all_rows

def clean_and_save_dataframe(df: pd.DataFrame, output_csv: str) -> None:
    for col in df.columns:
        if col in NUMERIC_COLUMNS or any(k in col.lower() for k in ['total', 'simpanan', 'volume', 'nilai', 'koperasi', 'pct', 'lahan', 'gerai']):
            if col not in ['province_name', 'regency_name', 'no', 'regency_no', 'province_id']:
                df[col] = clean_number_col(df[col])

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"[BERHASIL] Dataset terstandardisasi numerik ({len(df)} baris) disimpan ke: {output_csv}")

def load_scraped_province_ids() -> list:
    prov_ids = []
    geo_id_map = {}
    if os.path.exists(GEO_PROVINCES_JSON):
        try:
            with open(GEO_PROVINCES_JSON, encoding='utf-8') as f:
                prov_data = json.load(f)
                geo_id_map = {p['name'].strip().upper(): int(p['province_id']) for p in prov_data if 'name' in p}
        except Exception as e:
            print(f"Gagal memuat province.json: {e}")

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
        except Exception as e:
            print(f"Gagal membaca province IDs dari {RAW_PROVINCES_CSV}: {e}")
    return prov_ids

def scrape_single_regency(prov_id: int, url_template: str, table_index: int = 2) -> tuple[list, list]:
    url = url_template.format(id=prov_id)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        headers, rows = scrape_table_with_pagination(page, url, target_table_index=table_index)
        browser.close()
    labeled_rows = [[prov_id] + r for r in rows]
    return headers, labeled_rows

def main():
    print("=== 1. Scraping Data Tingkat Provinsi ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        headers, rows = scrape_table_with_pagination(page, SCRAPE_TARGET_URL, target_table_index=SCRAPE_TABLE_INDEX)
        browser.close()

    if headers and rows:
        mapped_headers = map_column_headers(headers, PROVINCE_COLUMN_MAPPING)
        df_prov = pd.DataFrame(rows, columns=mapped_headers)
        clean_and_save_dataframe(df_prov, RAW_PROVINCES_CSV)
        print(f"Ekstraksi data provinsi selesai ({len(df_prov)} entri).")

    print("\n=== 2. Scraping Data Tingkat Kabupaten/Kota ===")
    prov_ids = load_scraped_province_ids()
    print(f"Memulai scraping {len(prov_ids)} kabupaten/kota dengan {SCRAPE_MAX_WORKERS} worker threads...")

    all_rows = []
    final_headers = []

    with ThreadPoolExecutor(max_workers=SCRAPE_MAX_WORKERS) as executor:
        futures = {executor.submit(scrape_single_regency, pid, SCRAPE_BASE_URL_TEMPLATE, SCRAPE_TABLE_INDEX): pid for pid in prov_ids}
        for future in as_completed(futures):
            pid = futures[future]
            try:
                h, r = future.result()
                if h and not final_headers:
                    final_headers = ['province_id'] + map_column_headers(h, REGENCY_COLUMN_MAPPING)
                all_rows.extend(r)
                print(f"Provinsi ID {pid}: Berhasil mengekstrak {len(r)} baris kabupaten/kota.")
            except Exception as e:
                print(f"Provinsi ID {pid} gagal diekstrak: {e}")

    if final_headers and all_rows:
        df_reg = pd.DataFrame(all_rows, columns=final_headers)
        clean_and_save_dataframe(df_reg, RAW_REGENCIES_CSV)
        print(f"Ekstraksi data kabupaten/kota selesai ({len(df_reg)} entri).")

if __name__ == "__main__":
    main()
