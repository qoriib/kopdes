import os
import json
import pandas as pd
import numpy as np

from utils.log_utils import get_logger
from utils.data_utils import clean_number_col
from utils.report_utils import generate_report_from_template
from config import (
    RAW_REGENCIES_CSV,
    DATA_QUALITY_REPORT_MD,
    DATA_QUALITY_METRICS_JSON,
    DATA_QUALITY_TEMPLATE_MD,
    IGNORED_METADATA_COLUMNS
)

logger = get_logger("understanding.quality")

def run_quality():
    logger.info("Menjalankan CRISP-DM: Understanding - Verify Data Quality...")

    if not os.path.exists(RAW_REGENCIES_CSV):
        raise FileNotFoundError(f"File {RAW_REGENCIES_CSV} tidak ditemukan.")

    df_raw = pd.read_csv(RAW_REGENCIES_CSV)
    total_samples = len(df_raw)

    # 1. Uji Kelengkapan (Completeness)
    missing_counts = df_raw.isnull().sum()
    missing_headers = ["Kolom / Atribut", "Jumlah Nilai Kosong (NaN)", "Persentase Kelengkapan"]
    missing_rows = ""
    for col, null_count in missing_counts.items():
        pct_complete = round(((total_samples - null_count) / total_samples) * 100, 2)
        missing_rows += f"| `{col}` | {null_count} | {pct_complete}% |\n"

    missing_values_table = "| " + " | ".join(missing_headers) + " |\n" + "| :--- | :---: | :---: |\n" + missing_rows

    # 2. Uji Keunikan (Uniqueness)
    duplicate_rows = int(df_raw.duplicated().sum())
    duplicate_keys = int(df_raw.duplicated(subset=['province_id', 'regency_no']).sum()) if 'province_id' in df_raw.columns and 'regency_no' in df_raw.columns else 0

    # 3. Uji Konsistensi Format Penulisan Wilayah
    name_col = 'regency_name' if 'regency_name' in df_raw.columns else 'Kabupaten/Kota'
    is_upper = df_raw[name_col].astype(str).str.isupper().all() if name_col in df_raw.columns else False
    naming_consistency_status = "100% Huruf Kapital Sesuai Standar Administrasi" if is_upper else "Sebagian Perlu Penyeragaman Kapital"

    # 4. Uji Kemiringan Distribusi & Deteksi Pencilan (IQR Method)
    num_cols = [c for c in df_raw.columns if c not in IGNORED_METADATA_COLUMNS]
    outlier_headers = ["Nama Fitur", "Skewness (Kemiringan)", "Batas Bawah (IQR)", "Batas Atas (IQR)", "Jumlah Outliers", "Persentase Outliers"]
    outlier_rows = ""

    outlier_metrics = {}

    for col in num_cols:
        series_clean = clean_number_col(df_raw[col])
        q1 = float(series_clean.quantile(0.25))
        q3 = float(series_clean.quantile(0.75))
        iqr = q3 - q1
        lower = max(0.0, q1 - 1.5 * iqr)
        upper = q3 + 1.5 * iqr
        outliers_count = int(((series_clean < lower) | (series_clean > upper)).sum())
        outliers_pct = round((outliers_count / total_samples) * 100, 2)
        skew_val = round(float(series_clean.skew()), 2)

        outlier_metrics[col] = {
            "skewness": skew_val,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "outliers_count": outliers_count,
            "outliers_pct": outliers_pct
        }

        if "nilai" in col or "simpanan" in col:
            low_str = f"Rp {lower:,.0f}"
            up_str = f"Rp {upper:,.0f}"
        else:
            low_str = f"{lower:,.1f}"
            up_str = f"{upper:,.1f}"

        outlier_rows += f"| **`{col}`** | {skew_val} | {low_str} | {up_str} | {outliers_count} | {outliers_pct}% |\n"

    outlier_summary_table = "| " + " | ".join(outlier_headers) + " |\n" + "| :--- | :---: | :---: | :---: | :---: | :---: |\n" + outlier_rows

    # 5. Simpan Metrik Kualitas Data ke JSON
    metrics = {
        "data_quality": {
            "total_samples": total_samples,
            "duplicate_rows": duplicate_rows,
            "duplicate_keys": duplicate_keys,
            "is_naming_capital_standard": bool(is_upper),
            "feature_quality": outlier_metrics
        }
    }

    os.makedirs(os.path.dirname(DATA_QUALITY_METRICS_JSON), exist_ok=True)
    with open(DATA_QUALITY_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Data Quality Metrics -> {DATA_QUALITY_METRICS_JSON}")

    # 6. Generate Markdown Report
    replacements = {
        "{{total_samples}}": str(total_samples),
        "{{missing_values_table}}": missing_values_table,
        "{{duplicate_rows_count}}": str(duplicate_rows),
        "{{duplicate_keys_count}}": str(duplicate_keys),
        "{{naming_consistency_status}}": naming_consistency_status,
        "{{outlier_summary_table}}": outlier_summary_table,
    }

    generate_report_from_template(DATA_QUALITY_TEMPLATE_MD, DATA_QUALITY_REPORT_MD, replacements)
    logger.info(f"Data Quality Report -> {DATA_QUALITY_REPORT_MD}")

def main():
    run_quality()

if __name__ == "__main__":
    main()
