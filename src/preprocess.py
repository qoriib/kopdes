import os
import json
import pandas as pd
from sklearn.preprocessing import StandardScaler
from utils.log_utils import get_logger
from config import (
    TRANSFORMED_REGENCIES_CSV,
    SCALED_FEATURES_CSV,
    PREPROCESS_META_JSON
)

logger = get_logger("preprocess")

FEATURE_COLUMNS = [
    'jumlah_koperasi',
    'koperasi_nib',
    'koperasi_npwp',
    'koperasi_rat',
    'simpanan_pokok',
    'simpanan_wajib',
    'volume_transaksi',
    'nilai_transaksi',
    'latitude',
    'longitude'
]


def main():
    logger.info("Memulai Stage Preprocessing Data...")

    if not os.path.exists(TRANSFORMED_REGENCIES_CSV):
        raise FileNotFoundError(f"Berkas input {TRANSFORMED_REGENCIES_CSV} tidak ditemukan.")

    df = pd.read_csv(TRANSFORMED_REGENCIES_CSV)
    logger.info(f"Berhasil memuat {len(df)} baris data kabupaten/kota.")

    # 1. Seleksi & Penanganan Missing Values pada Fitur Numerik
    feature_cols_present = [col for col in FEATURE_COLUMNS if col in df.columns]
    X = df[feature_cols_present].fillna(0).values

    # 2. Standarisasi Fitur Menggunakan StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Simpan Scaled Features ke CSV (menggunakan prefix 'scaled_')
    scaled_df = pd.DataFrame(X_scaled, columns=[f"scaled_{col}" for col in feature_cols_present])
    scaled_df.to_csv(SCALED_FEATURES_CSV, index=False)
    logger.info(f"Scaled Features -> {SCALED_FEATURES_CSV}")

    # 4. Simpan Metadata Preprocessing ke JSON
    meta = {
        "total_samples": len(df),
        "total_features": len(feature_cols_present),
        "feature_columns": feature_cols_present,
        "scaler_type": "StandardScaler"
    }
    
    with open(PREPROCESS_META_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Preprocess Meta -> {PREPROCESS_META_JSON}")

    logger.info("Stage ML Preprocessing selesai.")

if __name__ == "__main__":
    main()