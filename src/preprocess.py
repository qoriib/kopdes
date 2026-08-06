import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from yellowbrick.cluster import KElbowVisualizer

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

TRANSFORM_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "transform")
PREPROCESS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "preprocess")

INPUT_REGENCIES_CSV = os.path.join(TRANSFORM_DIR, "transformed_regencies.csv")
SCALED_FEATURES_CSV = os.path.join(PREPROCESS_DIR, "scaled_features.csv")
PREPROCESS_META_JSON = os.path.join(PREPROCESS_DIR, "preprocess_meta.json")

FEATURE_COLUMNS = [
    'jumlah_koperasi', 'koperasi_nib', 'koperasi_npwp', 'koperasi_rat',
    'simpanan_pokok', 'simpanan_wajib', 'volume_transaksi', 'nilai_transaksi',
    'latitude', 'longitude'
]

class YellowbrickKMeans(KMeans):
    @property
    def _estimator_type(self):
        return 'clusterer'

def find_optimal_k(X_scaled, min_k=2, max_k=8):
    k_range = list(range(min_k, max_k + 1))
    
    # 1. KElbowVisualizer via YellowbrickKMeans
    try:
        model = YellowbrickKMeans(random_state=42, n_init=10)
        visualizer = KElbowVisualizer(model, k=(min_k, max_k), timings=False)
        visualizer.fit(X_scaled)
        if visualizer.elbow_value_ is not None and visualizer.elbow_value_ > 0:
            print(f"[*] KElbowVisualizer menentukan optimal K = {visualizer.elbow_value_}")
            return int(visualizer.elbow_value_)
    except Exception as e:
        print(f"[*] Fallback kalkulasi Elbow: {e}")

    # 2. Geometric Chord Distance Fallback
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    p1 = np.array([k_range[0], inertias[0]])
    p2 = np.array([k_range[-1], inertias[-1]])
    distances = []
    for i, k in enumerate(k_range):
        p0 = np.array([k, inertias[i]])
        # Distance formula in 2D plane: |(y2-y1)x0 - (x2-x1)y0 + x2*y1 - y2*x1| / sqrt((y2-y1)^2 + (x2-x1)^2)
        dist = abs((p2[1] - p1[1]) * p0[0] - (p2[0] - p1[0]) * p0[1] + p2[0] * p1[1] - p2[1] * p1[0]) / np.sqrt((p2[1] - p1[1])**2 + (p2[0] - p1[0])**2)
        distances.append(dist)
    
    return int(k_range[np.argmax(distances)])

def main():
    print("[+] Memulai Stage Preprocessing Machine Learning...")
    os.makedirs(PREPROCESS_DIR, exist_ok=True)

    if not os.path.exists(INPUT_REGENCIES_CSV):
        raise FileNotFoundError(f"Berkas input {INPUT_REGENCIES_CSV} tidak ditemukan.")

    df = pd.read_csv(INPUT_REGENCIES_CSV)
    print(f"[*] Berhasil memuat {len(df)} baris data kabupaten/kota.")

    # 1. Seleksi Fitur Numerik
    X = df[FEATURE_COLUMNS].fillna(0).values

    # 2. Standarisasi Fitur (StandardScaler)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Penentuan K Terbaik Menggunakan KElbowVisualizer
    print("[*] Menentukan nilai K terbaik dengan KElbowVisualizer...")
    optimal_k = find_optimal_k(X_scaled, min_k=2, max_k=8)
    print(f"[OK] K Terbaik yang terdeteksi: K = {optimal_k}")

    # 4. Simpan Scaled Features ke CSV
    scaled_df = pd.DataFrame(X_scaled, columns=[f"scaled_{col}" for col in FEATURE_COLUMNS])
    scaled_df.to_csv(SCALED_FEATURES_CSV, index=False)
    print(f"[SAVED] Scaled Features -> {SCALED_FEATURES_CSV}")

    # 5. Simpan Meta Config & Optimal K ke JSON
    meta = {
        "total_samples": len(df),
        "feature_columns": FEATURE_COLUMNS,
        "optimal_k": optimal_k,
        "scaler_type": "StandardScaler"
    }
    with open(PREPROCESS_META_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] Preprocess Meta -> {PREPROCESS_META_JSON}")

    print("[DONE] Stage ML Preprocessing selesai.")

if __name__ == "__main__":
    main()
