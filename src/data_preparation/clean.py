import os
import sys
import json
import pandas as pd
import numpy as np

# Ensure src root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_utils import get_logger
from config import (
    RAW_PROVINCES_CSV,
    RAW_REGENCIES_CSV,
    GEO_PROVINCES_JSON,
    GEO_REGENCIES_JSON,
    CLEANED_PROVINCES_CSV,
    CLEANED_REGENCIES_CSV
)

logger = get_logger("data_preparation.clean")

def clean_number_col(series: pd.Series) -> pd.Series:
    """Membersihkan format mata uang / angka Indonesia dan konversi ke numerik."""
    return (
        series.astype(str)
        .str.replace(r'[Rp%\s]', '', regex=True)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .pipe(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

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

    # 1. Bersihkan Kolom Numerik
    num_cols = [c for c in df.columns if c not in ['No', 'Provinsi']]
    for col in num_cols:
        df[col] = clean_number_col(df[col])

    # 2. Penyeragaman Penamaan Wilayah (Kapital Standar)
    df['Provinsi'] = df['Provinsi'].astype(str).str.strip().str.upper()

    # 3. Mapping Geografi (Nama -> ID, Lat, Lon)
    geo_data = load_geo_json(GEO_PROVINCES_JSON)
    geo_df = pd.DataFrame(geo_data)

    if not geo_df.empty:
        geo_df['province_name_clean'] = geo_df['name'].astype(str).str.strip().str.upper()
        df = df.merge(
            geo_df[['province_name_clean', 'province_id', 'latitude', 'longitude']],
            left_on='Provinsi',
            right_on='province_name_clean',
            how='left'
        ).drop(columns=['province_name_clean'])

    # 4. Standardisasi Nama Kolom & Hitung Rasio
    rename_map = {
        'Provinsi': 'province_name',
        'Jumlah Koperasi': 'total_koperasi',
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
    df = df.rename(columns=rename_map).fillna(0)

    # Hitung rasio operasional (0 - 100%)
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

    # 1. Bersihkan Kolom Numerik
    num_cols = [c for c in df.columns if c not in ['Province_ID', 'No', 'Kabupaten/Kota']]
    for col in num_cols:
        df[col] = clean_number_col(df[col])

    # 2. Penyeragaman Penamaan Wilayah (Kapital Standar)
    df['Kabupaten/Kota'] = df['Kabupaten/Kota'].astype(str).str.strip().str.upper()

    # 3. Penanganan Missing Values / Nilai Nol Ekstrem Menggunakan Imputasi Median Lokal per Provinsi
    # Untuk nilai finansial yang bernilai NaN atau null, isi dengan median per Province_ID
    for col in num_cols:
        # Ganti nilai null dengan median per provinsi
        df[col] = df.groupby('Province_ID')[col].transform(lambda s: s.fillna(s.median() if not s.dropna().empty else 0))
        df[col] = df[col].fillna(0)

    # 4. Penggabungan Koordinat Geografis (Province ID + Regency No)
    geo_data = load_geo_json(GEO_REGENCIES_JSON)
    geo_df = pd.DataFrame(geo_data)

    if not geo_df.empty:
        df = df.merge(
            geo_df[['province_id', 'regency_no', 'latitude', 'longitude']],
            left_on=['Province_ID', 'No'],
            right_on=['province_id', 'regency_no'],
            how='left'
        )

    # 5. Standardisasi Kolom & Fitur Rasio (Tabel 3.1)
    rename_map = {
        'Province_ID': 'province_id',
        'No': 'regency_no',
        'Kabupaten/Kota': 'regency_name',
        'Jumlah Koperasi': 'total_koperasi',
        'Koperasi Memiliki NIB': 'koperasi_nib',
        'Koperasi Memiliki NPWP': 'koperasi_npwp',
        'Koperasi Telah RAT (2025)': 'koperasi_rat',
        'Simpanan Pokok': 'simpanan_pokok',
        'Simpanan Wajib': 'simpanan_wajib',
        'Volume Transaksi (2026)': 'volume_transaksi',
        'Nilai Transaksi (2026)': 'nilai_transaksi'
    }
    df = df.rename(columns=rename_map).fillna(0)

    # Hitung fitur rasio (0 - 100%)
    df['rasio_nib'] = np.where(df['total_koperasi'] > 0, (df['koperasi_nib'] / df['total_koperasi']) * 100.0, 0.0).clip(0, 100).round(2)
    df['rasio_npwp'] = np.where(df['total_koperasi'] > 0, (df['koperasi_npwp'] / df['total_koperasi']) * 100.0, 0.0).clip(0, 100).round(2)
    df['rasio_rat'] = np.where(df['total_koperasi'] > 0, (df['koperasi_rat'] / df['total_koperasi']) * 100.0, 0.0).clip(0, 100).round(2)

    os.makedirs(os.path.dirname(CLEANED_REGENCIES_CSV), exist_ok=True)
    df.to_csv(CLEANED_REGENCIES_CSV, index=False)
    logger.info(f"Cleaned {len(df)} kabupaten/kota -> {CLEANED_REGENCIES_CSV}")

def main():
    logger.info("Memulai Stage Data Preparation (Cleaning & Imputation)...")
    clean_provinces_data()
    clean_regencies_data()
    logger.info("Pembersihan data selesai.")

if __name__ == "__main__":
    main()
