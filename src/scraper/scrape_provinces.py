import os
import sys

# Ensure src root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_utils import get_logger
from utils.scraper_utils import scrape_provinces_data
from config import RAW_PROVINCES_CSV, SCRAPE_TARGET_URL, SCRAPE_TABLE_INDEX

logger = get_logger("scraper.scrape_provinces")

def main():
    logger.info("Memulai ekstraksi mandiri data tingkat provinsi dari SIMKOPDES...")
    os.makedirs(os.path.dirname(RAW_PROVINCES_CSV), exist_ok=True)
    scrape_provinces_data(SCRAPE_TARGET_URL, RAW_PROVINCES_CSV, table_index=SCRAPE_TABLE_INDEX)
    logger.info("Ekstraksi data provinsi selesai.")

if __name__ == "__main__":
    main()
