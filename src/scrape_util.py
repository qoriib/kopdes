import os
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

# KONFIGURASI PARAMETER SCRAPING
SCRAPE_TABLE_INDEX = 2
SCRAPE_TARGET_URL = "https://simkopdes.go.id/pers/dashboard"
SCRAPE_BASE_URL_TEMPLATE = "https://simkopdes.go.id/pers/dashboard/district/{id}"


# FUNGSI PARSING HTML KE DATA TABEL
def parse_table_from_html(html_content: str, target_index: int = 2) -> tuple[list, list]:
    soup = BeautifulSoup(html_content, "html.parser")
    table_elements = soup.find_all("table")

    if not table_elements:
        return [], []

    selected_table = table_elements[target_index - 1]

    # Ekstrak header tabel
    header_names = []
    for th_element in selected_table.select("thead th"):
        header_text = th_element.get_text(strip=True)
        header_names.append(header_text)

    # Ekstrak baris data tabel
    data_rows = []
    for row_element in selected_table.select("tbody tr.ant-table-row"):
        row_cells = []
        for cell_element in row_element.find_all("td"):
            cell_text = cell_element.get_text(strip=True)
            row_cells.append(cell_text)
        data_rows.append(row_cells)

    return header_names, data_rows


# FUNGSI SCRAPING TABEL BESERTA PAGINATION
def scrape_table_with_pagination(page: Page, target_url: str, target_table_index: int = 2) -> tuple[list, list]:
    print(f"Navigasi ke URL: {target_url}")

    try:
        page.goto(target_url, wait_until="networkidle", timeout=30000)
        page.wait_for_selector("table", timeout=20000)
    except PlaywrightTimeoutError:
        print("Batas waktu navigasi / tabel tidak ditemukan.")
        return [], []

    all_table_headers = []
    all_table_rows = []
    seen_row_signatures = set()

    while True:
        current_html = page.content()
        extracted_headers, extracted_rows = parse_table_from_html(current_html, target_table_index)

        if not all_table_headers and extracted_headers:
            all_table_headers = extracted_headers

        for row_data in extracted_rows:
            row_signature = tuple(row_data)
            if row_signature not in seen_row_signatures:
                seen_row_signatures.add(row_signature)
                all_table_rows.append(row_data)

        # Cek tombol pagination berikutnya
        next_button = page.query_selector(
            "li.ant-pagination-next:not(.ant-pagination-disabled) button, "
            "li.ant-pagination-next:not(.ant-pagination-disabled) a"
        )

        if not next_button:
            break

        next_button.click()
        page.wait_for_timeout(2000)

    return all_table_headers, all_table_rows


# FUNGSI MEMUAT ID PROVINSI DARI CSV
def load_scraped_province_ids(raw_prov_csv: str) -> list:
    province_ids = []

    try:
        dataframe_provinces = pd.read_csv(raw_prov_csv)
        province_series = dataframe_provinces["No"].dropna().astype(int)
        province_ids = province_series.tolist()
    except Exception as error_message:
        print(f"Gagal membaca ID provinsi dari {raw_prov_csv}: {error_message}")

    return province_ids
