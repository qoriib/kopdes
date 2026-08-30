import os
import json
import sqlite3
import datetime
import pandas as pd
from config import (
    UNDERSTANDING_PROVINCES_CSV,
    CLUSTERED_REGENCIES_CSV,
    FEATURE_SELECTION_JSON,
    GEO_PROVINCES_JSON,
    GEO_REGENCIES_JSON,
    SCHEMA_SQL,
    PROMPT_MD,
)


def get_current_snapshot_date() -> str:
    """Mengembalikan tanggal hari ini dalam format ISO YYYY-MM-DD."""
    return datetime.date.today().isoformat()


def load_merged_deployment_data() -> tuple[pd.DataFrame, pd.DataFrame, list]:
    """
    Memuat data provinsi, kabupaten/kota terklasterisasi, dan menggabungkan
    koordinat geospasial latitude dan longitude.
    """
    provinces_df = pd.read_csv(UNDERSTANDING_PROVINCES_CSV)
    regencies_df = pd.read_csv(CLUSTERED_REGENCIES_CSV)

    feature_config = json.load(open(FEATURE_SELECTION_JSON, "r", encoding="utf-8"))
    selected_features = feature_config.get("selected_features", [])

    geo_provinces = pd.DataFrame(json.load(open(GEO_PROVINCES_JSON, "r", encoding="utf-8")))
    geo_provinces["province_name_clean"] = geo_provinces["name"].astype(str).str.strip().str.upper()
    provinces_df = provinces_df.merge(
        geo_provinces[["province_name_clean", "province_id", "latitude", "longitude"]],
        left_on="province_name",
        right_on="province_name_clean",
        how="left"
    ).drop(columns=["province_name_clean"], errors="ignore")

    geo_regencies = pd.DataFrame(json.load(open(GEO_REGENCIES_JSON, "r", encoding="utf-8")))

    if "province_id" in regencies_df.columns:
        regencies_df["province_id"] = regencies_df["province_id"].fillna(0).astype(int)
    if "regency_no" in regencies_df.columns:
        regencies_df["regency_no"] = regencies_df["regency_no"].fillna(0).astype(int)

    regencies_df = regencies_df.merge(
        geo_regencies[["province_id", "regency_no", "latitude", "longitude"]],
        on=["province_id", "regency_no"],
        how="left"
    )

    if "province_id" in provinces_df.columns:
        provinces_df["province_id"] = provinces_df["province_id"].fillna(0).astype(int)

    return provinces_df, regencies_df, selected_features


def prepare_provinces_dataframe(provinces_df: pd.DataFrame, snapshot_date: str) -> pd.DataFrame:
    """Membentuk DataFrame provinsi terstruktur sesuai skema D1."""
    total_koperasi_series = provinces_df["total_koperasi"].replace(0, 1)

    return pd.DataFrame({
        "id": provinces_df["province_id"].fillna(provinces_df.get("no", range(1, len(provinces_df) + 1))).astype(int),
        "province_name": provinces_df["province_name"].astype(str),
        "total_koperasi": provinces_df["total_koperasi"].fillna(0).astype(int),
        "koperasi_nib": provinces_df.get("koperasi_nib", 0).fillna(0).astype(int),
        "koperasi_npwp": provinces_df.get("koperasi_npwp", 0).fillna(0).astype(int),
        "koperasi_rat": provinces_df.get("koperasi_rat", 0).fillna(0).astype(int),
        "rasio_nib": ((provinces_df.get("koperasi_nib", 0) / total_koperasi_series) * 100).round(2).fillna(0.0),
        "rasio_npwp": ((provinces_df.get("koperasi_npwp", 0) / total_koperasi_series) * 100).round(2).fillna(0.0),
        "rasio_rat": ((provinces_df.get("koperasi_rat", 0) / total_koperasi_series) * 100).round(2).fillna(0.0),
        "simpanan_pokok": provinces_df.get("simpanan_pokok", 0.0).fillna(0.0),
        "simpanan_wajib": provinces_df.get("simpanan_wajib", 0.0).fillna(0.0),
        "volume_transaksi": provinces_df.get("volume_transaksi", 0.0).fillna(0.0),
        "nilai_transaksi": provinces_df.get("nilai_transaksi", 0.0).fillna(0.0),
        "latitude": provinces_df.get("latitude", 0.0).fillna(0.0),
        "longitude": provinces_df.get("longitude", 0.0).fillna(0.0),
        "upload_date": snapshot_date,
    })


