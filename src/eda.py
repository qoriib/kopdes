import os
import sys
import json
import base64
import io
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Set matplotlib to run without GUI (headless)
import matplotlib
matplotlib.use('Agg')

TRANSFORM_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "transform")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

TRANSFORMED_PROVINCES_CSV = os.path.join(TRANSFORM_DIR, "transformed_provinces.csv")
TRANSFORMED_REGENCIES_CSV = os.path.join(TRANSFORM_DIR, "transformed_regencies.csv")

METRICS_JSON = os.path.join(REPORTS_DIR, "eda_metrics.json")
EDA_SUMMARY_MD = os.path.join(REPORTS_DIR, "eda_summary.md")

FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")

PARAMS_FILE = os.path.join(os.path.dirname(__file__), "..", "params.yaml")
params = {}
if os.path.exists(PARAMS_FILE):
    try:
        with open(PARAMS_FILE, encoding='utf-8') as f:
            params = yaml.safe_load(f).get('eda', {})
    except Exception:
        pass

TOP_PROVINCES_LIMIT = params.get('top_provinces_limit', 10)
TOP_REGENCIES_LIMIT = params.get('top_regencies_limit', 5)
PLOT_DPI = params.get('plot_dpi', 120)
PLOT_STYLE = params.get('plot_style', 'seaborn-v0_8-whitegrid')

