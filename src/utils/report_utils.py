import os
from utils.log_utils import get_logger

logger = get_logger("report_utils")

def generate_report_from_template(template_path: str, output_path: str, replacements: dict) -> None:
    """
    Load a markdown report template, replace placeholders, and write to output path.

    Args:
        template_path: Absolute path to the template .md file.
        output_path: Absolute path to output the generated .md report.
        replacements: Dict mapping placeholders (e.g. '{{name}}') to their replacement values.
    """
    if not os.path.exists(template_path):
        logger.error(f"Template tidak ditemukan: {template_path}")
        raise FileNotFoundError(f"Template file not found at: {template_path}")

    logger.info(f"Membaca template dari: {template_path}")
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    for key, val in replacements.items():
        content = content.replace(key, str(val))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Laporan berhasil ditulis ke: {output_path}")