def prepare_regencies_dataframe(regencies_df: pd.DataFrame, snapshot_date: str) -> pd.DataFrame:
    """Membentuk DataFrame kabupaten/kota terstruktur sesuai skema D1."""
    total_koperasi_series = regencies_df["total_koperasi"].replace(0, 1)

    return pd.DataFrame({
        "id": range(1, len(regencies_df) + 1),
        "province_id": regencies_df.get("province_id", 1).fillna(1).astype(int),
        "regency_name": regencies_df["regency_name"].astype(str),
        "total_koperasi": regencies_df["total_koperasi"].fillna(0).astype(int),
        "koperasi_nib": regencies_df.get("koperasi_nib", 0).fillna(0).astype(int),
        "koperasi_npwp": regencies_df.get("koperasi_npwp", 0).fillna(0).astype(int),
        "koperasi_rat": regencies_df.get("koperasi_rat", 0).fillna(0).astype(int),
        "rasio_nib": ((regencies_df.get("koperasi_nib", 0) / total_koperasi_series) * 100).round(2).fillna(0.0),
        "rasio_npwp": ((regencies_df.get("koperasi_npwp", 0) / total_koperasi_series) * 100).round(2).fillna(0.0),
        "rasio_rat": ((regencies_df.get("koperasi_rat", 0) / total_koperasi_series) * 100).round(2).fillna(0.0),
        "simpanan_pokok": regencies_df.get("simpanan_pokok", 0.0).fillna(0.0),
        "simpanan_wajib": regencies_df.get("simpanan_wajib", 0.0).fillna(0.0),
        "volume_transaksi": regencies_df.get("volume_transaksi", 0.0).fillna(0.0),
        "nilai_transaksi": regencies_df.get("nilai_transaksi", 0.0).fillna(0.0),
        "cluster_label": regencies_df.get("cluster_label", 0).fillna(0).astype(int),
        "latitude": regencies_df.get("latitude", 0.0).fillna(0.0),
        "longitude": regencies_df.get("longitude", 0.0).fillna(0.0),
        "upload_date": snapshot_date,
    })


def compute_cluster_descriptive_stats(regencies_df: pd.DataFrame, selected_features: list) -> pd.DataFrame:
    """Menghitung ringkasan statistik deskriptif agregat (mean, std, median, min, max) tiap klaster."""
    active_features = [feature for feature in selected_features if feature in regencies_df.columns]
    stats_df = regencies_df.groupby("cluster_label")[active_features].agg(["mean", "std", "median", "min", "max"]).round(2)
    return stats_df


def format_descriptive_stats_markdown(stats_df: pd.DataFrame, regencies_df: pd.DataFrame) -> str:
    """Mengubah tabel statistik deskriptif menjadi teks format Markdown yang mudah dibaca oleh LLM."""
    markdown_lines = []
    cluster_counts = regencies_df["cluster_label"].value_counts().to_dict()

    for cluster_label in sorted(stats_df.index):
        count = cluster_counts.get(cluster_label, 0)
        markdown_lines.append(f"\n### Statistik Klaster {cluster_label} ({count} Kabupaten/Kota)")
        
        feature_names = stats_df.columns.levels[0]
        for feature in feature_names:
            mean_val = stats_df.loc[cluster_label, (feature, "mean")]
            std_val = stats_df.loc[cluster_label, (feature, "std")]
            median_val = stats_df.loc[cluster_label, (feature, "median")]
            min_val = stats_df.loc[cluster_label, (feature, "min")]
            max_val = stats_df.loc[cluster_label, (feature, "max")]
            
            label_text = feature.replace("_", " ").title()
            if "nilai" in feature or "simpanan" in feature:
                markdown_lines.append(
                    f"- **{label_text}**: Rata-rata = Rp {mean_val:,.2f} (Median = Rp {median_val:,.2f}, Std = Rp {std_val:,.2f}, Min = Rp {min_val:,.2f}, Max = Rp {max_val:,.2f})"
                )
            elif "rasio" in feature:
                markdown_lines.append(
                    f"- **{label_text}**: Rata-rata = {mean_val:.2f}% (Median = {median_val:.2f}%, Min = {min_val:.2f}%, Max = {max_val:.2f}%)"
                )
            else:
                markdown_lines.append(
                    f"- **{label_text}**: Rata-rata = {mean_val:,.2f} (Median = {median_val:,.2f}, Std = {std_val:,.2f}, Min = {min_val:,.2f}, Max = {max_val:,.2f})"
                )

    return "\n".join(markdown_lines)