def generate_base64_plot(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=PLOT_DPI, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def save_plot_to_file(fig, filepath):
    """Save a matplotlib figure to a PNG file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, format='png', dpi=PLOT_DPI, bbox_inches='tight')
    print(f"[SAVED] Plot -> {filepath}")

def main():
    print("[+] Memulai Tahap Analisis Eksplorasi Data (EDA) yang Dikembangkan...")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    if not os.path.exists(TRANSFORMED_PROVINCES_CSV) or not os.path.exists(TRANSFORMED_REGENCIES_CSV):
        print("[-] Data transform tidak ditemukan. Silakan jalankan transform terlebih dahulu.")
        sys.exit(1)

    # Load data with Pandas
    df_prov = pd.read_csv(TRANSFORMED_PROVINCES_CSV)
    df_reg = pd.read_csv(TRANSFORMED_REGENCIES_CSV)

    # Clean data (convert numeric columns)
    num_cols_prov = [
        'jumlah_koperasi', 'koperasi_nib', 'koperasi_npwp', 'koperasi_rat',
        'simpanan_pokok', 'simpanan_wajib', 'volume_transaksi', 'nilai_transaksi'
    ]
    for col in num_cols_prov:
        if col in df_prov.columns:
            df_prov[col] = pd.to_numeric(df_prov[col], errors='coerce').fillna(0)

    num_cols_reg = [
        'jumlah_koperasi', 'koperasi_nib', 'koperasi_npwp', 'koperasi_rat',
        'simpanan_pokok', 'simpanan_wajib', 'volume_transaksi', 'nilai_transaksi'
    ]
    for col in num_cols_reg:
        if col in df_reg.columns:
            df_reg[col] = pd.to_numeric(df_reg[col], errors='coerce').fillna(0)

    # Summaries
    total_provinces = len(df_prov)
    total_regencies = len(df_reg)
    total_koperasi = int(df_prov['jumlah_koperasi'].sum())
    total_nib = int(df_prov['koperasi_nib'].sum())
    total_npwp = int(df_prov['koperasi_npwp'].sum())
    total_rat = int(df_prov['koperasi_rat'].sum())
    simpanan_pokok = float(df_prov['simpanan_pokok'].sum())
    simpanan_wajib = float(df_prov['simpanan_wajib'].sum())
    total_nilai_transaksi = float(df_prov['nilai_transaksi'].sum())

    pct_nib = round((total_nib / total_koperasi * 100), 2) if total_koperasi else 0
    pct_npwp = round((total_npwp / total_koperasi * 100), 2) if total_koperasi else 0
    pct_rat = round((total_rat / total_koperasi * 100), 2) if total_koperasi else 0

    # Top items
    top_provinces_koperasi = df_prov.sort_values(by='jumlah_koperasi', ascending=False).head(TOP_PROVINCES_LIMIT)
    top_regencies_koperasi = df_reg.sort_values(by='jumlah_koperasi', ascending=False).head(TOP_REGENCIES_LIMIT)
    top_regencies_transaksi = df_reg.sort_values(by='nilai_transaksi', ascending=False).head(TOP_REGENCIES_LIMIT)

    # Descriptive Stats
    desc_prov = df_prov[num_cols_prov].describe().T
    desc_prov.columns = ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max']
    desc_prov_markdown = desc_prov.to_markdown(floatfmt=",.2f")

    desc_reg = df_reg[num_cols_reg].describe().T
    desc_reg.columns = ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max']
    desc_reg_markdown = desc_reg.to_markdown(floatfmt=",.2f")
    sns.set_theme() # Gunakan styling default dari seaborn

    # Chart 1: Top Provinces by Total Koperasi
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    prov_sorted = df_prov.sort_values(by='jumlah_koperasi', ascending=True).tail(TOP_PROVINCES_LIMIT)
    sns.barplot(x='jumlah_koperasi', y='province_name', data=prov_sorted, ax=ax1)
    ax1.set_title(f'{TOP_PROVINCES_LIMIT} Provinsi dengan Jumlah Koperasi Terbanyak')
    ax1.set_xlabel('Jumlah Koperasi')
    ax1.set_ylabel('')
    fig1.tight_layout()
    save_plot_to_file(fig1, os.path.join(FIGURES_DIR, "eda_top_provinces.png"))
    img_prov_b64 = generate_base64_plot(fig1)

    # Chart 2: Top Regencies by Nilai Transaksi
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    reg_sorted = df_reg.sort_values(by='nilai_transaksi', ascending=True).tail(TOP_PROVINCES_LIMIT)
    sns.barplot(x=reg_sorted['nilai_transaksi'] / 1e6, y=reg_sorted['regency_name'], ax=ax2)
    ax2.set_title(f'{TOP_PROVINCES_LIMIT} Kabupaten/Kota dengan Nilai Transaksi Tertinggi (Juta Rp)')
    ax2.set_xlabel('Nilai Transaksi (Juta Rp)')
    ax2.set_ylabel('')
    fig2.tight_layout()
    save_plot_to_file(fig2, os.path.join(FIGURES_DIR, "eda_top_regencies_transaksi.png"))
    img_reg_b64 = generate_base64_plot(fig2)

    # Save metrics
    metrics = {
        "summary": {
            "total_provinces": total_provinces,
            "total_regencies": total_regencies,
            "total_koperasi": total_koperasi,
            "koperasi_memiliki_nib": total_nib,
            "pct_nib": pct_nib,
            "koperasi_memiliki_npwp": total_npwp,
            "pct_npwp": pct_npwp,
            "koperasi_telah_rat": total_rat,
            "pct_rat": pct_rat,
            "total_simpanan_pokok": simpanan_pokok,
            "total_simpanan_wajib": simpanan_wajib,
            "total_nilai_transaksi": total_nilai_transaksi
        },
        "top_province_by_koperasi": {
            "name": top_provinces_koperasi.iloc[0]['province_name'] if not top_provinces_koperasi.empty else "",
            "count": int(top_provinces_koperasi.iloc[0]['jumlah_koperasi']) if not top_provinces_koperasi.empty else 0
        },
        "top_regency_by_koperasi": {
            "name": top_regencies_koperasi.iloc[0]['regency_name'] if not top_regencies_koperasi.empty else "",
            "count": int(top_regencies_koperasi.iloc[0]['jumlah_koperasi']) if not top_regencies_koperasi.empty else 0
        }
    }

    with open(METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] DVC Metrics -> {METRICS_JSON}")

    # Generate Markdown Report
    md_content = f"""# Laporan Analisis Eksplorasi Data SIMKOPDES

Laporan ini dihasilkan secara otomatis oleh pipeline analisis data SIMKOPDES berbasis Data Version Control (DVC).

## Ringkasan Statistik Nasional

| Indikator Kinerja | Jumlah | Persentase |
| :--- | :--- | :--- |
| Jumlah Provinsi | {total_provinces} | 100% |
| Jumlah Kabupaten/Kota | {total_regencies} | 100% |
| Total Koperasi Terdaftar | {total_koperasi:,} | 100% |
| Koperasi Memiliki NIB | {total_nib:,} | {pct_nib}% |
| Koperasi Memiliki NPWP | {total_npwp:,} | {pct_npwp}% |
| Koperasi Telah Melaksanakan RAT (2025) | {total_rat:,} | {pct_rat}% |
| Total Simpanan Pokok | Rp {simpanan_pokok:,.2f} | - |
| Total Simpanan Wajib | Rp {simpanan_wajib:,.2f} | - |
| Total Nilai Transaksi | Rp {total_nilai_transaksi:,.2f} | - |

## Visualisasi Analisis Eksplorasi Data

### 1. Distribusi Koperasi di Tingkat Provinsi
<img src="data:image/png;base64,{img_prov_b64}" alt="10 Provinsi dengan Koperasi Terbanyak" width="300">

### 2. Nilai Transaksi di Tingkat Kabupaten/Kota
<img src="data:image/png;base64,{img_reg_b64}" alt="10 Kabupaten/Kota dengan Nilai Transaksi Tertinggi" width="300">

## Statistik Deskriptif Tingkat Provinsi
Laporan statistik deskriptif berikut dihitung untuk seluruh indikator di tingkat Provinsi:

{desc_prov_markdown}

## Statistik Deskriptif Tingkat Kabupaten/Kota
Laporan statistik deskriptif berikut dihitung untuk seluruh indikator di tingkat Kabupaten/Kota:

{desc_reg_markdown}

## Provinsi Teratas dengan Jumlah Koperasi Terbanyak
"""
    for idx, (_, p) in enumerate(top_provinces_koperasi.iterrows(), 1):
        md_content += f"{idx}. **{p['province_name']}**: {int(p['jumlah_koperasi']):,} Koperasi (NIB: {int(p['koperasi_nib']):,}, RAT: {int(p['koperasi_rat']):,})\n"

    md_content += "\n\n## Kabupaten/Kota Teratas dengan Jumlah Koperasi Terbanyak\n\n"
    for idx, (_, r) in enumerate(top_regencies_koperasi.iterrows(), 1):
        md_content += f"{idx}. **{r['regency_name']}**: {int(r['jumlah_koperasi']):,} Koperasi\n"

    md_content += "\n\n## Kabupaten/Kota Teratas dengan Nilai Transaksi Tertinggi\n\n"
    for idx, (_, r) in enumerate(top_regencies_transaksi.iterrows(), 1):
        md_content += f"{idx}. **{r['regency_name']}**: Rp {float(r['nilai_transaksi']):,.2f}\n"

    with open(EDA_SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[SAVED] Laporan Markdown EDA -> {EDA_SUMMARY_MD}")

    print("[DONE] Tahap EDA selesai.")

if __name__ == "__main__":
    main()
