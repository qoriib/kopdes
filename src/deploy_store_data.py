import datetime
from config import SEED_DATA_SQL, MODEL_COMPARISON_JSON
from deploy_store_util import (
    load_merged_deployment_data,
    prepare_metrics_dataframe,
    dump_tables_to_sql,
)

snapshot_date = datetime.date.today().isoformat()
print(f"=== Menyimpan Seeder Data Wilayah (Snapshot: {snapshot_date}) ===")

provinces_df, regencies_df, _ = load_merged_deployment_data()

# Siapkan kolom id dan upload_date
provinces_df["id"] = provinces_df["no"]
provinces_df["upload_date"] = snapshot_date

regencies_df["id"] = list(range(1, len(regencies_df) + 1))
regencies_df["upload_date"] = snapshot_date

metrics_database_df = prepare_metrics_dataframe(MODEL_COMPARISON_JSON, snapshot_date)

dump_tables_to_sql(
    {
        "provinces": provinces_df,
        "regencies": regencies_df,
        "metrics": metrics_database_df,
    },
    SEED_DATA_SQL,
    snapshot_date,
)

print(f"File SQL Seed Data berhasil dibuat : {SEED_DATA_SQL}")
print(f"Total Baris Tabel Provinces        : {len(provinces_df)}")
print(f"Total Baris Tabel Regencies        : {len(regencies_df)}")
print(f"Total Baris Tabel Metrics          : {len(metrics_database_df)}")
