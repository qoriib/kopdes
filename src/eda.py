import os
import sys
import json
import dvc.api
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils.plot_utils import save_plot_to_file
from utils.log_utils import get_logger
from utils.report_utils import generate_report_from_template
from config import (
    TRANSFORMED_PROVINCES_CSV,
    TRANSFORMED_REGENCIES_CSV,
    METRICS_JSON,
    EDA_SUMMARY_MD,
    EDA_SUMMARY_TEMPLATE_MD,
    REPORTS_DIR,
    FIGURES_DIR
)

logger = get_logger("eda")
params = dvc.api.params_show().get('eda', {})

TOP_PROVINCES_LIMIT = params.get('top_provinces_limit', 10)
TOP_REGENCIES_LIMIT = params.get('top_regencies_limit', 5)
NUM_COLS_PROV = [
    'jumlah_koperasi',
    'koperasi_nib',
    'koperasi_npwp',
    'koperasi_rat',
    'simpanan_pokok',
    'simpanan_wajib',
    'volume_transaksi',
    'nilai_transaksi'
]
NUM_COLS_REG = [
    'jumlah_koperasi',
    'koperasi_nib',
    'koperasi_npwp',
    'koperasi_rat',
    'simpanan_pokok',
    'simpanan_wajib',
    'volume_transaksi',
    'nilai_transaksi'
]

def main():
    logger.info("Memulai Tahap Analisis Eksplorasi Data (EDA) yang Dikembangkan...")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    if not os.path.exists(TRANSFORMED_PROVINCES_CSV) or not os.path.exists(TRANSFORMED_REGENCIES_CSV):
        logger.error("Data transform tidak ditemukan. Silakan jalankan transform terlebih dahulu.")
        sys.exit(1)

    # Load data with Pandas
    df_prov = pd.read_csv(TRANSFORMED_PROVINCES_CSV)
    df_reg = pd.read_csv(TRANSFORMED_REGENCIES_CSV)

    # Clean data
    for col in NUM_COLS_PROV:
        if col in df_prov.columns:
            df_prov[col] = pd.to_numeric(df_prov[col], errors='coerce').fillna(0)

    for col in NUM_COLS_REG:
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
    desc_prov = df_prov[NUM_COLS_PROV].describe().T
    desc_prov.columns = ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max']
    desc_prov_markdown = desc_prov.to_markdown(floatfmt=",.2f")

    desc_reg = df_reg[NUM_COLS_REG].describe().T
    desc_reg.columns = ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max']
    desc_reg_markdown = desc_reg.to_markdown(floatfmt=",.2f")

    # Chart 1: Top Provinces by Total Koperasi
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    prov_sorted = df_prov.sort_values(by='jumlah_koperasi', ascending=True).tail(TOP_PROVINCES_LIMIT)
    sns.barplot(x='jumlah_koperasi', y='province_name', data=prov_sorted, ax=ax1)
    ax1.set_title(f'{TOP_PROVINCES_LIMIT} Provinsi dengan Jumlah Koperasi Terbanyak')
    ax1.set_xlabel('Jumlah Koperasi')
    ax1.set_ylabel('')
    fig1.tight_layout()
    save_plot_to_file(fig1, os.path.join(FIGURES_DIR, "eda_top_provinces.png"))

    # Chart 2: Top Regencies by Nilai Transaksi
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    reg_sorted = df_reg.sort_values(by='nilai_transaksi', ascending=True).tail(TOP_PROVINCES_LIMIT)
    sns.barplot(x=reg_sorted['nilai_transaksi'] / 1e6, y=reg_sorted['regency_name'], ax=ax2)
    ax2.set_title(f'{TOP_PROVINCES_LIMIT} Kabupaten/Kota dengan Nilai Transaksi Tertinggi (Juta Rp)')
    ax2.set_xlabel('Nilai Transaksi (Juta Rp)')
    ax2.set_ylabel('')
    fig2.tight_layout()
    save_plot_to_file(fig2, os.path.join(FIGURES_DIR, "eda_top_regencies_transaksi.png"))

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
    logger.info(f"DVC Metrics -> {METRICS_JSON}")

    top_provinces_list = ""
    for idx, (_, p) in enumerate(top_provinces_koperasi.iterrows(), 1):
        top_provinces_list += f"{idx}. **{p['province_name']}**: {int(p['jumlah_koperasi']):,} Koperasi (NIB: {int(p['koperasi_nib']):,}, RAT: {int(p['koperasi_rat']):,})\n"

    top_regencies_koperasi_list = ""
    for idx, (_, r) in enumerate(top_regencies_koperasi.iterrows(), 1):
        top_regencies_koperasi_list += f"{idx}. **{r['regency_name']}**: {int(r['jumlah_koperasi']):,} Koperasi\n"

    top_regencies_transaksi_list = ""
    for idx, (_, r) in enumerate(top_regencies_transaksi.iterrows(), 1):
        top_regencies_transaksi_list += f"{idx}. **{r['regency_name']}**: Rp {float(r['nilai_transaksi']):,.2f}\n"

    replacements = {
        "{{total_provinces}}": str(total_provinces),
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
        "{{desc_prov_markdown}}": desc_prov_markdown,
        "{{desc_reg_markdown}}": desc_reg_markdown,
        "{{top_provinces_list}}": top_provinces_list,
        "{{top_regencies_koperasi_list}}": top_regencies_koperasi_list,
        "{{top_regencies_transaksi_list}}": top_regencies_transaksi_list,
    }
    
    generate_report_from_template(EDA_SUMMARY_TEMPLATE_MD, EDA_SUMMARY_MD, replacements)

    logger.info("Tahap EDA selesai.")

if __name__ == "__main__":
    main()
