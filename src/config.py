import os
import sys

# Ensure src root is in python path
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Core Directories
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PREPARED_DIR = os.path.join(DATA_DIR, "prepared")
MODELING_DIR = os.path.join(DATA_DIR, "modeling")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")
SRC_REPORTS_DIR = os.path.join(SRC_DIR, "reports")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Scraper & Raw Data
RAW_PROVINCES_CSV = os.path.join(RAW_DIR, "scraped_provinces.csv")
RAW_REGENCIES_CSV = os.path.join(RAW_DIR, "scraped_regencies.csv")
GEO_PROVINCES_JSON = os.path.join(RAW_DIR, "province.json")
GEO_REGENCIES_JSON = os.path.join(RAW_DIR, "regency.json")

# Stage 1: Data Understanding Paths (4 Generic Tasks)
# Task 1: Collect Initial Data
INITIAL_DATA_REPORT_MD = os.path.join(REPORTS_DIR, "initial_data_collection_report.md")
INITIAL_DATA_METRICS_JSON = os.path.join(REPORTS_DIR, "initial_data_collection_metrics.json")
INITIAL_DATA_TEMPLATE_MD = os.path.join(SRC_REPORTS_DIR, "initial_data_collection_template.md")

# Task 2: Describe Data
DATA_DESC_REPORT_MD = os.path.join(REPORTS_DIR, "data_description_report.md")
DATA_DESC_METRICS_JSON = os.path.join(REPORTS_DIR, "data_description_metrics.json")
DATA_DESC_TEMPLATE_MD = os.path.join(SRC_REPORTS_DIR, "data_description_template.md")

# Task 3: Explore Data (EDA)
DATA_EXPLORATION_REPORT_MD = os.path.join(REPORTS_DIR, "data_exploration_report.md")
EDA_METRICS_JSON = os.path.join(REPORTS_DIR, "eda_metrics.json")
EDA_SUMMARY_MD = os.path.join(REPORTS_DIR, "eda_summary.md")
EDA_SUMMARY_TEMPLATE_MD = os.path.join(SRC_REPORTS_DIR, "eda_summary_template.md")

# Task 4: Verify Data Quality
DATA_QUALITY_REPORT_MD = os.path.join(REPORTS_DIR, "data_quality_report.md")
DATA_QUALITY_METRICS_JSON = os.path.join(REPORTS_DIR, "data_quality_metrics.json")
DATA_QUALITY_TEMPLATE_MD = os.path.join(SRC_REPORTS_DIR, "data_quality_template.md")

# Stage 2: Data Preparation Paths
CLEANED_PROVINCES_CSV = os.path.join(PREPARED_DIR, "cleaned_provinces.csv")
CLEANED_REGENCIES_CSV = os.path.join(PREPARED_DIR, "cleaned_regencies.csv")
SCALED_FEATURES_CSV = os.path.join(PREPARED_DIR, "scaled_features.csv")
PREPARATION_META_JSON = os.path.join(PREPARED_DIR, "preparation_meta.json")

# Stage 3: Modeling Paths
MODEL_PKL = os.path.join(MODELS_DIR, "kmeans_model.pkl")
CLUSTERED_REGENCIES_CSV = os.path.join(MODELING_DIR, "clustered_regencies.csv")

# Stage 4: Evaluation Paths
EVALUATE_METRICS_JSON = os.path.join(REPORTS_DIR, "evaluate_metrics.json")
EVALUATE_REPORT_MD = os.path.join(REPORTS_DIR, "evaluate_report.md")
EVALUATE_REPORT_TEMPLATE_MD = os.path.join(SRC_REPORTS_DIR, "evaluate_report_template.md")

INTERPRET_REPORT_MD = os.path.join(REPORTS_DIR, "interpret_report.md")
INTERPRET_LABELS_JSON = os.path.join(REPORTS_DIR, "interpret_labels.json")
INTERPRET_REPORT_TEMPLATE_MD = os.path.join(SRC_REPORTS_DIR, "interpret_report_template.md")

# Stage 5: Deployment Paths
SEED_SQL = os.path.join(DATA_DIR, "seed.sql")

# Scraper Settings
SCRAPE_TARGET_URL = "https://simkopdes.go.id/pers/dashboard"
SCRAPE_BASE_URL_TEMPLATE = "https://simkopdes.go.id/pers/dashboard/district/{id}"
SCRAPE_TABLE_INDEX = 2
SCRAPE_MAX_WORKERS = 5
