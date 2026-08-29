import os
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

from utils.log_utils import get_logger
from utils.config_utils import get_params
from config import (
    CLEANED_REGENCIES_CSV,
    SCALED_FEATURES_CSV,
    PREPARATION_META_JSON,
    FEATURE_COLUMNS
)

logger = get_logger("preparation.transform")

def run_transform():
    logger.info("Menjalankan CRISP-DM: Preparation - Transform Data (Log Transform & StandardScaler)...")

    prep_params = get_params('preparation')
    log_features = prep_params.get('log_transform_features', [
        'total_koperasi',
        'simpanan_pokok',
        'simpanan_wajib',
        'volume_transaksi',
        'nilai_transaksi'
    ])

    if not os.path.exists(CLEANED_REGENCIES_CSV):
        raise FileNotFoundError(f"Berkas input {CLEANED_REGENCIES_CSV} tidak ditemukan.")

    df = pd.read_csv(CLEANED_REGENCIES_CSV)
    logger.info(f"Memuat {len(df)} baris data kabupaten/kota bersih.")

    feature_cols_present = [col for col in FEATURE_COLUMNS if col in df.columns]
    X_df = df[feature_cols_present].copy().fillna(0)

    # 1. Transformasi Logaritmik Natural ln(1 + x)
    for col in log_features:
        if col in X_df.columns:
            logger.info(f"Menerapkan Transformasi Log Natural (log1p) pada: {col}")
            X_df[col] = np.log1p(np.maximum(X_df[col].values, 0))

    # 2. Standarisasi Z-Score (StandardScaler)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_df.values)

    # 3. Simpan Scaled Features CSV
    scaled_df = pd.DataFrame(X_scaled, columns=[f"scaled_{col}" for col in feature_cols_present])
    os.makedirs(os.path.dirname(SCALED_FEATURES_CSV), exist_ok=True)
    scaled_df.to_csv(SCALED_FEATURES_CSV, index=False)
    logger.info(f"Scaled Features -> {SCALED_FEATURES_CSV}")

    # 4. Simpan Metadata Preparation JSON
    meta = {
        "total_samples": len(df),
        "total_features": len(feature_cols_present),
        "feature_columns": feature_cols_present,
        "log_transformed_features": [c for c in log_features if c in feature_cols_present],
        "scaler_type": "StandardScaler (Z-Score Normalization)"
    }

    with open(PREPARATION_META_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info(f"Preparation Metadata -> {PREPARATION_META_JSON}")

def main():
    run_transform()

if __name__ == "__main__":
    main()
