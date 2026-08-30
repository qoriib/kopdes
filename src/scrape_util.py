import os
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright, TimeoutError as PlaywrightTimeoutError

# Scraping Configuration Parameters
SCRAPE_TABLE_INDEX = 2
SCRAPE_MAX_WORKERS = 5
SCRAPE_TARGET_URL = "https://simkopdes.go.id/pers/dashboard"
SCRAPE_BASE_URL_TEMPLATE = "https://simkopdes.go.id/pers/dashboard/district/{id}"

def parse_table_from_html(html_content: str, target_index: int = 2) -> tuple[list, list]:
    """
    Parses HTML content from  table and extracts headers and data rows.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    table_elements = soup.find_all("table")
    if not table_elements:
        return [], []

    # Calculate zero-based index safely within available tables
    safe_index = max(1, target_index)
    safe_index = min(safe_index, len(table_elements))
    selected_table = table_elements[safe_index - 1]

    # Extract header text from thead
    header_names = []
    header_th_elements = selected_table.select("thead th")
    for th_element in header_th_elements:
        header_text = th_element.get_text(strip=True)
        header_names.append(header_text)

    # Extract data rows from tbody (filtering to actual data rows with .ant-table-row)
    data_rows = []
    row_elements = selected_table.select("tbody tr.ant-table-row")
    for row_element in row_elements:
        row_cells = []
        cell_elements = row_element.find_all("td")
        for cell_element in cell_elements:
            cell_text = cell_element.get_text(strip=True)
            row_cells.append(cell_text)
        data_rows.append(row_cells)

    return header_names, data_rows

def change_page_size(page: Page) -> None:
    """
    Changes table pagination size to 50/100 to reduce total page navigation count.
    """
    try:
        size_changer_button = page.query_selector(".ant-pagination-options-size-changer")
        if size_changer_button:
            size_changer_button.click()
            page.wait_for_timeout(500)

            page_size_option = page.query_selector(
                '.ant-select-item-option[title*="100"], .ant-select-item-option[title*="50"]'
            )
            if page_size_option:
                page_size_option.click()
                page.wait_for_timeout(1500)
    except Exception as error_message:
        print(f"Gagal mengubah page size: {error_message}")

def scrape_table_with_pagination(page: Page, target_url: str, target_table_index: int = 2) -> tuple[list, list]:
    """
    Navigates to URL and iterates through pagination to extract all raw table rows.
    """
    print(f"Navigasi ke URL: {target_url}")
    try:
        page.goto(target_url, wait_until="networkidle", timeout=30000)
    except PlaywrightTimeoutError:
        print("Batas waktu navigasi utama habis. Melanjutkan...")

    try:
        page.wait_for_selector("table", timeout=20000)
    except PlaywrightTimeoutError:
        print("Gagal menemukan elemen <table> di halaman.")
        return [], []

    change_page_size(page)

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

        # Check if next page button exists and is not disabled
        next_page_item = page.query_selector("li.ant-pagination-next:not(.ant-pagination-disabled)")
        if not next_page_item:
            break

        is_aria_disabled = next_page_item.get_attribute("aria-disabled")
        if is_aria_disabled == "true":
            break

        next_page_clickable = next_page_item.query_selector("button, a")
        if not next_page_clickable:
            break

        next_page_clickable.click()
        page.wait_for_timeout(2000)

    return all_table_headers, all_table_rows

def load_scraped_province_ids(geo_json_path: str, raw_prov_csv: str) -> list:
    """
    Loads province IDs by matching raw province names from geo JSON and the raw scraped provinces CSV.
    """
    matched_province_ids = []
    geo_province_id_lookup = {}

    if os.path.exists(geo_json_path):
        try:
            province_json_data = json.load(open(geo_json_path, encoding="utf-8"))
            for province_entry in province_json_data:
                if "name" in province_entry and "province_id" in province_entry:
                    normalized_province_name = province_entry["name"].strip().upper()
                    province_id_number = int(province_entry["province_id"])
                    geo_province_id_lookup[normalized_province_name] = province_id_number
        except Exception as error_message:
            print(f"Gagal memuat {geo_json_path}: {error_message}")

    if os.path.exists(raw_prov_csv):
        try:
            csv_reader = csv.reader(open(raw_prov_csv, encoding="utf-8-sig"))
            # Skip CSV header line
            next(csv_reader, None)

                for csv_row in csv_reader:
                    if not csv_row or len(csv_row) < 2:
                        continue

                    raw_province_name = csv_row[1].strip().upper()
                    if raw_province_name.lower() == "no data":
                        continue

                    matched_id = geo_province_id_lookup.get(raw_province_name)
                    if matched_id is not None:
                        matched_province_ids.append(matched_id)
        except Exception as error_message:
            print(f"Gagal membaca province IDs dari {raw_prov_csv}: {error_message}")

    return matched_province_ids


def scrape_single_regency(prov_id: int,
                          url_template: str = SCRAPE_BASE_URL_TEMPLATE,
                          table_index: int = SCRAPE_TABLE_INDEX,
                          headless: bool = True) -> tuple[list, list]:
    """
    Scrapes raw regency/district table for a specific province ID.
    """
    target_district_url = url_template.format(id=prov_id)
    with sync_playwright() as playwright_instance:
        browser = playwright_instance.chromium.launch(headless=headless)
        page = browser.new_page()
        table_headers, table_rows = scrape_table_with_pagination(
            page,
            target_district_url,
            target_table_index=table_index
        )
        browser.close()

    labeled_rows_with_province_id = []
    for row_data in table_rows:
        row_with_id = [prov_id] + row_data
        labeled_rows_with_province_id.append(row_with_id)

    return table_headers, labeled_rows_with_province_id
