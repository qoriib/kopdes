import os
import json
import sqlite3
import pandas as pd
from config import SEED_SQL, INTERPRETATION_JSON, AI_REPORT_MD
from deploy_util import (
    load_merged_deployment_data,
    prepare_provinces_for_db,
    prepare_regencies_for_db,
)
from deploy_interpret import generate_cluster_interpretation

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS provinces (
    id INTEGER PRIMARY KEY,
    province_name TEXT NOT NULL,
    total_koperasi INTEGER DEFAULT 0,
    koperasi_nib INTEGER DEFAULT 0,
    koperasi_npwp INTEGER DEFAULT 0,
    koperasi_rat INTEGER DEFAULT 0,
    rasio_nib REAL DEFAULT 0.0,
    rasio_npwp REAL DEFAULT 0.0,
    rasio_rat REAL DEFAULT 0.0,
    simpanan_pokok REAL DEFAULT 0.0,
    simpanan_wajib REAL DEFAULT 0.0,
    volume_transaksi REAL DEFAULT 0.0,
    nilai_transaksi REAL DEFAULT 0.0,
    latitude REAL DEFAULT 0.0,
    longitude REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS regencies (
    id INTEGER PRIMARY KEY,
    province_id INTEGER NOT NULL REFERENCES provinces(id) ON DELETE CASCADE,
    regency_name TEXT NOT NULL,
    total_koperasi INTEGER DEFAULT 0,
    koperasi_nib INTEGER DEFAULT 0,
    koperasi_npwp INTEGER DEFAULT 0,
    koperasi_rat INTEGER DEFAULT 0,
    rasio_nib REAL DEFAULT 0.0,
    rasio_npwp REAL DEFAULT 0.0,
    rasio_rat REAL DEFAULT 0.0,
    simpanan_pokok REAL DEFAULT 0.0,
    simpanan_wajib REAL DEFAULT 0.0,
    volume_transaksi REAL DEFAULT 0.0,
    nilai_transaksi REAL DEFAULT 0.0,
    cluster_label INTEGER DEFAULT 0,
    latitude REAL DEFAULT 0.0,
    longitude REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS ai_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_text TEXT NOT NULL,
    labels_json TEXT NOT NULL
);
"""


def build_sqlite_seed_database(
    df_prov: pd.DataFrame,
    df_reg: pd.DataFrame,
    labels_map: dict,
    full_report_text: str
) -> sqlite3.Connection:
    """
    Membangun in-memory database SQLite dan mengisi data tabel menggunakan Pandas to_sql.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_DDL)

    # 1. Siapkan DataFrame terstruktur
    df_prov_db = prepare_provinces_for_db(df_prov)
    df_reg_db = prepare_regencies_for_db(df_reg)
    df_report_db = pd.DataFrame([{
        "id": 1,
        "report_text": full_report_text,
        "labels_json": json.dumps(labels_map, ensure_ascii=False)
    }])

    # 2. Masukkan data ke SQLite melalui Pandas to_sql
    df_prov_db.to_sql("provinces", conn, if_exists="append", index=False)
    df_reg_db.to_sql("regencies", conn, if_exists="append", index=False)
    df_report_db.to_sql("ai_report", conn, if_exists="append", index=False)

    return conn


def export_seed_sql_from_sqlite(conn: sqlite3.Connection, output_path: str):
    """
    Mengekspor seluruh skema dan data dari koneksi SQLite menjadi file SQL seed resmi.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("-- Cloudflare D1 SQL Seed Generated via Pandas & SQLite3\n")
        for statement in conn.iterdump():
            f.write(f"{statement}\n")


def run_deploy_store():
    print("=== Menjalankan Modul Pembangkitan Database Seed SQL (Pandas + SQLite3) ===")
    df_prov, df_reg, selected_features = load_merged_deployment_data()

    # 1. Pemuatan atau pembangkitan interpretasi klaster
    if os.path.exists(AI_REPORT_MD) and os.path.exists(INTERPRETATION_JSON):
        with open(AI_REPORT_MD, "r", encoding="utf-8") as f:
            full_report_text = f.read()
        with open(INTERPRETATION_JSON, "r", encoding="utf-8") as f:
            interp_data = json.load(f)
            labels_map = interp_data.get("labels_map", {})
    else:
        labels_map, full_report_text, _ = generate_cluster_interpretation(df_reg, selected_features)

    # 2. Bangun database in-memory & ekspor SQL
    conn = build_sqlite_seed_database(df_prov, df_reg, labels_map, full_report_text)
    export_seed_sql_from_sqlite(conn, SEED_SQL)

    # 3. Verifikasi jumlah baris langsung dari query SQLite
    cur = conn.cursor()
    prov_count = cur.execute("SELECT COUNT(*) FROM provinces").fetchone()[0]
    reg_count = cur.execute("SELECT COUNT(*) FROM regencies").fetchone()[0]
    rep_count = cur.execute("SELECT COUNT(*) FROM ai_report").fetchone()[0]
    conn.close()

    file_size_kb = round(os.path.getsize(SEED_SQL) / 1024, 2)
    print(f"File SQL Seed berhasil dibuat : {SEED_SQL}")
    print(f"Ukuran File                   : {file_size_kb} KB")
    print(f"Total Baris Tabel Provinces   : {prov_count}")
    print(f"Total Baris Tabel Regencies   : {reg_count}")
    print(f"Total Baris Tabel AI Report   : {rep_count}")


if __name__ == "__main__":
    run_deploy_store()
