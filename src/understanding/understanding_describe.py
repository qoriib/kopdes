import os
import json
import pandas as pd

from utils.log_utils import get_logger
from utils.data_utils import clean_number_col
from utils.report_utils import generate_report_from_template
from config import (
    RAW_REGENCIES_CSV,
    DATA_DESC_REPORT_MD,
    DATA_DESC_METRICS_JSON,
    DATA_DESC_TEMPLATE_MD,
    NUMERIC_COLUMNS
)

logger = get_logger("understanding.describe")

def run_describe():
    logger.info("Menjalankan CRISP-DM: Understanding - Describe Data...")

    if not os.path.exists(RAW_REGENCIES_CSV):
        raise FileNotFoundError(f"File {RAW_REGENCIES_CSV} tidak ditemukan.")

    df_raw = pd.read_csv(RAW_REGENCIES_CSV)
    total_rows = len(df_raw)
    total_cols = len(df_raw.columns)

    # Bersihkan kolom numerik
    df_clean = df_raw.copy()
    for col in NUMERIC_COLUMNS:
        if col in df_clean.columns:
            df_clean[col] = clean_number_col(df_clean[col])

    # 1. Statistik Deskriptif Menggunakan pandas.describe()
    desc_df = df_clean[NUMERIC_COLUMNS].describe(percentiles=[0.5]).T
    desc_df = desc_df.rename(columns={'50%': 'median', 'std': 'std_dev'})

    # 2. Pembuatan Markdown Table
    headers = ["Nama Variabel", "Count", "Mean", "Median", "Std Dev", "Min", "Max"]
    header_row = "| " + " | ".join(headers) + " |\n"
    separator_row = "| " + " | ".join([":---"] + [":---:"] * (len(headers) - 1)) + " |\n"

    body_rows = ""
    for var_name, row in desc_df.iterrows():
        label = var_name.replace("_", " ").title()
        is_currency = "nilai" in var_name or "simpanan" in var_name
        fmt = "Rp {:,.2f}" if is_currency else "{:,.2f}"
        int_fmt = "{:,}"

        mean_str = fmt.format(row['mean'])
        median_str = fmt.format(row['median'])
        std_str = fmt.format(row['std_dev'])
        min_str = fmt.format(row['min']) if is_currency else int_fmt.format(int(row['min']))
        max_str = fmt.format(row['max']) if is_currency else int_fmt.format(int(row['max']))

        body_rows += f"| **`{var_name}`** ({label}) | {int(row['count'])} | {mean_str} | {median_str} | {std_str} | {min_str} | {max_str} |\n"

    descriptive_stats_table = header_row + separator_row + body_rows

    # 3. Simpan Metrik Deskripsi Data ke JSON
    metrics = {
        "data_description": {
            "total_rows": total_rows,
            "total_cols": total_cols,
            "variables": {
                col: {k: round(float(v), 2) for k, v in desc_df.loc[col, ['mean', 'median', 'std_dev', 'min', 'max']].items()}
                for col in NUMERIC_COLUMNS if col in desc_df.index
            }
        }
    }

    os.makedirs(os.path.dirname(DATA_DESC_METRICS_JSON), exist_ok=True)
    with open(DATA_DESC_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Data Description Metrics -> {DATA_DESC_METRICS_JSON}")

    # 4. Generate Markdown Report
    replacements = {
        "{{total_rows}}": str(total_rows),
        "{{total_cols}}": str(total_cols),
        "{{descriptive_stats_table}}": descriptive_stats_table,
    }

    generate_report_from_template(DATA_DESC_TEMPLATE_MD, DATA_DESC_REPORT_MD, replacements)
    logger.info(f"Data Description Report -> {DATA_DESC_REPORT_MD}")

def main():
    run_describe()

if __name__ == "__main__":
    main()
