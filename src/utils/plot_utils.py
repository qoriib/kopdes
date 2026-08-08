import os
import matplotlib.pyplot as plt
from utils.log_utils import get_logger

logger = get_logger("plot_utils")

def save_plot_to_file(fig, filepath, dpi=120):
    """
    Save a matplotlib figure to a PNG file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, format='png', dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Plot saved to: {filepath}")

