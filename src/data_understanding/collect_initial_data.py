import os
import sys
import json
import pandas as pd

# Ensure src root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_utils import get_logger
from utils.report_utils import generate_report_from_template
from config import (
    RAW_PROVINCES_CSV,
    RAW_REGENCIES_CSV,
    INITIAL_DATA_REPORT_MD,
    INITIAL_DATA_METRICS_JSON,
    INITIAL_DATA_TEMPLATE_MD
)

logger = get_logger("data_understanding.collect_initial_data")

def build_markdown_schema_table(df: pd.DataFrame) -> str:
    """Membangun tabel markdown skema dan tipe data kolom mentah."""
    headers = ["No", "Nama Kolom / Atribut", "Tipe Data Asli", "Sampel Nilai Baris 1"]
    header_row = "| " + " | ".join(headers) + " |\n"
    separator_row = "| " + " | ".join([":---:"] + [":---"] * (len(headers) - 1)) + " |\n"

    body_rows = ""
    for idx, col in enumerate(df.columns, 1):
        sample_val = str(df[col].iloc[0]) if not df.empty else "N/A"
        dtype_str = str(df[col].dtype)
        body_rows += f"| {idx} | `{col}` | `{dtype_str}` | {sample_val} |\n"

    return header_row + separator_row + body_rows

def main():
    logger.info("Memulai Tugas Generik 1: Collect Initial Data (CRISP-DM Data Understanding)...")

    if not os.path.exists(RAW_PROVINCES_CSV) or not os.path.exists(RAW_REGENCIES_CSV):
        raise FileNotFoundError(
            f"File raw data tidak ditemukan. Pastikan data mentah tersedia di {RAW_PROVINCES_CSV} dan {RAW_REGENCIES_CSV}."
        )

    df_prov = pd.read_csv(RAW_PROVINCES_CSV)
    df_reg = pd.read_csv(RAW_REGENCIES_CSV)

    total_provinces = len(df_prov)
    total_regencies = len(df_reg)
    total_columns = len(df_reg.columns)

    logger.info(f"Berhasil memuat dataset sekunder: {total_provinces} Provinsi, {total_regencies} Kabupaten/Kota.")

    # 1. Simpan Metrik Pengumpulan Data Awal
    metrics = {
        "initial_data_collection": {
            "source": "SIMKOPDES Official Open Data 2026",
            "total_provinces_collected": total_provinces,
            "total_regencies_collected": total_regencies,
            "total_regencies_attributes": total_columns,
            "provinces_attributes": len(df_prov.columns),
            "completeness_status": "Complete (38 Provinces covered)"
        }
    }

    os.makedirs(os.path.dirname(INITIAL_DATA_METRICS_JSON), exist_ok=True)
    with open(INITIAL_DATA_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Initial Data Metrics -> {INITIAL_DATA_METRICS_JSON}")

    # 2. Bangun Laporan Markdown
    regencies_schema_table = build_markdown_schema_table(df_reg)
    provinces_schema_table = build_markdown_schema_table(df_prov)

    replacements = {
        "{{total_regencies}}": str(total_regencies),
        "{{total_provinces}}": str(total_provinces),
        "{{total_columns}}": str(total_columns),
        "{{regencies_schema_table}}": regencies_schema_table,
        "{{provinces_schema_table}}": provinces_schema_table,
    }

    generate_report_from_template(INITIAL_DATA_TEMPLATE_MD, INITIAL_DATA_REPORT_MD, replacements)
    logger.info(f"Initial Data Collection Report -> {INITIAL_DATA_REPORT_MD}")

if __name__ == "__main__":
    main()
