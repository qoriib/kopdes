import os

# Base & Data Directories (relative to project root)
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
SCRAPE_DIR = os.path.join(DATA_DIR, "0_scrape")
PREPARATION_DIR = os.path.join(DATA_DIR, "2_preparation")
MODELING_DIR = os.path.join(DATA_DIR, "3_modeling")
DEPLOYMENT_DIR = os.path.join(DATA_DIR, "5_deployment")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Data File Paths per Stage
RAW_PROVINCES_CSV = os.path.join(SCRAPE_DIR, "scraped_provinces.csv")
RAW_REGENCIES_CSV = os.path.join(SCRAPE_DIR, "scraped_regencies.csv")
GEO_PROVINCES_JSON = os.path.join(SCRAPE_DIR, "province.json")
GEO_REGENCIES_JSON = os.path.join(SCRAPE_DIR, "regency.json")

CLEANED_PROVINCES_CSV = os.path.join(PREPARATION_DIR, "cleaned_provinces.csv")
CLEANED_REGENCIES_CSV = os.path.join(PREPARATION_DIR, "cleaned_regencies.csv")
SCALED_FEATURES_CSV = os.path.join(PREPARATION_DIR, "scaled_features.csv")

CLUSTERED_REGENCIES_CSV = os.path.join(MODELING_DIR, "clustered_regencies.csv")
MODEL_PKL = os.path.join(MODELS_DIR, "kmeans_model.pkl")

SEED_SQL = os.path.join(DEPLOYMENT_DIR, "seed.sql")

# Shared Feature Definitions
NUMERIC_COLUMNS = [
    'total_koperasi',
    'koperasi_nib',
    'koperasi_npwp',
    'koperasi_rat',
    'simpanan_pokok',
    'simpanan_wajib',
    'volume_transaksi',
    'nilai_transaksi'
]

FEATURE_COLUMNS = [
    'total_koperasi',
    'rasio_nib',
    'rasio_npwp',
    'rasio_rat',
    'simpanan_pokok',
    'simpanan_wajib',
    'volume_transaksi',
    'nilai_transaksi'
]

SELECTED_FEATURES = FEATURE_COLUMNS
