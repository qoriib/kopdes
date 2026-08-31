-- Cloudflare D1 Database Migration
-- 0001_schema.sql

CREATE TABLE IF NOT EXISTS provinces (
    id INTEGER NOT NULL,
    province_name TEXT NOT NULL,
    total_koperasi INTEGER DEFAULT 0,
    koperasi_nib INTEGER DEFAULT 0,
    koperasi_npwp INTEGER DEFAULT 0,
    koperasi_rat INTEGER DEFAULT 0,
    simpanan_pokok REAL DEFAULT 0.0,
    simpanan_wajib REAL DEFAULT 0.0,
    volume_transaksi REAL DEFAULT 0.0,
    nilai_transaksi REAL DEFAULT 0.0,
    latitude REAL DEFAULT 0.0,
    longitude REAL DEFAULT 0.0,
    upload_date TEXT NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (id, upload_date)
);

CREATE TABLE IF NOT EXISTS regencies (
    id INTEGER NOT NULL,
    province_id INTEGER NOT NULL,
    regency_name TEXT NOT NULL,
    total_koperasi INTEGER DEFAULT 0,
    koperasi_nib INTEGER DEFAULT 0,
    koperasi_npwp INTEGER DEFAULT 0,
    koperasi_rat INTEGER DEFAULT 0,
    simpanan_pokok REAL DEFAULT 0.0,
    simpanan_wajib REAL DEFAULT 0.0,
    volume_transaksi REAL DEFAULT 0.0,
    nilai_transaksi REAL DEFAULT 0.0,
    cluster_label INTEGER DEFAULT 0,
    latitude REAL DEFAULT 0.0,
    longitude REAL DEFAULT 0.0,
    upload_date TEXT NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (id, upload_date)
);

CREATE TABLE IF NOT EXISTS metrics (
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    upload_date TEXT NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (key, upload_date)
);

CREATE TABLE IF NOT EXISTS ai_report (
    id INTEGER NOT NULL,
    report_text TEXT NOT NULL,
    labels_json TEXT NOT NULL,
    upload_date TEXT NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (id, upload_date)
);
