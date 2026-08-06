import os
import sys
import json
import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROVINCE_URL = "https://api.openadmindata.org/api/v1/id/province.json"
REGENCY_URL = "https://api.openadmindata.org/api/v1/id/regency.json"

DATA_RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROVINCE_FILE = os.path.join(DATA_RAW_DIR, "province.json")
REGENCY_FILE = os.path.join(DATA_RAW_DIR, "regency.json")

def process_and_optimize_json(raw_data):
    """
    Mengoptimalkan dan melengkapi struktur JSON openadmindata:
    1. Memastikan setiap entitas memiliki field 'latitude' dan 'longitude' (selain 'lat' dan 'lon').
    2. Memeriksa ketersediaan koordinat.
    """
    if not isinstance(raw_data, dict) or 'entities' not in raw_data:
        return raw_data

    entities = raw_data.get('entities', [])
    optimized_entities = []

    for item in entities:
        lat = item.get('lat')
        lon = item.get('lon')

        # Lengkapi key latitude & longitude
        item['latitude'] = lat if lat is not None else item.get('latitude')
        item['longitude'] = lon if lon is not None else item.get('longitude')

        # Pastikan lat & lon juga terisi jika latitude/longitude ada
        if item.get('lat') is None and item.get('latitude') is not None:
            item['lat'] = item['latitude']
        if item.get('lon') is None and item.get('longitude') is not None:
            item['lon'] = item['longitude']

        optimized_entities.append(item)

    raw_data['entities'] = optimized_entities
    return raw_data

def main():
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    print("[+] Memulai Pengunduhan & Optimalisasi Data OpenAdmin...")

    # 1. Download & Process Province JSON
    print(f"[*] Unduh Provinsi dari: {PROVINCE_URL} ...", end=" ", flush=True)
    try:
        r_prov = requests.get(PROVINCE_URL, timeout=60)
        if r_prov.status_code == 200:
            prov_data = process_and_optimize_json(r_prov.json())
            with open(PROVINCE_FILE, "w", encoding="utf-8") as f:
                json.dump(prov_data, f, indent=2, ensure_ascii=False)
            print(f"[OK] ({len(prov_data.get('entities', []))} provinsi tersimpan ke {PROVINCE_FILE})")
        else:
            print(f"[ERROR] HTTP {r_prov.status_code}")
    except Exception as e:
        print(f"[EXCEPTION] {str(e)}")

    # 2. Download & Process Regency JSON
    print(f"[*] Unduh Kabupaten/Kota dari: {REGENCY_URL} ...", end=" ", flush=True)
    try:
        r_reg = requests.get(REGENCY_URL, timeout=60)
        if r_reg.status_code == 200:
            reg_data = process_and_optimize_json(r_reg.json())
            with open(REGENCY_FILE, "w", encoding="utf-8") as f:
                json.dump(reg_data, f, indent=2, ensure_ascii=False)
            print(f"[OK] ({len(reg_data.get('entities', []))} kab/kota tersimpan ke {REGENCY_FILE})")
        else:
            print(f"[ERROR] HTTP {r_reg.status_code}")
    except Exception as e:
        print(f"[EXCEPTION] {str(e)}")

    print("[DONE] Pengunduhan & optimalisasi JSON selesai.")

if __name__ == "__main__":
    main()
