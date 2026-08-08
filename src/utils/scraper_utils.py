import csv
import logging
import os
import sys
from bs4 import BeautifulSoup
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

# Konfigurasi UTF-8 untuk output terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Konfigurasi Logging agar tampilan di terminal rapi dan profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("Scraper")


def is_header_row(row: list) -> bool:
    """Mengecek apakah baris data merupakan judul kolom/header."""
    if not row:
        return True
    c0 = str(row[0]).strip().lower()
    c1 = str(row[1]).strip().lower() if len(row) > 1 else ""
    return c0 == 'no' or c1 in ('provinsi', 'kabupaten/kota', 'kabupaten', 'kota') or 'provinsi' in c0


def parse_table_from_html(html: str, target_index: int = 2) -> tuple[list, list]:
    """Parsir tabel HTML berdasarkan indeks target menggunakan BeautifulSoup."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        if not tables:
            logger.warning("Tidak ada tabel (<table/>) yang ditemukan dalam HTML.")
            return [], []

        # Menentukan indeks tabel dengan aman
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

        # Jika thead tidak ada, ambil baris pertama sebagai header
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
        logger.warning(f"Gagal mengubah page size (melanjutkan dengan default): {e}")


def scrape_table_with_pagination(page: Page, target_url: str, target_table_index: int = 2) -> tuple[list, list]:
    """Mengekstrak tabel dengan dukungan penuh paginasi Ant Design di Playwright."""
    logger.info(f"Navigasi ke URL: {target_url}")
    
    # Handling Timeout & Navigasi
    try:
        page.goto(target_url, wait_until='networkidle', timeout=30000)
    except PlaywrightTimeoutError:
        logger.warning("Batas waktu navigasi utama habis. Mencoba melanjutkan pemrosesan...")

    # Memastikan tabel ada sebelum mengekstrak
    try:
        page.wait_for_selector('table', timeout=20000)
    except PlaywrightTimeoutError:
        logger.error("Gagal menemukan elemen <table> di halaman dalam batas waktu 20 detik.")
        return [], []

    # Ubah opsi pagination jika tersedia
    change_page_size(page)

    all_headers = []
    all_rows = []
    seen_rows = set()
    page_count = 1

    while True:
        logger.info(f"Mengekstrak data dari Halaman {page_count}...")
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

            logger.info(f"Halaman {page_count}: Mendapatkan {new_entries} baris baru (Total akumulasi: {len(all_rows)})")

            # Cek Tombol 'Next'
            next_li = page.query_selector('li.ant-pagination-next')
            if not next_li:
                logger.info("Tombol paginasi 'Next' tidak ditemukan. Selesai.")
                break

            is_disabled = page.evaluate("""(li) => {
                return li.classList.contains('ant-pagination-disabled') || 
                       li.getAttribute('aria-disabled') === 'true';
            }""", next_li)

            if is_disabled:
                logger.info("Mencapai halaman terakhir (Tombol 'Next' nonaktif). Selesai.")
                break

            next_btn = next_li.query_selector('button, a')
            if not next_btn:
                logger.warning("Elemen tombol 'Next' tidak dapat diklik. Selesai.")
                break

            next_btn.click()
            page_count += 1
            page.wait_for_timeout(2000)

        except PlaywrightTimeoutError:
            logger.error(f"Timeout terjadi saat pemrosesan Halaman {page_count}.")
            break
        except Exception as e:
            logger.error(f"Terjadi kesalahan tak terduga pada Halaman {page_count}: {e}")
            break

    return all_headers, all_rows


def save_to_csv(filename: str, headers: list, rows: list) -> bool:
    """
    Menyimpan data ke berkas CSV (utf-8 dengan BOM).
    Memastikan direktori tujuan dibuat secara otomatis.
    """
    if not headers and not rows:
        logger.warning("Tidak ada data untuk disimpan ke CSV (Header dan Rows kosong).")
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

    except PermissionError:
        logger.error(f"Gagal menyimpan: Akses ditolak ke file '{filename}'. Cek apakah file sedang dibuka aplikasi lain.")
    except IOError as e:
        logger.error(f"Gagal melakukan I/O file pada '{filename}': {e}")
    except Exception as e:
        logger.error(f"Gagal menyimpan file CSV: {e}")

    return False