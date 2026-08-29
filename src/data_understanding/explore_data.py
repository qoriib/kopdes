import os
import sys
import json
import dvc.api
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Ensure src root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.log_utils import get_logger
from utils.report_utils import generate_report_from_template
from config import (
    RAW_PROVINCES_CSV,
    RAW_REGENCIES_CSV,
    DATA_EXPLORATION_REPORT_MD,
    EDA_SUMMARY_TEMPLATE_MD,
    EDA_METRICS_JSON,
    FIGURES_DIR
)

logger = get_logger("data_understanding.explore_data")
params = dvc.api.params_show().get('data_understanding', {})

TOP_PROVINCES_LIMIT = params.get('top_provinces_limit', 10)
TOP_REGENCIES_LIMIT = params.get('top_regencies_limit', 10)

def clean_numeric_col(series: pd.Series) -> pd.Series:
    """Membersihkan format angka/mata uang ke nilai numerik float."""
    return (
        series.astype(str)
        .str.replace(r'[Rp%\s]', '', regex=True)
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .pipe(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

def main():
    logger.info("Memulai Tugas Generik 3: Explore Data (EDA & Correlation Analysis)...")

    if not os.path.exists(RAW_PROVINCES_CSV) or not os.path.exists(RAW_REGENCIES_CSV):
        raise FileNotFoundError("Data mentah provinsi atau kabupaten/kota tidak ditemukan.")

    df_prov = pd.read_csv(RAW_PROVINCES_CSV)
    df_reg = pd.read_csv(RAW_REGENCIES_CSV)

    # Standardize column naming
    prov_map = {
        'Provinsi': 'province_name',
        'Jumlah Koperasi': 'total_koperasi',
        'Koperasi Memiliki NIB': 'koperasi_nib',
        'Koperasi Memiliki NPWP': 'koperasi_npwp',
        'Koperasi Telah RAT (2025)': 'koperasi_rat',
        'Simpanan Pokok': 'simpanan_pokok',
        'Simpanan Wajib': 'simpanan_wajib',
        'Volume Transaksi (2026)': 'volume_transaksi',
        'Nilai Transaksi (2026)': 'nilai_transaksi'
    }
    reg_map = {
        'Province_ID': 'province_id',
        'No': 'regency_no',
        'Kabupaten/Kota': 'regency_name',
        'Jumlah Koperasi': 'total_koperasi',
        'Koperasi Memiliki NIB': 'koperasi_nib',
        'Koperasi Memiliki NPWP': 'koperasi_npwp',
        'Koperasi Telah RAT (2025)': 'koperasi_rat',
        'Simpanan Pokok': 'simpanan_pokok',
        'Simpanan Wajib': 'simpanan_wajib',
        'Volume Transaksi (2026)': 'volume_transaksi',
        'Nilai Transaksi (2026)': 'nilai_transaksi'
    }
    df_prov = df_prov.rename(columns=prov_map)
    df_reg = df_reg.rename(columns=reg_map)

    num_cols = ['total_koperasi', 'koperasi_nib', 'koperasi_npwp', 'koperasi_rat', 'simpanan_pokok', 'simpanan_wajib', 'volume_transaksi', 'nilai_transaksi']

    for col in num_cols:
        if col in df_prov.columns:
            df_prov[col] = clean_numeric_col(df_prov[col])
        if col in df_reg.columns:
            df_reg[col] = clean_numeric_col(df_reg[col])

    # 1. Agregat Nasional
    total_regencies = len(df_reg)
    total_provinces = len(df_prov)
    total_koperasi = int(df_prov['total_koperasi'].sum())
    total_nib = int(df_prov['koperasi_nib'].sum())
    total_npwp = int(df_prov['koperasi_npwp'].sum())
    total_rat = int(df_prov['koperasi_rat'].sum())
    simpanan_pokok = float(df_prov['simpanan_pokok'].sum())
    simpanan_wajib = float(df_prov['simpanan_wajib'].sum())
    total_nilai_transaksi = float(df_prov['nilai_transaksi'].sum())

    pct_nib = round((total_nib / total_koperasi * 100), 2) if total_koperasi else 0
    pct_npwp = round((total_npwp / total_koperasi * 100), 2) if total_koperasi else 0
    pct_rat = round((total_rat / total_koperasi * 100), 2) if total_koperasi else 0

    # 2. Visualisasi EDA
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # Plot 1: Correlation Matrix Heatmap
    corr_matrix = df_reg[num_cols].corr().round(2)
    plt.figure(figsize=(8.5, 7))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5, cbar_kws={'label': 'Pearson Correlation'})
    plt.title('Matriks Korelasi Pearson Antar-Indikator KDMP (Kabupaten/Kota)')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "eda_correlation_matrix.png"))
    plt.close()

    # Plot 2: Top Provinces by Total Koperasi
    top_provinces_koperasi = df_prov.sort_values(by='total_koperasi', ascending=False).head(TOP_PROVINCES_LIMIT)
    plt.figure(figsize=(10, 5))
    prov_sorted = df_prov.sort_values(by='total_koperasi', ascending=True).tail(TOP_PROVINCES_LIMIT)
    sns.barplot(x='total_koperasi', y='province_name', data=prov_sorted, palette='Blues_r')
    plt.title(f'{TOP_PROVINCES_LIMIT} Provinsi dengan Jumlah Koperasi Terbanyak di Indonesia')
    plt.xlabel('Jumlah Koperasi')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "eda_top_provinces.png"))
    plt.close()

    # Plot 3: Top Regencies by Nilai Transaksi
    top_regencies_transaksi = df_reg.sort_values(by='nilai_transaksi', ascending=False).head(TOP_REGENCIES_LIMIT)
    plt.figure(figsize=(10, 5))
    reg_sorted = df_reg.sort_values(by='nilai_transaksi', ascending=True).tail(TOP_REGENCIES_LIMIT)
    sns.barplot(x=reg_sorted['nilai_transaksi'] / 1e6, y=reg_sorted['regency_name'], palette='viridis')
    plt.title(f'{TOP_REGENCIES_LIMIT} Kabupaten/Kota dengan Nilai Transaksi Tertinggi (Juta Rp)')
    plt.xlabel('Nilai Transaksi (Juta Rp)')
    plt.ylabel('')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "eda_top_regencies_transaksi.png"))
    plt.close()

    # Plot 4: Feature Distributions (Subplots)
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    sns.histplot(df_reg['total_koperasi'], kde=True, ax=axes[0, 0], color='skyblue')
    axes[0, 0].set_title('Distribusi Total Koperasi')
    sns.histplot(np.log1p(df_reg['simpanan_wajib']), kde=True, ax=axes[0, 1], color='salmon')
    axes[0, 1].set_title('Distribusi Log Simpanan Wajib')
    sns.histplot(np.log1p(df_reg['volume_transaksi']), kde=True, ax=axes[1, 0], color='lightgreen')
    axes[1, 0].set_title('Distribusi Log Volume Transaksi')
    sns.histplot(np.log1p(df_reg['nilai_transaksi']), kde=True, ax=axes[1, 1], color='plum')
    axes[1, 1].set_title('Distribusi Log Nilai Transaksi')
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURES_DIR, "eda_feature_distributions.png"))
    plt.close()

    # 3. Simpan DVC Metrics JSON
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
        "correlations": {
            "simpanan_wajib_vs_nilai_transaksi": float(corr_matrix.loc['simpanan_wajib', 'nilai_transaksi']),
            "volume_vs_nilai_transaksi": float(corr_matrix.loc['volume_transaksi', 'nilai_transaksi']),
            "total_koperasi_vs_nib": float(corr_matrix.loc['total_koperasi', 'koperasi_nib'])
        }
    }

    with open(EDA_METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"EDA Metrics -> {EDA_METRICS_JSON}")

    # 4. Bangun Laporan Eksplorasi Data Markdown
    top_provinces_list = ""
    for idx, (_, p) in enumerate(top_provinces_koperasi.iterrows(), 1):
        top_provinces_list += f"{idx}. **{p['province_name']}**: {int(p['total_koperasi']):,} Koperasi (NIB: {int(p['koperasi_nib']):,}, RAT: {int(p['koperasi_rat']):,})\n"

    top_regencies_transaksi_list = ""
    for idx, (_, r) in enumerate(top_regencies_transaksi.iterrows(), 1):
        top_regencies_transaksi_list += f"{idx}. **{r['regency_name']}**: Rp {float(r['nilai_transaksi']):,.2f}\n"

    replacements = {
        "{{total_regencies}}": str(total_regencies),
        "{{total_koperasi}}": f"{total_koperasi:,}",
        "{{total_nib}}": f"{total_nib:,}",
        "{{pct_nib}}": str(pct_nib),
        "{{total_npwp}}": f"{total_npwp:,}",
        "{{pct_npwp}}": str(pct_npwp),
        "{{total_rat}}": f"{total_rat:,}",
        "{{pct_rat}}": str(pct_rat),
        "{{simpanan_pokok}}": f"{simpanan_pokok:,.2f}",
        "{{simpanan_wajib}}": f"{simpanan_wajib:,.2f}",
        "{{total_nilai_transaksi}}": f"{total_nilai_transaksi:,.2f}",
        "{{top_provinces_list}}": top_provinces_list,
        "{{top_regencies_transaksi_list}}": top_regencies_transaksi_list,
    }

    # Generate to DATA_EXPLORATION_REPORT_MD
    template_path = os.path.join(os.path.dirname(EDA_SUMMARY_TEMPLATE_MD), "data_exploration_template.md")
    generate_report_from_template(template_path, DATA_EXPLORATION_REPORT_MD, replacements)
    logger.info(f"Data Exploration Report -> {DATA_EXPLORATION_REPORT_MD}")

if __name__ == "__main__":
    main()
