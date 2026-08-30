from config import SEED_DATA_SQL
from deploy_util import (
    get_current_snapshot_date,
    load_merged_deployment_data,
    prepare_provinces_dataframe,
    prepare_regencies_dataframe,
    dump_tables_to_sql,
)

snapshot_date = get_current_snapshot_date()
print(f"=== Menyimpan Seeder Data Wilayah (Snapshot: {snapshot_date}) ===")

provinces_df, regencies_df, _ = load_merged_deployment_data()

provinces_database_df = prepare_provinces_dataframe(provinces_df, snapshot_date)
regencies_database_df = prepare_regencies_dataframe(regencies_df, snapshot_date)

dump_tables_to_sql(
    {
        "provinces": provinces_database_df,
        "regencies": regencies_database_df,
    },
    SEED_DATA_SQL,
    snapshot_date,
)

print(f"File SQL Seed Data berhasil dibuat : {SEED_DATA_SQL}")
print(f"Total Baris Tabel Provinces        : {len(provinces_database_df)}")
print(f"Total Baris Tabel Regencies        : {len(regencies_database_df)}")
