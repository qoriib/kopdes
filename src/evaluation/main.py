from utils.log_utils import get_logger
from evaluation.evaluation_metrics import run_metrics
from evaluation.evaluation_interpret import run_interpret

logger = get_logger("evaluation.main")

def main():
    logger.info("=== Memulai Eksekusi Stage CRISP-DM: Evaluation ===")
    
    logger.info("--> [1/2] Menjalankan Task: Metrics Calculation & Visualizations")
    run_metrics()
    
    logger.info("--> [2/2] Menjalankan Task: AI Cluster Interpretation")
    run_interpret()
    
    logger.info("=== Stage CRISP-DM: Evaluation Selesai ===")

if __name__ == "__main__":
    main()
