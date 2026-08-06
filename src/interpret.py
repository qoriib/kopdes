import os
import sys
import json
import urllib.request
import urllib.error
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def load_env():
    env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_file):
        with open(env_file, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

def main():
    print("[+] Memulai Tahap Interpretasi AI dengan Cloudflare Workers AI...")
    load_env()
    
    account_id = os.environ.get("CF_ACCOUNT_ID")
    api_token = os.environ.get("CF_API_TOKEN")
    
    if not account_id or not api_token:
        print("[!] Error: CF_ACCOUNT_ID atau CF_API_TOKEN tidak ditemukan di environment.")
        sys.exit(1)
        
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "model", "clustered_regencies.csv")
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "reports", "model_metrics.json")
    output_path = os.path.join(os.path.dirname(__file__), "..", "reports", "ai_interpretation.md")
    
    if not os.path.exists(data_path) or not os.path.exists(metrics_path):
        print("[!] Error: Data atau metrik evaluasi tidak ditemukan.")
        sys.exit(1)
        
    # Read files
    df = pd.read_csv(data_path)
    with open(metrics_path, encoding='utf-8') as f:
        metrics = json.load(f)
        
    # Group by cluster and aggregate
    cluster_profile = df.groupby('cluster_label').agg({
        'jumlah_koperasi': 'mean',
        'koperasi_nib': 'mean',
        'koperasi_npwp': 'mean',
        'koperasi_rat': 'mean',
        'nilai_transaksi': 'mean',
        'regency_name': 'count'
    }).rename(columns={'regency_name': 'jumlah_anggota_kabupaten'}).round(2)
    
    profile_text = ""
    for label, row in cluster_profile.iterrows():
        profile_text += f"- **Klaster {label}** ({int(row['jumlah_anggota_kabupaten'])} Kabupaten/Kota):\n"
        profile_text += f"  - Rata-rata Jumlah Koperasi: {row['jumlah_koperasi']:,}\n"
        profile_text += f"  - Rata-rata Koperasi NIB: {row['koperasi_nib']:,}\n"
        profile_text += f"  - Rata-rata Koperasi NPWP: {row['koperasi_npwp']:,}\n"
        profile_text += f"  - Rata-rata Koperasi RAT: {row['koperasi_rat']:,}\n"
        profile_text += f"  - Rata-rata Nilai Transaksi: Rp {row['nilai_transaksi']:,}\n\n"
        
    prompt = f"""
Analisis hasil pengelompokan (clustering) koperasi kabupaten/kota di Indonesia berikut.
Berdasarkan karakteristik rata-rata tiap klaster di bawah ini, harap:
1. Berikan nama yang representatif dan profesional untuk masing-masing klaster (misalnya, "Klaster 0: Pusat Koperasi Mikro Berkembang").
2. Jelaskan interpretasi mendalam karakteristik unik dari masing-masing klaster (kekuatan, kelemahan, pola).
3. Berikan rekomendasi kebijakan pembangunan daerah yang spesifik untuk setiap klaster.

Karakteristik Klaster:
{profile_text}

Metrik Nasional:
- Jumlah klaster: {metrics['clustering_metrics']['number_of_clusters']}
- Silhouette Score: {metrics['clustering_metrics']['silhouette_score']}

Tuliskan output dalam Bahasa Indonesia, gunakan format Markdown yang rapi. Mulai langsung dengan '# Laporan Interpretasi AI untuk Klasterisasi SIMKOPDES'.
"""

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3-8b-instruct"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "Anda adalah asisten analisis data ahli perkoperasian Indonesia."},
            {"role": "user", "content": prompt}
        ]
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_data = json.loads(res_body)
            
            if res_data.get("success"):
                ai_text = res_data["result"]["response"]
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(ai_text)
                print(f"[SAVED] Laporan Interpretasi AI -> {output_path}")
            else:
                print(f"[!] Gagal: {res_data.get('errors')}")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"[!] HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
