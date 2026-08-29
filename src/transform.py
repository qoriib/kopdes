import os
import json
import pandas as pd
from utils.log_utils import get_logger
from config import (
    RAW_PROVINCES_CSV,
    RAW_REGENCIES_CSV,
    TRANSFORMED_PROVINCES_CSV,
    TRANSFORMED_REGENCIES_CSV,
    GEO_PROVINCES_JSON,
    GEO_REGENCIES_JSON
)

logger = get_logger("transform")

PROVINCE_RENAME_MAP = {
    'Provinsi': 'province_name',
    'Jumlah Koperasi': 'jumlah_koperasi',
    'Koperasi Memiliki NIB': 'koperasi_nib',
    'Koperasi Memiliki NPWP': 'koperasi_npwp',
    'Koperasi Telah RAT (2025)': 'koperasi_rat',
    'Simpanan Pokok': 'simpanan_pokok',
    'Simpanan Wajib': 'simpanan_wajib',
    'Volume Transaksi (2026)': 'volume_transaksi',
    'Nilai Transaksi (2026)': 'nilai_transaksi',
    'Pemetahaan Lahan': 'pemetahaan_lahan',
    'Pemetahaan Lahan (%)': 'pemetahaan_lahan_pct',
    'Pembangunan Gerai (%)': 'pembangunan_gerai_pct'
}

REGENCIES_RENAME_MAP = {
    'Province_ID': 'province_id',
    'No': 'regency_no',
    'Kabupaten/Kota': 'regency_name',
    'Jumlah Koperasi': 'jumlah_koperasi',
    'Koperasi Memiliki NIB': 'koperasi_nib',
    'Koperasi Memiliki NPWP': 'koperasi_npwp',
    'Koperasi Telah RAT (2025)': 'koperasi_rat',
    'Simpanan Pokok': 'simpanan_pokok',
    'Simpanan Wajib': 'simpanan_wajib',
    'Volume Transaksi (2026)': 'volume_transaksi',
    'Nilai Transaksi (2026)': 'nilai_transaksi'
}

def clean_number_col(series: pd.Series) -> pd.Series:
    """Membersihkan format mata uang/angka Indonesia dan mengonversi ke numerik."""
    return (
        series.astype(str)
        .str.replace(r'[Rp%\s]', '', regex=True)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .pipe(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

def load_geo_json(filepath: str) -> list:
    """Membaca file JSON geografi jika tersedia."""
    if os.path.exists(filepath):
        with open(filepath, encoding='utf-8') as f:
            return json.load(f)
    return []

def transform_provinces():
    """Transformasi data provinsi & gabung koordinat geografis."""
    logger.info(f"Transforming Provinsi dari {RAW_PROVINCES_CSV}...")
    df = pd.read_csv(RAW_PROVINCES_CSV)

    # 1. Bersihkan Kolom Numerik
    num_cols = [c for c in df.columns if c not in ['No', 'Provinsi']]
    for col in num_cols:
        df[col] = clean_number_col(df[col])

    # 2. Mapping Geografi (Nama -> ID, Lat, Lon)
    geo_data = load_geo_json(GEO_PROVINCES_JSON)
    geo_df = pd.DataFrame(geo_data)

    if not geo_df.empty:
        geo_df['province_name_clean'] = geo_df['name'].astype(str).str.strip().str.upper()
        df['province_name_clean'] = df['Provinsi'].astype(str).str.strip().str.upper()

        df = df.merge(
            geo_df[['province_name_clean', 'province_id', 'latitude', 'longitude']],
            on='province_name_clean',
            how='left'
        ).drop(columns=['province_name_clean'])

    # 3. Rename & Reorder Kolom
    df = df.rename(columns=PROVINCE_RENAME_MAP).fillna(0)
    df.to_csv(TRANSFORMED_PROVINCES_CSV, index=False)
    logger.info(f"Transformed {len(df)} provinsi -> {TRANSFORMED_PROVINCES_CSV}")

def transform_regencies():
    """Transformasi data kabupaten/kota & gabung koordinat geografis."""
    logger.info(f"Transforming Kabupaten/Kota dari {RAW_REGENCIES_CSV}...")
    df = pd.read_csv(RAW_REGENCIES_CSV)

    # 1. Bersihkan Kolom Numerik
    num_cols = [c for c in df.columns if c not in ['Kabupaten/Kota']]
    for col in num_cols:
        df[col] = clean_number_col(df[col])

    # 2. Mapping Geografi (Province ID + Regency No -> Lat, Lon)
    geo_data = load_geo_json(GEO_REGENCIES_JSON)
    geo_df = pd.DataFrame(geo_data)

    if not geo_df.empty:
        df = df.merge(
            geo_df[['province_id', 'regency_no', 'latitude', 'longitude']],
            left_on=['Province_ID', 'No'],
            right_on=['province_id', 'regency_no'],
            how='left'
        )

    # 3. Rename & Reorder Kolom
    df = df.rename(columns=REGENCIES_RENAME_MAP).fillna(0)
    df.to_csv(TRANSFORMED_REGENCIES_CSV, index=False)
    logger.info(f"Transformed {len(df)} kabupaten/kota -> {TRANSFORMED_REGENCIES_CSV}")

def main():
    logger.info("Memulai Stage Data Transformation...")
    transform_provinces()
    transform_regencies()
    logger.info("Transformation selesai.")

if __name__ == "__main__":
    main()
