import os
from utils.log_utils import get_logger

logger = get_logger("env_utils")

def load_env():
    """
    Load environment variables from root .env file.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_file = os.path.join(base_dir, ".env")
    if os.path.exists(env_file):
        logger.info(f"Loading environment variables from: {env_file}")
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    else:
        logger.warning(f"Environment file not found at: {env_file}")
