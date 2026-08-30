import os

# Base & Data Directories (relative to project root)
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)

ARTIFACT_DIR = os.path.join(BASE_DIR, "artifact")
DATA_DIR = ARTIFACT_DIR
SCRAPE_DIR = os.path.join(ARTIFACT_DIR, "scrape")
UNDERSTANDING_DIR = os.path.join(ARTIFACT_DIR, "1_understanding")
PREPARATION_DIR = os.path.join(ARTIFACT_DIR, "2_preparation")
MODELING_DIR = os.path.join(ARTIFACT_DIR, "3_modeling")
EVALUATION_DIR = os.path.join(ARTIFACT_DIR, "4_evaluation")
DEPLOYMENT_DIR = os.path.join(ARTIFACT_DIR, "deployment")

# Data File Paths per Stage
RAW_PROVINCES_CSV = os.path.join(SCRAPE_DIR, "scraped_provinces.csv")
RAW_REGENCIES_CSV = os.path.join(SCRAPE_DIR, "scraped_regencies.csv")
UNDERSTANDING_PROVINCES_CSV = os.path.join(UNDERSTANDING_DIR, "cleaned_provinces.csv")
UNDERSTANDING_REGENCIES_CSV = os.path.join(UNDERSTANDING_DIR, "cleaned_regencies.csv")
GEO_PROVINCES_JSON = os.path.join(DEPLOYMENT_DIR, "province.json")
GEO_REGENCIES_JSON = os.path.join(DEPLOYMENT_DIR, "regency.json")

PREPARED_REGENCIES_CSV = os.path.join(PREPARATION_DIR, "prepared_regencies.csv")

# Models (stored in artifact/3_modeling)
KMEANS_MODEL_PKL = os.path.join(MODELING_DIR, "kmeans_model.pkl")
AGGLOMERATIVE_MODEL_PKL = os.path.join(MODELING_DIR, "agglomerative_model.pkl")

# Evaluation & Output Paths
CLUSTERED_REGENCIES_CSV = os.path.join(EVALUATION_DIR, "clustered_regencies.csv")
MODEL_COMPARISON_JSON = os.path.join(EVALUATION_DIR, "model_comparison.json")
INTERPRETATION_JSON = os.path.join(DEPLOYMENT_DIR, "interpretation.json")
AI_REPORT_MD = os.path.join(DEPLOYMENT_DIR, "ai_report.md")
SCHEMA_SQL = os.path.join(DEPLOYMENT_DIR, "schema.sql")
SEED_SQL = os.path.join(DEPLOYMENT_DIR, "seed.sql")

# Raw Scraped Column Mappings
PROVINCE_COLUMN_MAPPING = {
    'No': 'no',
    'Provinsi': 'province_name',
    'Jumlah Koperasi': 'total_koperasi',
    'Koperasi Memiliki NIB': 'koperasi_nib',
    'Koperasi Memiliki NPWP': 'koperasi_npwp',
    'Koperasi Telah RAT (2025)': 'koperasi_rat',
    'Simpanan Pokok': 'simpanan_pokok',
    'Simpanan Wajib': 'simpanan_wajib',
    'Volume Transaksi (2026)': 'volume_transaksi',
    'Nilai Transaksi (2026)': 'nilai_transaksi',
    'Pemetahaan Lahan': 'pemetahaan_lahan',
    'Pemetahaan Lahan (%)': 'pemetahaan_lahan_pct',
    'Pembangunan Gerai (%)': 'pembangunan_gerai_pct'
}

REGENCY_COLUMN_MAPPING = {
    'province_id': 'province_id',
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

FEATURE_EVALUATION_JSON = os.path.join(UNDERSTANDING_DIR, "feature_evaluation.json")
FEATURE_SELECTION_JSON = os.path.join(PREPARATION_DIR, "feature_selection.json")

