import os
import json
import pandas as pd
from config import (
    UNDERSTANDING_PROVINCES_CSV,
    CLUSTERED_REGENCIES_CSV,
    FEATURE_SELECTION_JSON,
    GEO_PROVINCES_JSON,
    GEO_REGENCIES_JSON
)


def sql_val(val):
    """
    Format nilai kolom ke literal SQL yang aman untuk Cloudflare D1.
    Menangani NULL, tipe angka, dan escaping single quote.
    """
    if pd.isna(val) or val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    escaped = str(val).replace("'", "''")
    return f"'{escaped}'"


def load_merged_deployment_data() -> tuple[pd.DataFrame, pd.DataFrame, list]:
    """
    Memuat data provinsi, kabupaten/kota hasil klasterisasi, dan menggabungkan
    koordinat geospasial (latitude, longitude) dari berkas referensi GeoJSON.

    Returns:
        tuple: (df_prov, df_reg, selected_features)
    """
    if not os.path.exists(UNDERSTANDING_PROVINCES_CSV):
        raise FileNotFoundError(f"File provinsi tidak ditemukan: {UNDERSTANDING_PROVINCES_CSV}")
    if not os.path.exists(CLUSTERED_REGENCIES_CSV):
        raise FileNotFoundError(f"File klaster kabupaten/kota tidak ditemukan: {CLUSTERED_REGENCIES_CSV}")

    df_prov = pd.read_csv(UNDERSTANDING_PROVINCES_CSV)
    df_reg = pd.read_csv(CLUSTERED_REGENCIES_CSV)

    # 1. Memuat konfigurasi fitur terpilih
    if os.path.exists(FEATURE_SELECTION_JSON):
        with open(FEATURE_SELECTION_JSON, "r", encoding="utf-8") as f:
            prep_config = json.load(f)
        selected_features = prep_config.get("selected_features", [])
    else:
        selected_features = [
            c
            for c in df_reg.select_dtypes("number").columns
            if c not in (
                "province_id",
                "regency_no",
                "id",
                "cluster_label",
                "latitude",
                "longitude",
            )
        ]

    # 2. Penggabungan Geospasial Provinsi
    if os.path.exists(GEO_PROVINCES_JSON):
        with open(GEO_PROVINCES_JSON, encoding="utf-8") as f:
            geo_p = pd.DataFrame(json.load(f))
        if not geo_p.empty:
            geo_p["province_name_clean"] = geo_p["name"].astype(str).str.strip().str.upper()
            df_prov = df_prov.merge(
                geo_p[["province_name_clean", "province_id", "latitude", "longitude"]],
                left_on="province_name",
                right_on="province_name_clean",
                how="left",
            ).drop(columns=["province_name_clean"], errors="ignore")

    # 3. Penggabungan Geospasial Kabupaten/Kota
    if os.path.exists(GEO_REGENCIES_JSON):
        with open(GEO_REGENCIES_JSON, encoding="utf-8") as f:
            geo_r = pd.DataFrame(json.load(f))
        if not geo_r.empty:
            df_reg = df_reg.merge(
                geo_r[["province_id", "regency_no", "latitude", "longitude"]],
                on=["province_id", "regency_no"],
                how="left",
            )

    return df_prov, df_reg, selected_features
