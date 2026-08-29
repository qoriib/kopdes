from utils.log_utils import get_logger
from preparation.preparation_clean import run_clean
from preparation.preparation_transform import run_transform

logger = get_logger("preparation.main")

def main():
    logger.info("=== Memulai Eksekusi Stage CRISP-DM: Preparation ===")
    
    logger.info("--> [1/2] Menjalankan Task: Clean Data & Regional Imputation")
    run_clean()
    
    logger.info("--> [2/2] Menjalankan Task: Transform Data (Log-Transform & Z-Score Scaling)")
    run_transform()
    
    logger.info("=== Stage CRISP-DM: Preparation Selesai ===")

if __name__ == "__main__":
    main()
