import os
import sys
import json
import dvc.api
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Ensure src root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_utils import get_logger
from config import (
    CLEANED_REGENCIES_CSV,
    SCALED_FEATURES_CSV,
    PREPARATION_META_JSON
)

logger = get_logger("data_preparation.transform")

prep_params = dvc.api.params_show().get('data_preparation', {})
LOG_TRANSFORM_FEATURES = prep_params.get('log_transform_features', [
    'total_koperasi',
    'simpanan_pokok',
    'simpanan_wajib',
    'volume_transaksi',
    'nilai_transaksi'
])

FEATURE_COLUMNS = [
    'total_koperasi',
    'rasio_nib',
    'rasio_npwp',
    'rasio_rat',
    'simpanan_pokok',
    'simpanan_wajib',
    'volume_transaksi',
    'nilai_transaksi'
]

def main():
    logger.info("Memulai Stage Data Preparation (Transformasi Logaritmik & Normalisasi Z-Score)...")

    if not os.path.exists(CLEANED_REGENCIES_CSV):
        raise FileNotFoundError(f"Berkas input {CLEANED_REGENCIES_CSV} tidak ditemukan.")

    df = pd.read_csv(CLEANED_REGENCIES_CSV)
    logger.info(f"Berhasil memuat {len(df)} baris data kabupaten/kota bersih.")

    # 1. Seleksi Fitur Numerik
    feature_cols_present = [col for col in FEATURE_COLUMNS if col in df.columns]
    X_df = df[feature_cols_present].copy().fillna(0)

    # 2. Transformasi Logaritmik Natural ln(1 + x) pada Fitur Finansial/Ekstrem Skewed
    for col in LOG_TRANSFORM_FEATURES:
        if col in X_df.columns:
            logger.info(f"Menerapkan Transformasi Natural Log (log1p) pada fitur: {col}")
            X_df[col] = np.log1p(np.maximum(X_df[col].values, 0))

    # 3. Standarisasi Fitur Menggunakan Z-Score (StandardScaler)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_df.values)

    # 4. Simpan Scaled Features ke CSV (menggunakan prefix 'scaled_')
    scaled_df = pd.DataFrame(X_scaled, columns=[f"scaled_{col}" for col in feature_cols_present])
    os.makedirs(os.path.dirname(SCALED_FEATURES_CSV), exist_ok=True)
    scaled_df.to_csv(SCALED_FEATURES_CSV, index=False)
    logger.info(f"Scaled Features -> {SCALED_FEATURES_CSV}")

    # 5. Simpan Metadata Preprocessing ke JSON
    meta = {
        "total_samples": len(df),
        "total_features": len(feature_cols_present),
        "feature_columns": feature_cols_present,
        "log_transformed_features": [c for c in LOG_TRANSFORM_FEATURES if c in feature_cols_present],
        "scaler_type": "StandardScaler (Z-Score Normalization)"
    }

    with open(PREPARATION_META_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info(f"Preparation Metadata -> {PREPARATION_META_JSON}")
    logger.info("Transformasi data selesai.")

if __name__ == "__main__":
    main()
