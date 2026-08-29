from utils.log_utils import get_logger
from understanding.understanding_describe import run_describe
from understanding.understanding_explore import run_explore
from understanding.understanding_quality import run_quality

logger = get_logger("understanding.main")

def main():
    logger.info("=== Memulai Eksekusi Stage CRISP-DM: Understanding ===")
    
    logger.info("--> [1/3] Menjalankan Task: Describe Data")
    run_describe()
    
    logger.info("--> [2/3] Menjalankan Task: Explore Data (EDA & Correlations)")
    run_explore()
    
    logger.info("--> [3/3] Menjalankan Task: Verify Data Quality")
    run_quality()
    
    logger.info("=== Stage CRISP-DM: Understanding Selesai ===")

if __name__ == "__main__":
    main()
