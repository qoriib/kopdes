from utils.log_utils import get_logger
from modeling.modeling_train import run_train

logger = get_logger("modeling.main")

def main():
    logger.info("=== Memulai Eksekusi Stage CRISP-DM: Modeling ===")
    
    logger.info("--> Menjalankan Task: KMeans Training & Kneedle Optimization")
    run_train()
    
    logger.info("=== Stage CRISP-DM: Modeling Selesai ===")

if __name__ == "__main__":
    main()
