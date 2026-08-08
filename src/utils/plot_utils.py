import os
import io
import base64
import matplotlib.pyplot as plt
from utils.log_utils import get_logger

logger = get_logger("plot_utils")

def file_to_base64(filepath):
    """
    Convert any file to a base64 encoded string.
    """
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def generate_base64_plot(fig, dpi=120):
    """
    Save a matplotlib figure to base64 string.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def save_plot_to_file(fig, filepath, dpi=120):
    """
    Save a matplotlib figure to a PNG file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, format='png', dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Plot saved to: {filepath}")

