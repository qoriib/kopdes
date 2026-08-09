import os
import json
import pickle
import pandas as pd
import dvc.api
from sklearn.cluster import KMeans
from utils.log_utils import get_logger
from config import (
    SCALED_FEATURES_CSV,
    PREPROCESS_META_JSON,
    TRANSFORMED_REGENCIES_CSV,
    MODEL_PKL,
    CLUSTERED_REGENCIES_CSV,
    MODEL_DIR,
    DATA_MODEL_DIR
)

logger = get_logger("model")
params = dvc.api.params_show().get('model', {})

RANDOM_STATE = params.get('random_state', 42)
N_INIT = params.get('n_init', 10)
OVERRIDE_K = params.get('override_k', None)

def main():
    logger.info("Memulai Stage Modelling KMeans Clustering...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(DATA_MODEL_DIR, exist_ok=True)

    with open(PREPROCESS_META_JSON, encoding="utf-8") as f:
        meta = json.load(f)
    
    # 1. Menentukan K (baik dari optimal_k hasil preprocess atau override_k dari params)
    if OVERRIDE_K is not None:
        n_clusters = int(OVERRIDE_K)
        logger.info(f"Menggunakan K = {n_clusters} (OVERRIDE dari params.yaml) untuk KMeans Clustering...")
    else:
        n_clusters = meta.get("optimal_k", 3)
    df_scaled = pd.read_csv(SCALED_FEATURES_CSV)

    # 1.5. Seleksi Fitur Terpilih
    selected_features = params.get('selected_features', [])
    if selected_features:
        logger.info(f"Fitur terpilih untuk modelling: {selected_features}")
        scaled_cols = [f"scaled_{col}" for col in selected_features if f"scaled_{col}" in df_scaled.columns]
        if not scaled_cols:
            logger.warning("Fitur terpilih tidak valid. Menggunakan seluruh fitur yang tersedia.")
            X_scaled = df_scaled.values
        else:
            X_scaled = df_scaled[scaled_cols].values
    else:
        logger.info("Tidak ada spesifikasi fitur terpilih. Menggunakan seluruh fitur yang tersedia.")
        X_scaled = df_scaled.values

    # 2. Melatih Model KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=N_INIT)
    cluster_labels = kmeans.fit_predict(X_scaled)

    # 3. Menyimpan Artifact Model Trained PKL
    with open(MODEL_PKL, "wb") as f:
        pickle.dump(kmeans, f)
    logger.info(f"Trained Model PKL -> {MODEL_PKL}")

    # 4. Penggabungan Label Klaster ke Dataset Kabupaten/Kota
    df_raw = pd.read_csv(TRANSFORMED_REGENCIES_CSV)
    df_raw['cluster_label'] = cluster_labels
    df_raw.to_csv(CLUSTERED_REGENCIES_CSV, index=False)
    logger.info(f"Clustered Regencies Dataset -> {CLUSTERED_REGENCIES_CSV}")

    logger.info("Stage ML Modelling selesai.")

if __name__ == "__main__":
    main()
