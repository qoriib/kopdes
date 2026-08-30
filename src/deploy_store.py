import os
import json
import pandas as pd
from config import SEED_SQL, INTERPRETATION_JSON, AI_REPORT_MD
from deploy_util import sql_val, load_merged_deployment_data
from deploy_interpret import generate_cluster_interpretation


def generate_seed_statements(
    df_prov: pd.DataFrame,
    df_reg: pd.DataFrame,
    labels_map: dict,
    full_report_text: str
) -> list[str]:
    """
    Menyusun baris perintah SQL (DDL dan DML INSERT) untuk seeding tabel database Cloudflare D1.
    """
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

    return sql_lines


def run_deploy_store():
    print("=== Menjalankan Modul Pembangkitan Database Seed SQL Cloudflare D1 ===")
    df_prov, df_reg, selected_features = load_merged_deployment_data()

    # Periksa apakah file laporan & interpretasi sudah tersedia
    if os.path.exists(AI_REPORT_MD) and os.path.exists(INTERPRETATION_JSON):
        with open(AI_REPORT_MD, "r", encoding="utf-8") as f:
            full_report_text = f.read()
        with open(INTERPRETATION_JSON, "r", encoding="utf-8") as f:
            interp_data = json.load(f)
            labels_map = interp_data.get("labels_map", {})
    else:
        labels_map, full_report_text, _ = generate_cluster_interpretation(df_reg, selected_features)

    sql_statements = generate_seed_statements(df_prov, df_reg, labels_map, full_report_text)

    os.makedirs(os.path.dirname(SEED_SQL), exist_ok=True)
    with open(SEED_SQL, "w", encoding="utf-8") as f:
        f.write("\n".join(sql_statements))

    file_size_kb = round(os.path.getsize(SEED_SQL) / 1024, 2)
    print(f"File SQL Seed berhasil dibuat : {SEED_SQL}")
    print(f"Ukuran File                   : {file_size_kb} KB")
    print(f"Total Entri Provinsi          : {len(df_prov)}")
    print(f"Total Entri Kabupaten/Kota    : {len(df_reg)}")


if __name__ == "__main__":
    run_deploy_store()
