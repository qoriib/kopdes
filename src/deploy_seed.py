import os
import json
import pandas as pd
from config import (
    UNDERSTANDING_PROVINCES_CSV,
    CLUSTERED_REGENCIES_CSV,
    FEATURE_SELECTION_JSON,
    GEO_PROVINCES_JSON,
    GEO_REGENCIES_JSON,
    SEED_SQL
)


def sql_val(val):
    """Helper untuk format nilai SQL yang aman dan menangani NULL/escape string."""
    if pd.isna(val) or val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    escaped = str(val).replace("'", "''")
    return f"'{escaped}'"


def generate_seed_sql():
    print("=== Memulai Pembangkitan Data Seed SQL Cloudflare D1 ===")

    # 1. Pemuatan Data
    df_prov = pd.read_csv(UNDERSTANDING_PROVINCES_CSV)
    df_reg = pd.read_csv(CLUSTERED_REGENCIES_CSV)

    if os.path.exists(FEATURE_SELECTION_JSON):
        with open(FEATURE_SELECTION_JSON, "r", encoding="utf-8") as f:
            prep_config = json.load(f)
        selected_features = prep_config.get("selected_features", [])
    else:
        selected_features = [
            c
            for c in df_reg.select_dtypes("number").columns
            if c
            not in (
                "province_id",
                "regency_no",
                "id",
                "cluster_label",
                "latitude",
                "longitude",
            )
        ]

    # 2. Penggabungan Data Geospasial Provinsi
    if os.path.exists(GEO_PROVINCES_JSON):
        with open(GEO_PROVINCES_JSON, encoding="utf-8") as f:
            geo_p = pd.DataFrame(json.load(f))
        if not geo_p.empty:
            geo_p["province_name_clean"] = (
                geo_p["name"].astype(str).str.strip().str.upper()
            )
            df_prov = df_prov.merge(
                geo_p[
                    [
                        "province_name_clean",
                        "province_id",
                        "latitude",
                        "longitude",
                    ]
                ],
                left_on="province_name",
                right_on="province_name_clean",
                how="left",
            ).drop(columns=["province_name_clean"], errors="ignore")

    # 3. Penggabungan Data Geospasial Kabupaten/Kota
    if os.path.exists(GEO_REGENCIES_JSON):
        with open(GEO_REGENCIES_JSON, encoding="utf-8") as f:
            geo_r = pd.DataFrame(json.load(f))
        if not geo_r.empty:
            df_reg = df_reg.merge(
                geo_r[["province_id", "regency_no", "latitude", "longitude"]],
                on=["province_id", "regency_no"],
                how="left",
            )

    print(f"Total Baris Provinsi     : {len(df_prov)}")
    print(f"Total Baris Kab/Kota     : {len(df_reg)}")
    print(f"Fitur Terpilih Aktif     : {selected_features}")

    # 4. Profil Rata-Rata & Tipologi Klaster
    active_features = [c for c in selected_features if c in df_reg.columns]
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
            tipologi = (
                "Klaster Koperasi Rintisan (Perlu Akselerasi Kelembagaan & Usaha)"
            )

        labels_map[str(label)] = f"Klaster {label}: {tipologi}"

        profile_text += (
            f"\n### Klaster {label} ({len(group)} Kabupaten/Kota)\n"
        )
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

    # 5. Membangun Pernyataan SQL Insert
    sql_lines = [
        "-- Cloudflare D1 SQL Seed Generated Automatically by Pipeline",
        "CREATE TABLE IF NOT EXISTS provinces (id INTEGER PRIMARY KEY, province_name TEXT NOT NULL, total_koperasi INTEGER DEFAULT 0, koperasi_nib INTEGER DEFAULT 0, koperasi_npwp INTEGER DEFAULT 0, koperasi_rat INTEGER DEFAULT 0, rasio_nib REAL DEFAULT 0.0, rasio_npwp REAL DEFAULT 0.0, rasio_rat REAL DEFAULT 0.0, simpanan_pokok REAL DEFAULT 0.0, simpanan_wajib REAL DEFAULT 0.0, volume_transaksi REAL DEFAULT 0.0, nilai_transaksi REAL DEFAULT 0.0, latitude REAL DEFAULT 0.0, longitude REAL DEFAULT 0.0);",
        "CREATE TABLE IF NOT EXISTS regencies (id INTEGER PRIMARY KEY, province_id INTEGER NOT NULL REFERENCES provinces(id) ON DELETE CASCADE, regency_name TEXT NOT NULL, total_koperasi INTEGER DEFAULT 0, koperasi_nib INTEGER DEFAULT 0, koperasi_npwp INTEGER DEFAULT 0, koperasi_rat INTEGER DEFAULT 0, rasio_nib REAL DEFAULT 0.0, rasio_npwp REAL DEFAULT 0.0, rasio_rat REAL DEFAULT 0.0, simpanan_pokok REAL DEFAULT 0.0, simpanan_wajib REAL DEFAULT 0.0, volume_transaksi REAL DEFAULT 0.0, nilai_transaksi REAL DEFAULT 0.0, cluster_label INTEGER DEFAULT 0, latitude REAL DEFAULT 0.0, longitude REAL DEFAULT 0.0);",
        "CREATE TABLE IF NOT EXISTS ai_report (id INTEGER PRIMARY KEY AUTOINCREMENT, report_text TEXT NOT NULL, labels_json TEXT NOT NULL);",
        "\n-- Insert Provinces",
    ]

    for idx, r in df_prov.iterrows():
        p_id = sql_val(r.get("province_id", r.get("no", idx + 1)))
        p_name = sql_val(r["province_name"])
        lat = sql_val(r.get("latitude", 0.0))
        lon = sql_val(r.get("longitude", 0.0))
        tot = r["total_koperasi"] if r["total_koperasi"] > 0 else 1
        r_nib = (
            round(r["koperasi_nib"] / tot * 100, 2)
            if "koperasi_nib" in r
            else r.get("rasio_nib", 0.0)
        )
        r_npwp = (
            round(r["koperasi_npwp"] / tot * 100, 2)
            if "koperasi_npwp" in r
            else r.get("rasio_npwp", 0.0)
        )
        r_rat = (
            round(r["koperasi_rat"] / tot * 100, 2)
            if "koperasi_rat" in r
            else r.get("rasio_rat", 0.0)
        )
        sql_lines.append(
            f"INSERT OR REPLACE INTO provinces (id, province_name, total_koperasi, koperasi_nib, koperasi_npwp, koperasi_rat, rasio_nib, rasio_npwp, rasio_rat, simpanan_pokok, simpanan_wajib, volume_transaksi, nilai_transaksi, latitude, longitude) VALUES ({p_id}, {p_name}, {r['total_koperasi']}, {r['koperasi_nib']}, {r['koperasi_npwp']}, {r['koperasi_rat']}, {r_nib}, {r_npwp}, {r_rat}, {r['simpanan_pokok']}, {r['simpanan_wajib']}, {r['volume_transaksi']}, {r['nilai_transaksi']}, {lat}, {lon});"
        )

    sql_lines.append("\n-- Insert Regencies")
    for idx, r in df_reg.iterrows():
        r_id = sql_val(idx + 1)
        p_id = sql_val(r.get("province_id", 1))
        r_name = sql_val(r["regency_name"])
        lat = sql_val(r.get("latitude", 0.0))
        lon = sql_val(r.get("longitude", 0.0))
        tot = r["total_koperasi"] if r["total_koperasi"] > 0 else 1
        r_nib = (
            round(r["koperasi_nib"] / tot * 100, 2)
            if "koperasi_nib" in r
            else r.get("rasio_nib", 0.0)
        )
        r_npwp = (
            round(r["koperasi_npwp"] / tot * 100, 2)
            if "koperasi_npwp" in r
            else r.get("rasio_npwp", 0.0)
        )
        r_rat = (
            round(r["koperasi_rat"] / tot * 100, 2)
            if "koperasi_rat" in r
            else r.get("rasio_rat", 0.0)
        )
        sql_lines.append(
            f"INSERT OR REPLACE INTO regencies (id, province_id, regency_name, total_koperasi, koperasi_nib, koperasi_npwp, koperasi_rat, rasio_nib, rasio_npwp, rasio_rat, simpanan_pokok, simpanan_wajib, volume_transaksi, nilai_transaksi, cluster_label, latitude, longitude) VALUES ({r_id}, {p_id}, {r_name}, {r['total_koperasi']}, {r['koperasi_nib']}, {r['koperasi_npwp']}, {r['koperasi_rat']}, {r_nib}, {r_npwp}, {r_rat}, {r['simpanan_pokok']}, {r['simpanan_wajib']}, {r['volume_transaksi']}, {r['nilai_transaksi']}, {r['cluster_label']}, {lat}, {lon});"
        )

    sql_lines.append("\n-- Insert AI Interpretation Report")
    report_escaped = sql_val(full_report_text)
    labels_escaped = sql_val(json.dumps(labels_map))
    sql_lines.append(
        f"INSERT OR REPLACE INTO ai_report (id, report_text, labels_json) VALUES (1, {report_escaped}, {labels_escaped});"
    )

    # 6. Penyimpanan File
    os.makedirs(os.path.dirname(SEED_SQL), exist_ok=True)
    with open(SEED_SQL, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_lines))

    file_size_kb = round(os.path.getsize(SEED_SQL) / 1024, 2)
    print(f"File SQL Seed berhasil dibuat : {SEED_SQL}")
    print(f"Ukuran File                   : {file_size_kb} KB")
    print(f"Total Entri Provinsi          : {len(df_prov)}")
    print(f"Total Entri Kabupaten/Kota    : {len(df_reg)}")


if __name__ == "__main__":
    generate_seed_sql()
