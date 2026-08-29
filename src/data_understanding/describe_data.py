import os
import sys
import json
import pandas as pd
import numpy as np

# Ensure src root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_utils import get_logger
from utils.report_utils import generate_report_from_template
from config import (
    RAW_REGENCIES_CSV,
    DATA_DESC_REPORT_MD,
    DATA_DESC_METRICS_JSON,
    DATA_DESC_TEMPLATE_MD
)

logger = get_logger("data_understanding.describe_data")

def clean_numeric_col(series: pd.Series) -> pd.Series:
    """Membersihkan format angka/mata uang ke nilai numerik float."""
    return (
        series.astype(str)
        .str.replace(r'[Rp%\s]', '', regex=True)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .pipe(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

def main():
    logger.info("Memulai Tugas Generik 2: Describe Data (CRISP-DM Data Understanding)...")

    if not os.path.exists(RAW_REGENCIES_CSV):
        raise FileNotFoundError(f"File {RAW_REGENCIES_CSV} tidak ditemukan.")

    df_raw = pd.read_csv(RAW_REGENCIES_CSV)
    total_rows = len(df_raw)
    total_cols = len(df_raw.columns)

    # Bersihkan kolom numerik untuk perhitungan statistik deskriptif
    df_clean = df_raw.copy()
    rename_map = {
        'Jumlah Koperasi': 'total_koperasi',
        'Koperasi Memiliki NIB': 'koperasi_nib',
        'Koperasi Memiliki NPWP': 'koperasi_npwp',
        'Koperasi Telah RAT (2025)': 'koperasi_rat',
        'Simpanan Pokok': 'simpanan_pokok',
        'Simpanan Wajib': 'simpanan_wajib',
        'Volume Transaksi (2026)': 'volume_transaksi',
        'Nilai Transaksi (2026)': 'nilai_transaksi'
    }
    df_clean = df_clean.rename(columns=rename_map)

    num_cols = list(rename_map.values())
    for col in num_cols:
        if col in df_clean.columns:
            df_clean[col] = clean_numeric_col(df_clean[col])

    # 1. Perhitungan Statistik Deskriptif Dasar
    desc_df = df_clean[num_cols].describe().T
    # Tambahkan median eksplisit
    desc_df['median'] = df_clean[num_cols].median()
    desc_df = desc_df[['count', 'mean', 'median', 'std', 'min', 'max']]
    desc_df.columns = ['Count', 'Mean', 'Median', 'Std Dev', 'Min', 'Max']

    # Bangun tabel markdown
    headers = ["Nama Variabel", "Count", "Mean", "Median", "Std Dev", "Min", "Max"]
    header_row = "| " + " | ".join(headers) + " |\n"
    separator_row = "| " + " | ".join([":---"] + [":---:"] * (len(headers) - 1)) + " |\n"

    body_rows = ""
    for var_name, row in desc_df.iterrows():
        label = var_name.replace("_", " ").title()
        if "nilai" in var_name or "simpanan" in var_name:
            mean_str = f"Rp {row['Mean']:,.2f}"
            median_str = f"Rp {row['Median']:,.2f}"
            std_str = f"Rp {row['Std Dev']:,.2f}"
            min_str = f"Rp {row['Min']:,.2f}"
            max_str = f"Rp {row['Max']:,.2f}"
        else:
            mean_str = f"{row['Mean']:,.2f}"
            median_str = f"{row['Median']:,.2f}"
            std_str = f"{row['Std Dev']:,.2f}"
            min_str = f"{row['Min']:,}"
            max_str = f"{row['Max']:,}"

        body_rows += f"| **`{var_name}`** ({label}) | {int(row['Count'])} | {mean_str} | {median_str} | {std_str} | {min_str} | {max_str} |\n"

    descriptive_stats_table = header_row + separator_row + body_rows

    # 2. Simpan Metrik Deskripsi Data ke JSON
    metrics = {
        "data_description": {
            "total_rows": total_rows,
            "total_cols": total_cols,
            "variables": {
                col: {
                    "mean": round(float(desc_df.loc[col, 'Mean']), 2),
                    "median": round(float(desc_df.loc[col, 'Median']), 2),
                    "std_dev": round(float(desc_df.loc[col, 'Std Dev']), 2),
                    "min": round(float(desc_df.loc[col, 'Min']), 2),
                    "max": round(float(desc_df.loc[col, 'Max']), 2)
                } for col in num_cols if col in desc_df.index
            }
        }
    }

    os.makedirs(os.path.dirname(DATA_DESC_METRICS_JSON), exist_ok=True)
    with open(DATA_DESC_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Data Description Metrics -> {DATA_DESC_METRICS_JSON}")

    # 3. Generate Markdown Report
    replacements = {
        "{{total_rows}}": str(total_rows),
        "{{total_cols}}": str(total_cols),
        "{{descriptive_stats_table}}": descriptive_stats_table,
    }

    generate_report_from_template(DATA_DESC_TEMPLATE_MD, DATA_DESC_REPORT_MD, replacements)
    logger.info(f"Data Description Report -> {DATA_DESC_REPORT_MD}")

if __name__ == "__main__":
    main()
