import os

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
TRANSFORM_DIR = os.path.join(DATA_DIR, "transform")
PREPROCESS_DIR = os.path.join(DATA_DIR, "preprocess")
DATA_MODEL_DIR = os.path.join(DATA_DIR, "model")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")
MODEL_DIR = os.path.join(BASE_DIR, "models")

# File Paths
RAW_PROVINCES_CSV = os.path.join(RAW_DIR, "scraped_provinces.csv")
RAW_REGENCIES_CSV = os.path.join(RAW_DIR, "scraped_regencies.csv")
GEO_PROVINCES_JSON = os.path.join(RAW_DIR, "province.json")
GEO_REGENCIES_JSON = os.path.join(RAW_DIR, "regency.json")

TRANSFORMED_PROVINCES_CSV = os.path.join(TRANSFORM_DIR, "transformed_provinces.csv")
TRANSFORMED_REGENCIES_CSV = os.path.join(TRANSFORM_DIR, "transformed_regencies.csv")

SCALED_FEATURES_CSV = os.path.join(PREPROCESS_DIR, "scaled_features.csv")
PREPROCESS_META_JSON = os.path.join(PREPROCESS_DIR, "preprocess_meta.json")
PREPROCESS_REPORT_MD = os.path.join(REPORTS_DIR, "preprocess_report.md")

MODEL_PKL = os.path.join(MODEL_DIR, "kmeans_model.pkl")
CLUSTERED_REGENCIES_CSV = os.path.join(DATA_MODEL_DIR, "clustered_regencies.csv")

MODEL_METRICS_JSON = os.path.join(REPORTS_DIR, "evaluate_metrics.json")
CLUSTERING_REPORT_MD = os.path.join(REPORTS_DIR, "evaluate_report.md")

METRICS_JSON = os.path.join(REPORTS_DIR, "eda_metrics.json")
EDA_SUMMARY_MD = os.path.join(REPORTS_DIR, "eda_summary.md")

AI_REPORT_MD = os.path.join(REPORTS_DIR, "interpret_report.md")
AI_LABELS_JSON = os.path.join(REPORTS_DIR, "interpret_labels.json")

SEED_SQL = os.path.join(DATA_DIR, "seed.sql")

PARAMS_FILE = os.path.join(BASE_DIR, "params.yaml")
