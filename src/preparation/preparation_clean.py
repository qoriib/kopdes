import os
import json
import pandas as pd
import numpy as np

from utils.log_utils import get_logger
from utils.data_utils import clean_number_col
from config import (
    RAW_PROVINCES_CSV,
    RAW_REGENCIES_CSV,
    GEO_PROVINCES_JSON,
    GEO_REGENCIES_JSON,
    CLEANED_PROVINCES_CSV,
    CLEANED_REGENCIES_CSV
)

logger = get_logger("preparation.clean")

def load_geo_json(filepath: str) -> list:
    """Membaca file JSON koordinat geografis jika tersedia."""
    if os.path.exists(filepath):
        with open(filepath, encoding='utf-8') as f:
            return json.load(f)
    return []

def clean_provinces_data():
    """Pembersihan dan standardisasi data level provinsi."""
    logger.info(f"Membersihkan data provinsi dari {RAW_PROVINCES_CSV}...")
    df = pd.read_csv(RAW_PROVINCES_CSV)

    num_cols = [c for c in df.columns if c not in ['no', 'province_name', 'province_id', 'latitude', 'longitude']]
    for col in num_cols:
        df[col] = clean_number_col(df[col])

    df['province_name'] = df['province_name'].astype(str).str.strip().str.upper()

    geo_data = load_geo_json(GEO_PROVINCES_JSON)
    geo_df = pd.DataFrame(geo_data)

    if not geo_df.empty:
        geo_df['province_name_clean'] = geo_df['name'].astype(str).str.strip().str.upper()
        df = df.merge(
            geo_df[['province_name_clean', 'province_id', 'latitude', 'longitude']],
            left_on='province_name',
            right_on='province_name_clean',
            how='left'
        ).drop(columns=['province_name_clean'], errors='ignore')

    df['rasio_nib'] = np.where(df['total_koperasi'] > 0, (df['koperasi_nib'] / df['total_koperasi']) * 100.0, 0.0).clip(0, 100).round(2)
    df['rasio_npwp'] = np.where(df['total_koperasi'] > 0, (df['koperasi_npwp'] / df['total_koperasi']) * 100.0, 0.0).clip(0, 100).round(2)
    df['rasio_rat'] = np.where(df['total_koperasi'] > 0, (df['koperasi_rat'] / df['total_koperasi']) * 100.0, 0.0).clip(0, 100).round(2)

    os.makedirs(os.path.dirname(CLEANED_PROVINCES_CSV), exist_ok=True)
    df.to_csv(CLEANED_PROVINCES_CSV, index=False)
    logger.info(f"Cleaned {len(df)} provinsi -> {CLEANED_PROVINCES_CSV}")

def clean_regencies_data():
    """Pembersihan, penanganan missing value via median lokal per provinsi, dan standarisasi kabupaten/kota."""
    logger.info(f"Membersihkan data kabupaten/kota dari {RAW_REGENCIES_CSV}...")
    df = pd.read_csv(RAW_REGENCIES_CSV)

    num_cols = [c for c in df.columns if c not in ['province_id', 'regency_no', 'regency_name', 'latitude', 'longitude']]
    for col in num_cols:
        df[col] = clean_number_col(df[col])

    df['regency_name'] = df['regency_name'].astype(str).str.strip().str.upper()

    for col in num_cols:
        df[col] = df.groupby('province_id')[col].transform(lambda s: s.fillna(s.median() if not s.dropna().empty else 0))
        df[col] = df[col].fillna(0)

    geo_data = load_geo_json(GEO_REGENCIES_JSON)
    geo_df = pd.DataFrame(geo_data)

    if not geo_df.empty:
        df = df.merge(
            geo_df[['province_id', 'regency_no', 'latitude', 'longitude']],
            on=['province_id', 'regency_no'],
            how='left'
        )

    df['rasio_nib'] = np.where(df['total_koperasi'] > 0, (df['koperasi_nib'] / df['total_koperasi']) * 100.0, 0.0).clip(0, 100).round(2)
    df['rasio_npwp'] = np.where(df['total_koperasi'] > 0, (df['koperasi_npwp'] / df['total_koperasi']) * 100.0, 0.0).clip(0, 100).round(2)
    df['rasio_rat'] = np.where(df['total_koperasi'] > 0, (df['koperasi_rat'] / df['total_koperasi']) * 100.0, 0.0).clip(0, 100).round(2)

    os.makedirs(os.path.dirname(CLEANED_REGENCIES_CSV), exist_ok=True)
    df.to_csv(CLEANED_REGENCIES_CSV, index=False)
    logger.info(f"Cleaned {len(df)} kabupaten/kota -> {CLEANED_REGENCIES_CSV}")

def run_clean():
    clean_provinces_data()
    clean_regencies_data()

def main():
    logger.info("Memulai Stage Preparation: Clean Data...")
    run_clean()
    logger.info("Stage Preparation: Clean Data selesai.")

if __name__ == "__main__":
    main()
