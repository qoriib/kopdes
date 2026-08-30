import os
import json
import pandas as pd
from config import INTERPRETATION_JSON, AI_REPORT_MD
from deploy_util import load_merged_deployment_data

def generate_cluster_interpretation(
    df_reg: pd.DataFrame, selected_features: list
) -> tuple[dict, str, pd.DataFrame]:
    """
    Menganalisis karakteristik tiap kelompok klaster, menentukan tipologi wilayah,
    dan menyusun laporan interpretasi kebijakan strategis.

    Returns:
        tuple: (labels_map, full_report_text, profile_df)
    """
    active_features = [c for c in selected_features if c in df_reg.columns]
    profile_df = df_reg.groupby("cluster_label")[active_features].mean().round(2)

    profile_text = ""
    labels_map = {}

    for label, group in df_reg.groupby("cluster_label"):
        avg_koperasi = (
            group["total_koperasi"].mean()
            if "total_koperasi" in group.columns
            else 0
        )
        avg_transaksi = (
            group["nilai_transaksi"].mean()
            if "nilai_transaksi" in group.columns
            else 0
        )
        avg_nib = (
            (group["koperasi_nib"] / group["total_koperasi"] * 100).mean()
            if ("koperasi_nib" in group.columns and "total_koperasi" in group.columns)
            else 0
        )

        if (
            avg_transaksi > df_reg["nilai_transaksi"].mean()
            and avg_koperasi > df_reg["total_koperasi"].mean()
        ):
            tipologi = "Klaster Sentra Ekonomi Utama (Skala Usaha & Transaksi Sangat Tinggi)"
        elif avg_nib > 80 and avg_koperasi > df_reg["total_koperasi"].mean():
            tipologi = "Klaster Koperasi Berkembang (Kepatuhan Formalitas & Skala Tinggi)"
        elif avg_transaksi > df_reg["nilai_transaksi"].mean():
            tipologi = "Klaster Potensi Transaksi Produktif (Aktivitas Ekonomi Signifikan)"
        else:
            tipologi = "Klaster Koperasi Rintisan (Perlu Akselerasi Kelembagaan & Usaha)"

        labels_map[str(label)] = f"Klaster {label}: {tipologi}"

        profile_text += f"\n### Klaster {label} ({len(group)} Kabupaten/Kota)\n"
        profile_text += f"**Tipologi**: {tipologi}\n\n"
        for col in active_features:
            m = group[col].mean()
            lbl = col.replace("_", " ").title()
            if "nilai" in col or "simpanan" in col:
                profile_text += f"- Rata-rata {lbl}: Rp {m:,.2f}\n"
            elif "rasio" in col:
                profile_text += f"- Rata-rata {lbl}: {m:.2f}%\n"
            else:
                profile_text += f"- Rata-rata {lbl}: {m:,.2f}\n"

    full_report_text = f"""# Laporan Interpretasi Hasil Klasterisasi Koperasi Desa/Kelurahan (SIMKOPDES)

Berdasarkan hasil analisis klastering terhadap indikator kelembagaan, kepatuhan legalitas (NIB, NPWP, RAT), dan kinerja transaksi keuangan koperasi di 514 Kabupaten/Kota di Indonesia, diperoleh segmentasi tipologi wilayah sebagai berikut:

{profile_text}

## Rekomendasi Kebijakan & Intervensi:
1. **Klaster Skala/Transaksi Tinggi**: Penguatan integrasi rantai pasok industri dan diversifikasi produk bernilai tambah.
2. **Klaster Legalitas Berkembang**: Fasilitasi kemitraan perbankan/fintech dan peningkatan literasi RAT tahunan.
3. **Klaster Rintisan**: Pendampingan intensif kelembagaan, digitalisasi pembukuan, dan program pembiayaan awal.
"""

    return labels_map, full_report_text, profile_df


def run_deploy_interpret():
    print("=== Menjalankan Modul Interpretasi Klaster & Rekomendasi Kebijakan ===")
    _, df_reg, selected_features = load_merged_deployment_data()

    labels_map, full_report_text, profile_df = generate_cluster_interpretation(
        df_reg, selected_features
    )

    # Simpan laporan markdown & JSON metadata
    os.makedirs(os.path.dirname(INTERPRETATION_JSON), exist_ok=True)

    with open(AI_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(full_report_text)
    print(f"Laporan interpretasi tersimpan di: {AI_REPORT_MD}")

    interpretation_data = {
        "labels_map": labels_map,
        "profile_summary": profile_df.to_dict(orient="index")
    }
    with open(INTERPRETATION_JSON, "w", encoding="utf-8") as f:
        json.dump(interpretation_data, f, indent=2)
    print(f"Metadata tipologi tersimpan di : {INTERPRETATION_JSON}")

    print("\nTipologi Klaster Terbentuk:")
    for k, v in labels_map.items():
        print(f"  [{k}] -> {v}")


if __name__ == "__main__":
    run_deploy_interpret()
