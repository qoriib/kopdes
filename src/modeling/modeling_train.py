import os
import json
import pickle
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from kneed import KneeLocator
from sklearn.cluster import KMeans

from utils.log_utils import get_logger
from utils.config_utils import get_params
from config import (
    SCALED_FEATURES_CSV,
    CLEANED_REGENCIES_CSV,
    MODEL_PKL,
    CLUSTERED_REGENCIES_CSV,
    FIGURES_DIR
)

logger = get_logger("modeling.train")

def find_optimal_k_and_plot(X_scaled: list, min_k: int = 2, max_k: int = 10, random_state: int = 42, n_init: int = 10, kneedle_curve: str = "convex", kneedle_direction: str = "decreasing", fallback_k: int = 3) -> int:
    """
    Menghitung WCSS/Inertia untuk rentang K secara iteratif,
    menggunakan KneeLocator untuk deteksi elbow point otomatis,
    dan menyimpan visualisasi kurva Elbow.
    """
    k_range = list(range(min_k, max_k + 1))
    inertias = []

    logger.info(f"Menghitung WCSS/Inertia untuk K dari {min_k} sampai {max_k}...")
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    kneedle = KneeLocator(
        x=k_range,
        y=inertias,
        curve=kneedle_curve,
        direction=kneedle_direction
    )

    optimal_k = kneedle.knee
    if optimal_k is None:
        logger.warning(f"KneeLocator tidak menemukan titik belok yang tegas. Menggunakan K = {fallback_k} sebagai fallback.")
        optimal_k = fallback_k
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

def run_train():
    logger.info("Menjalankan CRISP-DM: Modeling - KMeans Training & Kneedle Optimization...")

    params = get_params('modeling')
    min_k = params.get('min_k', 2)
    max_k = params.get('max_k', 10)
    random_state = params.get('random_state', 42)
    n_init = params.get('n_init', 10)
    kneedle_curve = params.get('kneedle', {}).get('curve', 'convex')
    kneedle_direction = params.get('kneedle', {}).get('direction', 'decreasing')
    fallback_k = params.get('fallback_k', 3)
    override_k = params.get('override_k', None)
    selected_features = params.get('selected_features', [])

    if not os.path.exists(SCALED_FEATURES_CSV):
        raise FileNotFoundError(f"Berkas input {SCALED_FEATURES_CSV} tidak ditemukan.")

    df_scaled = pd.read_csv(SCALED_FEATURES_CSV)

    if selected_features:
        logger.info(f"Fitur terpilih untuk pemodelan: {selected_features}")
        scaled_cols = [f"scaled_{col}" for col in selected_features if f"scaled_{col}" in df_scaled.columns]
        if not scaled_cols:
            logger.warning("Fitur terpilih tidak ditemukan di scaled data. Menggunakan seluruh fitur yang ada.")
            X_scaled = df_scaled.values
        else:
            X_scaled = df_scaled[scaled_cols].values
    else:
        logger.info("Menggunakan seluruh fitur scaled.")
        X_scaled = df_scaled.values

    # Penentuan Nilai K
    if override_k is not None:
        n_clusters = int(override_k)
        logger.info(f"Menggunakan K = {n_clusters} (OVERRIDE dari params.yaml)...")
    else:
        logger.info("Mencari K optimal menggunakan KneeLocator...")
        n_clusters = find_optimal_k_and_plot(
            X_scaled, min_k=min_k, max_k=max_k,
            random_state=random_state, n_init=n_init,
            kneedle_curve=kneedle_curve, kneedle_direction=kneedle_direction,
            fallback_k=fallback_k
        )
        logger.info(f"K Optimal Terpilih: K = {n_clusters}")

    # Melatih Model KMeans Akhir
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
    cluster_labels = kmeans.fit_predict(X_scaled)

    # Validasi Partisi
    counts = pd.Series(cluster_labels).value_counts()
    logger.info(f"Distribusi anggota klaster:\n{counts.to_dict()}")

    # Menyimpan Artefak Model PKL
    os.makedirs(os.path.dirname(MODEL_PKL), exist_ok=True)
    with open(MODEL_PKL, "wb") as f:
        pickle.dump(kmeans, f)
    logger.info(f"Trained Model PKL -> {MODEL_PKL}")

    # Penggabungan Label Klaster ke Dataset Bersih Kabupaten/Kota
    df_raw = pd.read_csv(CLEANED_REGENCIES_CSV)
    df_raw['cluster_label'] = cluster_labels
    os.makedirs(os.path.dirname(CLUSTERED_REGENCIES_CSV), exist_ok=True)
    df_raw.to_csv(CLUSTERED_REGENCIES_CSV, index=False)
    logger.info(f"Clustered Regencies Dataset -> {CLUSTERED_REGENCIES_CSV}")

def main():
    run_train()

if __name__ == "__main__":
    main()
