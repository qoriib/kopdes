from utils.log_utils import get_logger
from deployment.deployment_seed import run_seed

logger = get_logger("deployment.main")

def main():
    logger.info("=== Memulai Eksekusi Stage CRISP-DM: Deployment ===")
    
    logger.info("--> Menjalankan Task: Generating Cloudflare D1 Database Seed")
    run_seed()
    
    logger.info("=== Stage CRISP-DM: Deployment Selesai ===")

if __name__ == "__main__":
    main()
