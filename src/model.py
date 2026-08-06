import os
import sys
import json
import joblib
import pandas as pd
from sklearn.cluster import KMeans

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TRANSFORM_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "transform")
PREPROCESS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "preprocess")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
DATA_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "model")

SCALED_FEATURES_CSV = os.path.join(PREPROCESS_DIR, "scaled_features.csv")
PREPROCESS_META_JSON = os.path.join(PREPROCESS_DIR, "preprocess_meta.json")
TRANSFORMED_REGENCIES_CSV = os.path.join(TRANSFORM_DIR, "transformed_regencies.csv")

MODEL_PKL = os.path.join(MODEL_DIR, "kmeans_model.pkl")
CLUSTERED_REGENCIES_CSV = os.path.join(DATA_MODEL_DIR, "clustered_regencies.csv")

def main():
    print("[+] Memulai Stage Modelling KMeans Clustering...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(DATA_MODEL_DIR, exist_ok=True)

    with open(PREPROCESS_META_JSON, encoding="utf-8") as f:
        meta = json.load(f)
    
    optimal_k = meta.get("optimal_k", 3)
    print(f"[*] Menggunakan K = {optimal_k} untuk KMeans Clustering...")

    X_scaled = pd.read_csv(SCALED_FEATURES_CSV).values

    # 1. Melatih Model KMeans
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)

    # 2. Menyimpan Artifact Model Trained PKL
    joblib.dump(kmeans, MODEL_PKL)
    print(f"[SAVED] Trained Model PKL -> {MODEL_PKL}")

    # 3. Penggabungan Label Klaster ke Dataset Kabupaten/Kota
    df_raw = pd.read_csv(TRANSFORMED_REGENCIES_CSV)
    df_raw['cluster_label'] = cluster_labels
    df_raw.to_csv(CLUSTERED_REGENCIES_CSV, index=False)
    print(f"[SAVED] Clustered Regencies Dataset -> {CLUSTERED_REGENCIES_CSV}")

    print("[DONE] Stage ML Modelling selesai.")

if __name__ == "__main__":
    main()
