import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from kneed import KneeLocator
import matplotlib.pyplot as plt
import seaborn as sns

from config import (
    TRANSFORMED_REGENCIES_CSV,
    SCALED_FEATURES_CSV,
    PREPROCESS_META_JSON,
    PREPROCESS_REPORT_MD,
    PREPROCESS_DIR,
    REPORTS_DIR,
    FIGURES_DIR,
    get_params
)
from utils.plot_utils import generate_base64_plot, save_plot_to_file

INPUT_REGENCIES_CSV = TRANSFORMED_REGENCIES_CSV

FEATURE_COLUMNS = [
    'jumlah_koperasi', 'koperasi_nib', 'koperasi_npwp', 'koperasi_rat',
    'simpanan_pokok', 'simpanan_wajib', 'volume_transaksi', 'nilai_transaksi',
    'latitude', 'longitude'
]

params = get_params('preprocess')

MIN_K = params.get('min_k', 2)
MAX_K = params.get('max_k', 8)
RANDOM_STATE = params.get('random_state', 42)
N_INIT = params.get('n_init', 10)
KNEEDLE_CURVE = params.get('kneedle', {}).get('curve', 'convex')
KNEEDLE_DIRECTION = params.get('kneedle', {}).get('direction', 'decreasing')
FALLBACK_K = params.get('fallback_k', 3)
PLOT_STYLE = params.get('plot_style', 'seaborn-v0_8-whitegrid')

def find_optimal_k_and_plot(X_scaled, min_k=2, max_k=8):
    k_range = list(range(min_k, max_k + 1))
    inertias = []
    
    print(f"[*] Menghitung inertia untuk K dari {min_k} sampai {max_k}...")
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
        print(f"[*] KneeLocator tidak mendeteksi elbow point. Menggunakan K = {FALLBACK_K} sebagai fallback.")
        optimal_k = FALLBACK_K
    else:
        print(f"[*] KneeLocator mendeteksi elbow point pada K = {optimal_k}")

    # Generate Elbow Curve plot using standard seaborn lineplot
    sns.set_theme()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.lineplot(x=list(k_range), y=inertias, marker='o', ax=ax)
    ax.set_title('Metode Elbow untuk Penentuan K Optimal')
    ax.set_xlabel('Jumlah Klaster (K)')
    ax.set_ylabel('Inertia / WCSS')
    fig.tight_layout()
    save_plot_to_file(fig, os.path.join(FIGURES_DIR, "preprocess_elbow_curve.png"))
    img_elbow_b64 = generate_base64_plot(fig)

    return int(optimal_k), k_range, inertias, img_elbow_b64

def main():
    print("[+] Memulai Stage Preprocessing Machine Learning...")
    os.makedirs(PREPROCESS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    if not os.path.exists(INPUT_REGENCIES_CSV):
        raise FileNotFoundError(f"Berkas input {INPUT_REGENCIES_CSV} tidak ditemukan.")

    df = pd.read_csv(INPUT_REGENCIES_CSV)
    print(f"[*] Berhasil memuat {len(df)} baris data kabupaten/kota.")

    # 1. Seleksi Fitur Numerik
    X = df[FEATURE_COLUMNS].fillna(0).values

    # 2. Standarisasi Fitur (StandardScaler)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Penentuan K Terbaik Menggunakan KneeLocator
    print("[*] Menentukan nilai K terbaik dengan KneeLocator...")
    optimal_k, k_range, inertias, img_elbow_b64 = find_optimal_k_and_plot(X_scaled, min_k=MIN_K, max_k=MAX_K)
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

    # 6. Generate Preprocess & K Selection Markdown Report
    md_content = f"""# Laporan Preprocessing & Penentuan K Optimal SIMKOPDES

Laporan ini menyajikan hasil standarisasi fitur dan pencarian nilai klaster optimal (K) menggunakan metode Elbow.

## 1. Parameter Penentuan K Optimal (Kneedle Algorithm)

- **K Terbaik Terdeteksi**: **K = {optimal_k}**
- **Metode Pendeteksian**: KneeLocator (`kneed`)
- **Jenis Standarisasi**: StandardScaler

## 2. Nilai WCSS (Within-Cluster Sum of Squares)

| Nilai K | Nilai Inertia (WCSS) |
| :---: | :---: |
"""
    for k, inertia in zip(k_range, inertias):
        md_content += f"| **K = {k}** | {inertia:,.2f} |\n"

    md_content += f"""

## 3. Kurva Elbow Visualisasi
<img src="data:image/png;base64,{img_elbow_b64}" alt="Kurva Elbow" width="300">"""
    with open(PREPROCESS_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[SAVED] Laporan Markdown Preprocessing -> {PREPROCESS_REPORT_MD}")

    print("[DONE] Stage ML Preprocessing selesai.")

if __name__ == "__main__":
    main()
