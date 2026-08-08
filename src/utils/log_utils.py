import logging
import sys

_root_configured = False

def get_logger(name: str) -> logging.Logger:
    """
    Get or configure a logger with consistent formatting for the pipeline stages.
    """
    global _root_configured
    if not _root_configured:
        # Konfigurasi root logging basic configuration agar format seragam
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] (%(name)s) %(message)s',
            datefmt='%H:%M:%S',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        _root_configured = True
        
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
