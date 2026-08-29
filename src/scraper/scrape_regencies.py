import os

from utils.log_utils import get_logger
from utils.scraper_utils import scrape_all_regencies
from config import RAW_REGENCIES_CSV, SCRAPE_BASE_URL_TEMPLATE, SCRAPE_TABLE_INDEX, SCRAPE_MAX_WORKERS

logger = get_logger("scraper.scrape_regencies")

def main():
    logger.info("Memulai ekstraksi mandiri seluruh data kabupaten/kota dari SIMKOPDES...")
    os.makedirs(os.path.dirname(RAW_REGENCIES_CSV), exist_ok=True)
    scrape_all_regencies(
        base_url_template=SCRAPE_BASE_URL_TEMPLATE,
        output_filename=RAW_REGENCIES_CSV,
        target_table_index=SCRAPE_TABLE_INDEX,
        max_workers=SCRAPE_MAX_WORKERS
    )
    logger.info("Ekstraksi data kabupaten/kota selesai.")

if __name__ == "__main__":
    main()
