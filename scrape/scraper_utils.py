import csv
import sys
import os
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def is_header_row(row):
    """
    Mengecek apakah baris data merupakan judul kolom/header
    """
    if not row:
        return True
    c0 = str(row[0]).strip().lower()
    c1 = str(row[1]).strip().lower() if len(row) > 1 else ""
    if c0 == 'no' or c1 in ('provinsi', 'kabupaten/kota', 'kabupaten', 'kota') or 'provinsi' in c0:
        return True
    return False

def parse_table_from_html(html, target_index=2):
    """
    Parsir tabel HTML berdasarkan indeks target menggunakan BeautifulSoup
    """
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
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

def scrape_table_with_pagination(page, target_url, target_table_index=2):
    """
    Mengekstrak tabel dengan dukungan penuh paginasi Ant Design di Playwright
    """
    page.goto(target_url, wait_until='networkidle', timeout=40000)
    page.wait_for_selector('table', timeout=15000)

    # Coba ubah opsi page size ke 100/page atau 50/page jika dropdown Ant Design tersedia
    try:
        size_changer = page.query_selector('.ant-pagination-options-size-changer')
        if size_changer:
            size_changer.click()
            page.wait_for_timeout(300)
            option = page.query_selector('.ant-select-item-option[title*="100"], .ant-select-item-option[title*="50"]')
            if option:
                option.click()
                page.wait_for_timeout(1000)
    except Exception:
        pass

    all_headers = []
    all_rows = []
    seen_rows = set()

    while True:
        html_content = page.content()
        headers, rows = parse_table_from_html(html_content, target_table_index)

        if not all_headers and headers:
            all_headers = headers

        for r in rows:
            t = tuple(r)
            if t not in seen_rows:
                seen_rows.add(t)
                all_rows.append(r)

        # Cek tombol Next pada pagination Ant Design
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
        page.wait_for_timeout(1500)

    return all_headers, all_rows

def save_to_csv(filename, headers, rows):
    """
    Menyimpan data ke berkas CSV (utf-8 dengan BOM)
    Memastikan direktori tujuan (misal data/) dibuat secara otomatis.
    """
    if headers and rows:
        parent_dir = os.path.dirname(filename)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"[SAVED] File CSV -> {filename}")
