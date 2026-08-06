import os
import sys
import csv
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

CLEANED_PROVINCES_CSV = os.path.join(PROCESSED_DIR, "cleaned_provinces.csv")
CLEANED_REGENCIES_CSV = os.path.join(PROCESSED_DIR, "cleaned_regencies.csv")

METRICS_JSON = os.path.join(REPORTS_DIR, "metrics.json")
EDA_SUMMARY_MD = os.path.join(REPORTS_DIR, "eda_summary.md")

def read_csv_data(filepath):
    rows = []
    if os.path.exists(filepath):
        with open(filepath, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Convert numbers to numeric
                for k, v in r.items():
                    try:
                        r[k] = float(v) if '.' in str(v) else int(v)
                    except ValueError:
                        pass
                rows.append(r)
    return rows

def main():
    print("[+] Memulai Stage EDA (Exploratory Data Analysis)...")
    os.makedirs(REPORTS_DIR, exist_ok=True)

    prov_data = read_csv_data(CLEANED_PROVINCES_CSV)
    reg_data = read_csv_data(CLEANED_REGENCIES_CSV)

    total_provinces = len(prov_data)
    total_regencies = len(reg_data)

    total_koperasi = sum(r.get('jumlah_koperasi', 0) for r in prov_data)
    total_nib = sum(r.get('koperasi_nib', 0) for r in prov_data)
    total_npwp = sum(r.get('koperasi_npwp', 0) for r in prov_data)
    total_rat = sum(r.get('koperasi_rat', 0) for r in prov_data)

    simpanan_pokok = sum(r.get('simpanan_pokok', 0) for r in prov_data)
    simpanan_wajib = sum(r.get('simpanan_wajib', 0) for r in prov_data)
    total_nilai_transaksi = sum(r.get('nilai_transaksi', 0) for r in prov_data)

    pct_nib = round((total_nib / total_koperasi * 100), 2) if total_koperasi else 0
    pct_npwp = round((total_npwp / total_koperasi * 100), 2) if total_koperasi else 0
    pct_rat = round((total_rat / total_koperasi * 100), 2) if total_koperasi else 0

    top_provinces_koperasi = sorted(prov_data, key=lambda x: x.get('jumlah_koperasi', 0), reverse=True)[:5]
    top_regencies_koperasi = sorted(reg_data, key=lambda x: x.get('jumlah_koperasi', 0), reverse=True)[:5]
    top_regencies_transaksi = sorted(reg_data, key=lambda x: x.get('nilai_transaksi', 0), reverse=True)[:5]

    # Build DVC Metrics JSON
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
            "name": top_provinces_koperasi[0].get('province_name') if top_provinces_koperasi else "",
            "count": top_provinces_koperasi[0].get('jumlah_koperasi') if top_provinces_koperasi else 0
        },
        "top_regency_by_koperasi": {
            "name": top_regencies_koperasi[0].get('regency_name') if top_regencies_koperasi else "",
            "count": top_regencies_koperasi[0].get('jumlah_koperasi') if top_regencies_koperasi else 0
        }
    }

    with open(METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] DVC Metrics -> {METRICS_JSON}")

    # Build EDA Summary Markdown Document
    md_content = f"""# Laporan Analisis Eksplorasi Data (EDA) SIMKOPDES

Laporan otomatis ini dihasilkan dari stage pipeline EDA DVC berdasarkan data `cleaned_provinces.csv` dan `cleaned_regencies.csv`.

---

## 📊 Statistik Utama Nasional

| Parameter Metric | Nilai | Persentase |
| :--- | :--- | :--- |
| **Total Provinsi Scraped** | {total_provinces} | 100% |
| **Total Kabupaten/Kota** | {total_regencies} | 100% |
| **Total Koperasi Terdaftar** | **{total_koperasi:,}** | 100% |
| **Koperasi Memiliki NIB** | {total_nib:,} | **{pct_nib}%** |
| **Koperasi Memiliki NPWP** | {total_npwp:,} | **{pct_npwp}%** |
| **Koperasi Telah RAT (2025)** | {total_rat:,} | **{pct_rat}%** |
| **Total Simpanan Pokok** | Rp {simpanan_pokok:,} | - |
| **Total Simpanan Wajib** | Rp {simpanan_wajib:,} | - |
| **Total Nilai Transaksi** | **Rp {total_nilai_transaksi:,}** | - |

---

## 🏆 Top 5 Provinsi Jumlah Koperasi Terbanyak

"""
    for idx, p in enumerate(top_provinces_koperasi, 1):
        md_content += f"{idx}. **{p.get('province_name')}**: {p.get('jumlah_koperasi'):,} Koperasi (NIB: {p.get('koperasi_nib'):,}, RAT: {p.get('koperasi_rat'):,})\n"

    md_content += "\n---\n\n## 🏙️ Top 5 Kabupaten/Kota Jumlah Koperasi Terbanyak\n\n"
    for idx, r in enumerate(top_regencies_koperasi, 1):
        md_content += f"{idx}. **{r.get('regency_name')}**: {r.get('jumlah_koperasi'):,} Koperasi\n"

    md_content += "\n---\n\n## 💰 Top 5 Kabupaten/Kota Nilai Transaksi Tertinggi\n\n"
    for idx, r in enumerate(top_regencies_transaksi, 1):
        md_content += f"{idx}. **{r.get('regency_name')}**: Rp {r.get('nilai_transaksi'):,}\n"

    with open(EDA_SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[SAVED] EDA Summary Markdown -> {EDA_SUMMARY_MD}")

    print("[DONE] Stage EDA selesai.")

if __name__ == "__main__":
    main()
