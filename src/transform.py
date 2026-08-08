import os
import sys
import json
import csv
import re

from config import (
    RAW_PROVINCES_CSV,
    RAW_REGENCIES_CSV,
    GEO_PROVINCES_JSON,
    GEO_REGENCIES_JSON,
    TRANSFORMED_PROVINCES_CSV,
    TRANSFORMED_REGENCIES_CSV
)
from utils.scraper_utils import save_to_csv

def parse_num(val):
    if val is None:
        return 0
    s = str(val).strip()
    s = re.sub(r'[Rp\s]', '', s)
    if not s or s == '-':
        return 0

    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif '.' in s and len(s.split('.')[-1]) == 3:
        s = s.replace('.', '')
    elif ',' in s:
        s = s.replace(',', '.')

    try:
        f = float(s)
        return int(f) if f.is_integer() else f
    except ValueError:
        return 0

def load_geo_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

def transform_provinces():
    print(f"[*] Transforming Data Provinsi dari {RAW_PROVINCES_CSV}...")
    geo_data = load_geo_json(GEO_PROVINCES_JSON)
    geo_map = {int(p['province_id']): (p.get('latitude', 0.0), p.get('longitude', 0.0)) for p in geo_data if 'province_id' in p}

    transformed_rows = []
    headers = [
        'province_id', 'province_name', 'jumlah_koperasi', 'koperasi_nib', 
        'koperasi_npwp', 'koperasi_rat', 'simpanan_pokok', 'simpanan_wajib', 
        'volume_transaksi', 'nilai_transaksi', 'pemetahaan_lahan', 
        'pemetahaan_lahan_pct', 'pembangunan_gerai_pct', 'latitude', 'longitude'
    ]

    with open(RAW_PROVINCES_CSV, encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        raw_headers = next(reader, None)

        for row in reader:
            if not row or len(row) < 2:
                continue
            prov_id = parse_num(row[0])
            name = str(row[1]).strip()
            jml = parse_num(row[2])
            nib = parse_num(row[3])
            npwp = parse_num(row[4])
            rat = parse_num(row[5])
            pokok = parse_num(row[6])
            wajib = parse_num(row[7])
            vol = parse_num(row[8])
            nilai = parse_num(row[9])
            lahan = parse_num(row[10]) if len(row) > 10 else 0
            lahan_pct = parse_num(row[11]) if len(row) > 11 else 0
            gerai_pct = parse_num(row[12]) if len(row) > 12 else 0

            lat, lon = geo_map.get(prov_id, (0.0, 0.0))

            transformed_rows.append([
                prov_id, name, jml, nib, npwp, rat, pokok, wajib,
                vol, nilai, lahan, lahan_pct, gerai_pct, lat, lon
            ])

    save_to_csv(TRANSFORMED_PROVINCES_CSV, headers, transformed_rows)
    print(f"[OK] Transformed {len(transformed_rows)} provinsi -> {TRANSFORMED_PROVINCES_CSV}")

def transform_regencies():
    print(f"[*] Transforming Data Kabupaten/Kota dari {RAW_REGENCIES_CSV}...")
    geo_data = load_geo_json(GEO_REGENCIES_JSON)
    geo_map = {(int(r['province_id']), int(r['regency_no'])): (r.get('latitude', 0.0), r.get('longitude', 0.0)) for r in geo_data if 'province_id' in r and 'regency_no' in r}

    transformed_rows = []
    headers = [
        'province_id', 'regency_no', 'regency_name', 'jumlah_koperasi', 
        'koperasi_nib', 'koperasi_npwp', 'koperasi_rat', 'simpanan_pokok', 
        'simpanan_wajib', 'volume_transaksi', 'nilai_transaksi', 'latitude', 'longitude'
    ]

    with open(RAW_REGENCIES_CSV, encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        raw_headers = next(reader, None)

        for row in reader:
            if not row or len(row) < 3:
                continue
            prov_id = parse_num(row[0])
            reg_no = parse_num(row[1])
            name = str(row[2]).strip()
            jml = parse_num(row[3])
            nib = parse_num(row[4])
            npwp = parse_num(row[5])
            rat = parse_num(row[6])
            pokok = parse_num(row[7])
            wajib = parse_num(row[8])
            vol = parse_num(row[9])
            nilai = parse_num(row[10])

            lat, lon = geo_map.get((prov_id, reg_no), (0.0, 0.0))

            transformed_rows.append([
                prov_id, reg_no, name, jml, nib, npwp, rat, pokok,
                wajib, vol, nilai, lat, lon
            ])

    save_to_csv(TRANSFORMED_REGENCIES_CSV, headers, transformed_rows)
    print(f"[OK] Transformed {len(transformed_rows)} kabupaten/kota -> {TRANSFORMED_REGENCIES_CSV}")

def main():
    print("[+] Memulai Stage Data Transformation...")
    transform_provinces()
    transform_regencies()
    print("[DONE] Transformation selesai.")

if __name__ == "__main__":
    main()
