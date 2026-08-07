import os
import sys
import json
import base64
import io
import yaml
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from kneed import KneeLocator
import matplotlib.pyplot as plt
import seaborn as sns

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Set matplotlib to run without GUI (headless)
import matplotlib
matplotlib.use('Agg')

TRANSFORM_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "transform")
PREPROCESS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "preprocess")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

INPUT_REGENCIES_CSV = os.path.join(TRANSFORM_DIR, "transformed_regencies.csv")
SCALED_FEATURES_CSV = os.path.join(PREPROCESS_DIR, "scaled_features.csv")
PREPROCESS_META_JSON = os.path.join(PREPROCESS_DIR, "preprocess_meta.json")
PREPROCESS_REPORT_MD = os.path.join(REPORTS_DIR, "preprocess_report.md")

FEATURE_COLUMNS = [
    'jumlah_koperasi', 'koperasi_nib', 'koperasi_npwp', 'koperasi_rat',
    'simpanan_pokok', 'simpanan_wajib', 'volume_transaksi', 'nilai_transaksi',
    'latitude', 'longitude'
]

FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")

PARAMS_FILE = os.path.join(os.path.dirname(__file__), "..", "params.yaml")
params = {}
if os.path.exists(PARAMS_FILE):
    try:
        with open(PARAMS_FILE, encoding='utf-8') as f:
            params = yaml.safe_load(f).get('preprocess', {})
    except Exception:
        pass

MIN_K = params.get('min_k', 2)
MAX_K = params.get('max_k', 8)
RANDOM_STATE = params.get('random_state', 42)
N_INIT = params.get('n_init', 10)
KNEEDLE_CURVE = params.get('kneedle', {}).get('curve', 'convex')
KNEEDLE_DIRECTION = params.get('kneedle', {}).get('direction', 'decreasing')
FALLBACK_K = params.get('fallback_k', 3)
PLOT_STYLE = params.get('plot_style', 'seaborn-v0_8-whitegrid')

def generate_base64_plot(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def save_plot_to_file(fig, filepath):
    """Save a matplotlib figure to a PNG file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, format='png', dpi=120, bbox_inches='tight')
    print(f"[SAVED] Plot -> {filepath}")

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
![Kurva Elbow](data:image/png;base64,{img_elbow_b64})"""
    with open(PREPROCESS_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[SAVED] Laporan Markdown Preprocessing -> {PREPROCESS_REPORT_MD}")

    print("[DONE] Stage ML Preprocessing selesai.")

if __name__ == "__main__":
    main()
