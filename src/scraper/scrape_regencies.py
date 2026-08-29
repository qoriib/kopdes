import os
import sys

# Ensure src root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_utils import get_logger
from utils.scraper_utils import scrape_all_regencies
from config import (
    RAW_REGENCIES_CSV,
    RAW_PROVINCES_CSV,
    SCRAPE_BASE_URL_TEMPLATE,
    SCRAPE_MAX_WORKERS
)

logger = get_logger("scraper.scrape_regencies")

def main():
    logger.info("Memulai ekstraksi mandiri data tingkat kabupaten/kota dari SIMKOPDES...")
    os.makedirs(os.path.dirname(RAW_REGENCIES_CSV), exist_ok=True)
    scrape_all_regencies(
        RAW_PROVINCES_CSV,
        RAW_REGENCIES_CSV,
        SCRAPE_BASE_URL_TEMPLATE,
        max_workers=SCRAPE_MAX_WORKERS
    )
    logger.info("Ekstraksi data kabupaten/kota selesai.")

if __name__ == "__main__":
    main()
