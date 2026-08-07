import os
import sys
import json
import re
import urllib.request
import urllib.error
import yaml
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

PARAMS_FILE = os.path.join(os.path.dirname(__file__), "..", "params.yaml")
params = {}
if os.path.exists(PARAMS_FILE):
    try:
        with open(PARAMS_FILE, encoding='utf-8') as f:
            params = yaml.safe_load(f).get('interpret', {})
    except Exception:
        pass

MODEL_NAME = params.get('model', "@cf/openai/gpt-oss-120b")
MAX_TOKENS = params.get('max_tokens', 3000)

def sanitize_json_string(s):
    in_quote = False
    escaped = False
    chars = []
    for char in s:
        if char == '"' and not escaped:
            in_quote = not in_quote
        if char == '\\' and not escaped:
            escaped = True
        else:
            escaped = False
            
        if in_quote and char == '\n':
            chars.append('\\n')
        elif in_quote and char == '\r':
            chars.append('\\r')
        else:
            chars.append(char)
    return "".join(chars)

def main():
    print(f"[+] Memulai Tahap Interpretasi AI dengan Cloudflare Workers AI ({MODEL_NAME})...")
    load_env()
    
    account_id = os.environ.get("CF_ACCOUNT_ID")
    api_token = os.environ.get("CF_API_TOKEN")
    
    if not account_id or not api_token:
        print("[!] Error: CF_ACCOUNT_ID atau CF_API_TOKEN tidak ditemukan di environment.")
        sys.exit(1)
        
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "model", "clustered_regencies.csv")
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "reports", "evaluate_metrics.json")
    output_path = os.path.join(os.path.dirname(__file__), "..", "reports", "interpret_report.md")
    labels_output_path = os.path.join(os.path.dirname(__file__), "..", "reports", "interpret_labels.json")
    
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
Anda adalah pakar analis data koperasi Indonesia.
Analisis hasil pengelompokan (clustering) koperasi kabupaten/kota di Indonesia berikut:

Karakteristik Klaster:
{profile_text}

Metrik Nasional:
- Jumlah klaster: {metrics['clustering_metrics']['number_of_clusters']}
- Silhouette Score: {metrics['clustering_metrics']['silhouette_score']}

Harap keluarkan hasil analisis dalam format JSON murni dengan struktur berikut:
{{
  "labels": {{
    "0": {{
      "label_name": "Klaster 0 - [Berikan Nama Klaster yang Representatif dan Profesional]",
      "description": "Klaster ini mencakup rata-rata [rata-rata koperasi] dengan rata-rata nilai transaksi Rp [nilai transaksi]..."
    }},
    "1": {{
      "label_name": "Klaster 1 - [Berikan Nama Klaster yang Representatif dan Profesional]",
      "description": "Klaster ini mencakup rata-rata [rata-rata koperasi] dengan rata-rata nilai transaksi Rp [nilai transaksi]..."
    }}
    // Dan seterusnya untuk semua klaster yang ada
  }},
  "report": "# Laporan Interpretasi AI untuk Klasterisasi SIMKOPDES\\n\\n[Tulis laporan analisis eksekutif komprehensif, minimal 3-4 paragraf. Jelaskan interpretasi mendalam karakteristik unik dari masing-masing klaster (kekuatan, kelemahan, pola) serta rekomendasi kebijakan pembangunan daerah yang spesifik untuk setiap klaster. Gunakan format Markdown untuk isi laporan ini.]"
}}

Pastikan output hanya berupa JSON valid tanpa format markdown tambahan (seperti ```json ... ```) di luar JSON tersebut. PENTING: Jangan gunakan karakter baris baru (enter/newline) asli di dalam nilai string JSON; jika Anda ingin membuat baris baru di dalam teks laporan atau deskripsi, gunakan escape character '\\n'. DILARANG KERAS menggunakan emoji, simbol grafis sejenis, maupun separator garis horizontal (seperti `---`) di dalam nama klaster, deskripsi, maupun laporan markdown yang Anda hasilkan.
"""

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL_NAME}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "Anda adalah asisten analisis data ahli perkoperasian Indonesia yang hanya menjawab dalam format JSON sesuai spesifikasi."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": MAX_TOKENS
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_data = json.loads(res_body)
            
            if res_data.get("success"):
                result_obj = res_data.get("result", {})
                
                # Try chat completions structure first
                choices = result_obj.get("choices")
                ai_text = None
                if choices and len(choices) > 0:
                    ai_text = choices[0].get("message", {}).get("content")
                
                # Fallback to response or text
                if not ai_text:
                    ai_text = result_obj.get("response") or result_obj.get("text")
                    
                if not ai_text:
                    print("[!] Error: response/text/content tidak ditemukan dalam result:")
                    print(res_data)
                    sys.exit(1)
                
                # Clean up any potential markdown code block formatting
                clean_text = ai_text.strip()
                if clean_text.startswith("```"):
                    clean_text = re.sub(r"^```(?:json)?\n", "", clean_text)
                    clean_text = re.sub(r"\n```$", "", clean_text)
                
                clean_text = sanitize_json_string(clean_text)
                
                try:
                    result_json = json.loads(clean_text)
                    report_text = result_json.get("report", "")
                    labels_dict = result_json.get("labels", {})
                    
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(report_text)
                    print(f"[SAVED] Laporan Interpretasi AI -> {output_path}")
                    
                    with open(labels_output_path, "w", encoding="utf-8") as f:
                        json.dump(labels_dict, f, indent=2, ensure_ascii=False)
                    print(f"[SAVED] Cluster Labels JSON -> {labels_output_path}")
                except Exception as parse_err:
                    print(f"[!] Gagal mem-parse output AI ke JSON: {parse_err}")
                    print("Output raw dari AI:")
                    print(ai_text)
                    sys.exit(1)
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
