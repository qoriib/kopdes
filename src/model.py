import os
import sys
import json
import yaml
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

PARAMS_FILE = os.path.join(os.path.dirname(__file__), "..", "params.yaml")
params = {}
if os.path.exists(PARAMS_FILE):
    try:
        with open(PARAMS_FILE, encoding='utf-8') as f:
            params = yaml.safe_load(f).get('model', {})
    except Exception:
        pass

RANDOM_STATE = params.get('random_state', 42)
N_INIT = params.get('n_init', 10)
OVERRIDE_K = params.get('override_k', None)

def main():
    print("[+] Memulai Stage Modelling KMeans Clustering...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(DATA_MODEL_DIR, exist_ok=True)

    with open(PREPROCESS_META_JSON, encoding="utf-8") as f:
        meta = json.load(f)
    
    # 1. Menentukan K (baik dari optimal_k hasil preprocess atau override_k dari params)
    if OVERRIDE_K is not None:
        n_clusters = int(OVERRIDE_K)
        print(f"[*] Menggunakan K = {n_clusters} (OVERRIDE dari params.yaml) untuk KMeans Clustering...")
    else:
        n_clusters = meta.get("optimal_k", 3)
        print(f"[*] Menggunakan K = {n_clusters} (Optimal K hasil deteksi) untuk KMeans Clustering...")

    X_scaled = pd.read_csv(SCALED_FEATURES_CSV).values

    # 2. Melatih Model KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=N_INIT)
    cluster_labels = kmeans.fit_predict(X_scaled)

    # 3. Menyimpan Artifact Model Trained PKL
    joblib.dump(kmeans, MODEL_PKL)
    print(f"[SAVED] Trained Model PKL -> {MODEL_PKL}")

    # 4. Penggabungan Label Klaster ke Dataset Kabupaten/Kota
    df_raw = pd.read_csv(TRANSFORMED_REGENCIES_CSV)
    df_raw['cluster_label'] = cluster_labels
    df_raw.to_csv(CLUSTERED_REGENCIES_CSV, index=False)
    print(f"[SAVED] Clustered Regencies Dataset -> {CLUSTERED_REGENCIES_CSV}")

    print("[DONE] Stage ML Modelling selesai.")

if __name__ == "__main__":
    main()
