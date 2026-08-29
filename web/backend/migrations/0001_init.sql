-- Migration to initialize SIMKOPDES D1 database schema with CRISP-DM research indicators
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

CREATE TABLE IF NOT EXISTS metrics (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_text TEXT NOT NULL,
    labels_json TEXT NOT NULL
);
