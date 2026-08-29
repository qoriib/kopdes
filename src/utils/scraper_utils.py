import os
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

from utils.log_utils import get_logger
from utils.data_utils import clean_number_col
from config import (
    PROVINCE_COLUMN_MAPPING,
    REGENCY_COLUMN_MAPPING,
    GEO_PROVINCES_JSON,
    RAW_PROVINCES_CSV
)

logger = get_logger("scraper_utils")

def is_header_row(row: list) -> bool:
    """Mengecek apakah baris data merupakan judul kolom/header."""
    if not row:
        return True
    c0 = str(row[0]).strip().lower()
    c1 = str(row[1]).strip().lower() if len(row) > 1 else ""
    return c0 == 'no' or c1 in ('provinsi', 'kabupaten/kota', 'kabupaten', 'kota') or 'provinsi' in c0

def map_column_headers(headers: list, mapping: dict) -> list:
    """Mengubah nama kolom sesuai dictionary mapping yang ditentukan di config.py."""
    return [mapping.get(h.strip(), mapping.get(h, h.strip().lower().replace(" ", "_"))) for h in headers]

def parse_table_from_html(html: str, target_index: int = 2) -> tuple[list, list]:
    """Parsir tabel HTML berdasarkan indeks target menggunakan BeautifulSoup."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        if not tables:
            logger.warning("Tidak ada tabel (<table/>) yang ditemukan dalam HTML.")
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
        logger.error(f"Gagal memparsing HTML tabel: {e}")
        return [], []

def change_page_size(page: Page) -> None:
    """Mencoba mengubah jumlah item per halaman (Ant Design Pagination)."""
    try:
        size_changer = page.query_selector('.ant-pagination-options-size-changer')
        if size_changer:
            logger.info("Mengubah batas baris per halaman ke maksimum (100/50)...")
            size_changer.click()
            page.wait_for_timeout(500)
            
            option = page.query_selector(
                '.ant-select-item-option[title*="100"], .ant-select-item-option[title*="50"]'
            )
            if option:
                option.click()
                page.wait_for_timeout(1500)
                logger.info("Berhasil mengubah jumlah baris per halaman.")
    except Exception as e:
        logger.warning(f"Gagal mengubah page size: {e}")

def scrape_table_with_pagination(page: Page, target_url: str, target_table_index: int = 2) -> tuple[list, list]:
    """Mengekstrak tabel dengan dukungan penuh paginasi Ant Design di Playwright."""
    logger.info(f"Navigasi ke URL: {target_url}")
    
    try:
        page.goto(target_url, wait_until='networkidle', timeout=30000)
    except PlaywrightTimeoutError:
        logger.warning("Batas waktu navigasi utama habis. Melanjutkan...")

    try:
        page.wait_for_selector('table', timeout=20000)
    except PlaywrightTimeoutError:
        logger.error("Gagal menemukan elemen <table> di halaman.")
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
            logger.warning(f"Selesai atau kendala paginasi pada Halaman {page_count}: {e}")
            break

    return all_headers, all_rows

def save_to_csv(filename: str, headers: list, rows: list) -> bool:
    """Menyimpan data ke berkas CSV (utf-8 dengan BOM)."""
    if not headers and not rows:
        logger.warning("Tidak ada data untuk disimpan ke CSV.")
        return False

    try:
        parent_dir = os.path.dirname(filename)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            if rows:
                writer.writerows(rows)

        logger.info(f"[BERHASIL] Data ({len(rows)} baris) disimpan ke: {filename}")
        return True

    except Exception as e:
        logger.error(f"Gagal menyimpan file CSV {filename}: {e}")
        return False

def scrape_provinces_data(target_url: str, output_csv: str, table_index: int = 2):
    """Mengekstrak data provinsi dan menyimpan ke CSV dengan mapping header config.py."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        headers, rows = scrape_table_with_pagination(page, target_url, target_table_index=table_index)
        browser.close()

    if headers:
        mapped_headers = map_column_headers(headers, PROVINCE_COLUMN_MAPPING)
        save_to_csv(output_csv, mapped_headers, rows)

def scrape_single_regency(prov_id: int, url_template: str, table_index: int = 2) -> tuple[list, list]:
    url = url_template.format(id=prov_id)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        headers, rows = scrape_table_with_pagination(page, url, target_table_index=table_index)
        browser.close()
        
    labeled_rows = [[prov_id] + r for r in rows]
    return headers, labeled_rows

def load_scraped_province_ids() -> list:
    """Memuat daftar province_id yang sudah berhasil discrape."""
    prov_ids = []
    geo_id_map = {}
    if os.path.exists(GEO_PROVINCES_JSON):
        try:
            with open(GEO_PROVINCES_JSON, encoding='utf-8') as f:
                prov_data = json.load(f)
                geo_id_map = {p['name'].strip().upper(): int(p['province_id']) for p in prov_data if 'name' in p}
        except Exception as e:
            logger.error(f"Gagal memuat province.json: {e}")

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
            logger.error(f"Gagal membaca province IDs dari {RAW_PROVINCES_CSV}: {e}")
    return prov_ids

def scrape_all_regencies(base_url_template: str, output_filename: str, target_table_index: int = 2, max_workers: int = 5):
    """Mengekstrak data kabupaten/kota secara paralel dan menyimpan dengan header terstandardisasi."""
    prov_ids = load_scraped_province_ids()
    if not prov_ids:
        logger.error("Tidak ada province IDs yang ditemukan untuk discrape.")
        return

    all_rows = []
    final_headers = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_single_regency, pid, base_url_template, target_table_index): pid for pid in prov_ids}
        for future in as_completed(futures):
            pid = futures[future]
            try:
                h, r = future.result()
                if h and not final_headers:
                    final_headers = ['province_id'] + map_column_headers(h, REGENCY_COLUMN_MAPPING)
                all_rows.extend(r)
                logger.info(f"Provinsi ID {pid}: Berhasil mengekstrak {len(r)} baris kabupaten/kota.")
            except Exception as e:
                logger.error(f"Provinsi ID {pid} gagal diekstrak: {e}")

    if final_headers:
        save_to_csv(output_filename, final_headers, all_rows)
