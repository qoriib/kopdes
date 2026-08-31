import os
import json
import sqlite3
import pandas as pd
from config import (
    UNDERSTANDING_PROVINCES_CSV,
    CLUSTERED_REGENCIES_CSV,
    FEATURE_SELECTION_JSON,
    GEO_PROVINCES_JSON,
    GEO_REGENCIES_JSON,
    SCHEMA_SQL,
)


# FUNGSI MEMUAT DAN MENGGABUNGKAN DATA DEPLOYMENT
def load_merged_deployment_data() -> tuple[pd.DataFrame, pd.DataFrame, list]:
    # 1. Baca data provinsi dari file CSV
    provinces_df = pd.read_csv(
        UNDERSTANDING_PROVINCES_CSV,
        dtype={
            "no": str,
            "province_name": str,
        }
    )

    # 2. Baca data kabupaten/kota hasil klasterisasi
    regencies_df = pd.read_csv(
        CLUSTERED_REGENCIES_CSV,
        dtype={
            "province_id": str,
            "regency_no": str,
            "regency_name": str,
        }
    )

    # 3. Baca konfigurasi fitur yang dipilih
    feature_file = open(FEATURE_SELECTION_JSON, "r", encoding="utf-8")
    feature_config = json.load(feature_file)
    selected_features = feature_config.get("selected_features", [])

    # 4. Baca dan gabungkan koordinat GeoJSON Provinsi
    geo_provinces_file = open(GEO_PROVINCES_JSON, "r", encoding="utf-8")
    geo_provinces_data = json.load(geo_provinces_file)
    geo_provinces_df = pd.DataFrame(geo_provinces_data)
    geo_provinces_df["province_id"] = geo_provinces_df["province_id"].astype(str)

    provinces_df = provinces_df.merge(
        geo_provinces_df[["province_id", "latitude", "longitude"]],
        left_on="no",
        right_on="province_id",
        how="left"
    )

    # Laporan verifikasi mapping koordinat provinsi
    missing_geo_provinces = provinces_df[
        provinces_df["latitude"].isna() | provinces_df["longitude"].isna()
    ]
    if not missing_geo_provinces.empty:
        print(f"[PERINGATAN] Ditemukan {len(missing_geo_provinces)} provinsi tanpa koordinat geospasial:")
        for _, prov_row in missing_geo_provinces.iterrows():
            prov_no = prov_row.get("no", "-")
            prov_name = prov_row.get("province_name", "-")
            print(f"  - No: {prov_no} | Nama: {prov_name}")
    else:
        print(f"[INFO] Seluruh data provinsi ({len(provinces_df)}) berhasil dipetakan ke koordinat geospasial.")

    # 5. Baca dan gabungkan koordinat GeoJSON Kabupaten/Kota
    geo_regencies_file = open(GEO_REGENCIES_JSON, "r", encoding="utf-8")
    geo_regencies_data = json.load(geo_regencies_file)
    geo_regencies_df = pd.DataFrame(geo_regencies_data)
    geo_regencies_df["province_id"] = geo_regencies_df["province_id"].astype(str)
    geo_regencies_df["regency_no"] = geo_regencies_df["regency_no"].astype(str)

    regencies_df = regencies_df.merge(
        geo_regencies_df[["province_id", "regency_no", "latitude", "longitude"]],
        on=["province_id", "regency_no"],
        how="left"
    )

    # Laporan verifikasi mapping koordinat kabupaten/kota
    missing_geo_regencies = regencies_df[
        regencies_df["latitude"].isna() | regencies_df["longitude"].isna()
    ]
    if not missing_geo_regencies.empty:
        print(f"[PERINGATAN] Ditemukan {len(missing_geo_regencies)} kabupaten/kota tanpa koordinat geospasial:")
        for _, reg_row in missing_geo_regencies.iterrows():
            prov_id = reg_row.get("province_id", "-")
            reg_no = reg_row.get("regency_no", "-")
            reg_name = reg_row.get("regency_name", "-")
            print(f"  - Provinsi ID: {prov_id} | No: {reg_no} | Nama: {reg_name}")
    else:
        print(f"[INFO] Seluruh data kabupaten/kota ({len(regencies_df)}) berhasil dipetakan ke koordinat geospasial.")

    return provinces_df, regencies_df, selected_features


# FUNGSI MEMBENTUK DATAFRAME METRIK SESUAI SKEMA DATABASE
def prepare_metrics_dataframe(model_comparison_path: str, snapshot_date: str) -> pd.DataFrame:
    metrics_rows = []

    if os.path.exists(model_comparison_path):
        comparison_file = open(model_comparison_path, "r", encoding="utf-8")
        comparison_data = json.load(comparison_file)

        best_k = str(comparison_data.get("best_k", "3"))
        best_algo = str(comparison_data.get("best_algorithm", "Agglomerative"))
        comparison_table = comparison_data.get("comparison_table", [])

        # Cari metrik dari model terbaik
        best_model_metrics = {}
        for row in comparison_table:
            if str(row.get("Model", "")).lower() == best_algo.lower():
                best_model_metrics = row
                break

        if not best_model_metrics and comparison_table:
            best_model_metrics = comparison_table[0]

        silhouette = best_model_metrics.get("Silhouette", 0.0)
        calinski = best_model_metrics.get("Calinski-Harabasz", 0.0)
        davies = best_model_metrics.get("Davies-Bouldin", 0.0)

        metrics_map = {
            "silhouette_score": f"{float(silhouette):.4f}",
            "calinski_harabasz_index": f"{float(calinski):.2f}",
            "davies_bouldin_index": f"{float(davies):.4f}",
            "number_of_clusters": best_k,
            "best_algorithm": best_algo,
        }

        for key_name, value_text in metrics_map.items():
            metrics_rows.append({
                "key": key_name,
                "value": str(value_text),
                "upload_date": snapshot_date,
            })

    return pd.DataFrame(metrics_rows)


# FUNGSI MENGEKSPOR TABEL DATAFRAME KE FILE SEEDER SQL
def dump_tables_to_sql(table_data_map: dict[str, pd.DataFrame], output_path: str, snapshot_date: str):
    schema_file = open(SCHEMA_SQL, "r", encoding="utf-8")
    schema_ddl = schema_file.read()

    sqlite_connection = sqlite3.connect(":memory:")
    sqlite_connection.executescript(schema_ddl)

    for table_name, dataframe in table_data_map.items():
        if not dataframe.empty:
            cursor = sqlite_connection.execute(f"PRAGMA table_info({table_name})")
            schema_column_names = [table_info_row[1] for table_info_row in cursor.fetchall()]
            valid_columns = [col for col in schema_column_names if col in dataframe.columns]

            dataframe_filtered = dataframe[valid_columns]
            dataframe_filtered.to_sql(table_name, sqlite_connection, if_exists="append", index=False)

    sql_statements = [
        f"-- Cloudflare D1 SQL Seed (Snapshot Date: {snapshot_date})",
        "BEGIN TRANSACTION;"
    ]

    for statement in sqlite_connection.iterdump():
        if statement.startswith("INSERT INTO"):
            replaced_statement = statement.replace("INSERT INTO", "INSERT OR REPLACE INTO")
            sql_statements.append(replaced_statement)

    sql_statements.append("COMMIT;\n")

    output_file = open(output_path, "w", encoding="utf-8")
    output_file.write("\n".join(sql_statements))
    output_file.close()

    sqlite_connection.close()
