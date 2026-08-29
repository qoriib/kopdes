import os
import sys
import json
import pickle
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import dvc.api
from kneed import KneeLocator
from sklearn.cluster import KMeans

# Ensure src root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_utils import get_logger
from config import (
    SCALED_FEATURES_CSV,
    CLEANED_REGENCIES_CSV,
    MODEL_PKL,
    CLUSTERED_REGENCIES_CSV,
    FIGURES_DIR
)

logger = get_logger("modeling.train")
params = dvc.api.params_show().get('modeling', {})

MIN_K = params.get('min_k', 2)
MAX_K = params.get('max_k', 10)
RANDOM_STATE = params.get('random_state', 42)
N_INIT = params.get('n_init', 10)
KNEEDLE_CURVE = params.get('kneedle', {}).get('curve', 'convex')
KNEEDLE_DIRECTION = params.get('kneedle', {}).get('direction', 'decreasing')
FALLBACK_K = params.get('fallback_k', 3)
OVERRIDE_K = params.get('override_k', None)
SELECTED_FEATURES = params.get('selected_features', [])

def find_optimal_k_and_plot(X_scaled: list, min_k: int = 2, max_k: int = 10) -> int:
    """
    Menghitung WCSS/Inertia untuk rentang K secara iteratif,
    menggunakan KneeLocator untuk deteksi elbow point otomatis,
    dan menyimpan visualisasi kurva Elbow.
    """
    k_range = list(range(min_k, max_k + 1))
    inertias = []

    logger.info(f"Menghitung WCSS/Inertia untuk K dari {min_k} sampai {max_k}...")
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=N_INIT)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    kneedle = KneeLocator(
        x=k_range,
        y=inertias,
        curve=KNEEDLE_CURVE,
        direction=KNEEDLE_DIRECTION
    )

    optimal_k = kneedle.knee
    if optimal_k is None:
        logger.warning(f"KneeLocator tidak menemukan titik belok yang tegas. Menggunakan K = {FALLBACK_K} sebagai fallback.")
        optimal_k = FALLBACK_K
    else:
        logger.info(f"KneeLocator mendeteksi titik belok optimal pada K = {optimal_k}")

    # Visualisasi Elbow Curve
    os.makedirs(FIGURES_DIR, exist_ok=True)
    plt.figure(figsize=(8, 4.5))
    sns.lineplot(x=k_range, y=inertias, marker='o')
    plt.axvline(x=optimal_k, color='r', linestyle='--', label=f'Titik Belok Optimal (K={optimal_k})')
    plt.title('Metode Elbow Terprogram (Kneedle) untuk Penentuan K Optimal')
    plt.xlabel('Jumlah Klaster (K)')
    plt.ylabel('Inertia / WCSS')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "model_elbow_curve.png"))
    plt.close()

    return int(optimal_k)

def main():
    logger.info("Memulai Stage Modeling KMeans Clustering (CRISP-DM Modeling)...")

    if not os.path.exists(SCALED_FEATURES_CSV):
        raise FileNotFoundError(f"Berkas input {SCALED_FEATURES_CSV} tidak ditemukan.")

    df_scaled = pd.read_csv(SCALED_FEATURES_CSV)

    # 1. Seleksi Fitur Terpilih
    if SELECTED_FEATURES:
        logger.info(f"Fitur terpilih untuk pemodelan: {SELECTED_FEATURES}")
        scaled_cols = [f"scaled_{col}" for col in SELECTED_FEATURES if f"scaled_{col}" in df_scaled.columns]
        if not scaled_cols:
            logger.warning("Fitur terpilih tidak ditemukan di scaled data. Menggunakan seluruh fitur yang ada.")
            X_scaled = df_scaled.values
        else:
            X_scaled = df_scaled[scaled_cols].values
    else:
        logger.info("Tidak ada pembatasan fitur terpilih. Menggunakan seluruh fitur scaled.")
        X_scaled = df_scaled.values

    # 2. Penentuan Nilai K (Otomatis via Kneedle atau Override dari params)
    if OVERRIDE_K is not None:
        n_clusters = int(OVERRIDE_K)
        logger.info(f"Menggunakan K = {n_clusters} (OVERRIDE dari params.yaml)...")
    else:
        logger.info("Mencari K optimal menggunakan KneeLocator pada rentang [2, 10]...")
        n_clusters = find_optimal_k_and_plot(X_scaled, min_k=MIN_K, max_k=MAX_K)
        logger.info(f"K Optimal Terpilih: K = {n_clusters}")

    # 3. Melatih Model KMeans Akhir
    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=N_INIT)
    cluster_labels = kmeans.fit_predict(X_scaled)

    # 4. Validasi Partisi Klaster (Memastikan tidak ada klaster kosong atau klaster singular)
    counts = pd.Series(cluster_labels).value_counts()
    logger.info(f"Distribusi anggota klaster:\n{counts.to_dict()}")
    if (counts == 0).any():
        logger.error("Ditemukan klaster kosong!")
    if (counts == 1).any():
        logger.warning("Ditemukan klaster dengan 1 anggota (potensial outlier singular).")

    # 5. Menyimpan Artefak Model PKL
    os.makedirs(os.path.dirname(MODEL_PKL), exist_ok=True)
    with open(MODEL_PKL, "wb") as f:
        pickle.dump(kmeans, f)
    logger.info(f"Trained Model PKL -> {MODEL_PKL}")

    # 6. Penggabungan Label Klaster ke Dataset Bersih Kabupaten/Kota
    df_raw = pd.read_csv(CLEANED_REGENCIES_CSV)
    df_raw['cluster_label'] = cluster_labels
    os.makedirs(os.path.dirname(CLUSTERED_REGENCIES_CSV), exist_ok=True)
    df_raw.to_csv(CLUSTERED_REGENCIES_CSV, index=False)
    logger.info(f"Clustered Regencies Dataset -> {CLUSTERED_REGENCIES_CSV}")

    logger.info("Stage Modeling selesai.")

if __name__ == "__main__":
    main()