def generate_cluster_typology(regencies_df: pd.DataFrame, selected_features: list) -> tuple[dict, str, pd.DataFrame]:
    """
    Menyusun prompt berbasis statistik deskriptif dan menghasilkan laporan interpretasi klaster.
    """
    stats_df = compute_cluster_descriptive_stats(regencies_df, selected_features)
    stats_markdown = format_descriptive_stats_markdown(stats_df, regencies_df)

    active_features = [f for f in selected_features if f in regencies_df.columns]
    cluster_profiles_df = regencies_df.groupby("cluster_label")[active_features].mean().round(2)

    cluster_sections = []
    cluster_labels_map = {}
    total_regencies = len(regencies_df)

    for cluster_label, group_data in regencies_df.groupby("cluster_label"):
        count = len(group_data)
        percentage = round((count / total_regencies) * 100, 1)
        
        cluster_name = f"Klaster {cluster_label}"
        cluster_labels_map[str(cluster_label)] = f"{cluster_name} ({count} Kab/Kota - {percentage}%)"

        section_text = f"### {cluster_name} ({count} Kabupaten/Kota — {percentage}% dari Total Nasional)\n"
        section_text += "**Profil Statistik Indikator Koperasi:**\n"
        for feature in active_features:
            mean_val = group_data[feature].mean()
            median_val = group_data[feature].median()
            feature_title = feature.replace("_", " ").title()
            if "nilai" in feature or "simpanan" in feature:
                section_text += f"- {feature_title}: Rata-rata = Rp {mean_val:,.2f} (Median: Rp {median_val:,.2f})\n"
            elif "rasio" in feature:
                section_text += f"- {feature_title}: Rata-rata = {mean_val:.2f}% (Median: {median_val:.2f}%)\n"
            else:
                section_text += f"- {feature_title}: Rata-rata = {mean_val:,.2f} (Median: {median_val:,.2f})\n"

        cluster_sections.append(section_text)

    prompt_template = open(PROMPT_MD, "r", encoding="utf-8").read()

    complete_report_markdown = prompt_template.format(
        cluster_descriptive_stats=stats_markdown,
        total_regencies=total_regencies,
        cluster_sections="\n\n".join(cluster_sections),
    )

    return cluster_labels_map, complete_report_markdown, cluster_profiles_df


def dump_tables_to_sql(table_data_map: dict[str, pd.DataFrame], output_path: str, snapshot_date: str):
    """Membangun SQLite in-memory dan mengekspor pernyataan SQL INSERT OR REPLACE."""
    schema_ddl = open(SCHEMA_SQL, "r", encoding="utf-8").read()

    sqlite_connection = sqlite3.connect(":memory:")
    sqlite_connection.executescript(schema_ddl)

    for table_name, dataframe in table_data_map.items():
        dataframe.to_sql(table_name, sqlite_connection, if_exists="append", index=False)

    sql_statements = [f"-- Cloudflare D1 SQL Seed (Snapshot Date: {snapshot_date})", "BEGIN TRANSACTION;"]
    for statement in sqlite_connection.iterdump():
        if statement.startswith("INSERT INTO"):
            sql_statements.append(statement.replace("INSERT INTO", "INSERT OR REPLACE INTO"))
    sql_statements.append("COMMIT;\n")

    open(output_path, "w", encoding="utf-8").write("\n".join(sql_statements))
    sqlite_connection.close()
