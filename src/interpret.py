import os
import re
import sys
import json
import dvc.api
import urllib.request
import urllib.error
import pandas as pd
from utils.env_utils import load_env
from utils.log_utils import get_logger
from utils.report_utils import generate_report_from_template
from config import (
    CLUSTERED_REGENCIES_CSV,
    MODEL_METRICS_JSON,
    AI_REPORT_MD,
    AI_LABELS_JSON,
    AI_REPORT_TEMPLATE_MD
)

logger = get_logger("interpret")

# Ambil parameter DVC
interpret_params = dvc.api.params_show().get('interpret', {})
model_params = dvc.api.params_show().get('model', {})

MODEL_NAME = interpret_params.get('model', "@cf/openai/gpt-oss-120b")
MAX_TOKENS = interpret_params.get('max_tokens', 3000)
SELECTED_FEATURES = model_params.get('selected_features', [])

IGNORED_FEATURES = ['cluster_label', 'regency_name', 'province_name', 'No', 'Province_ID']

def sanitize_json_string(s: str) -> str:
    """Membersihkan karakter tak berizin dalam string JSON."""
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


def extract_json_object(s: str) -> str:
    """Mengekstrak blok JSON pertama dari string output AI."""
    start_idx = s.find('{')
    if start_idx == -1:
        raise ValueError("Tidak ditemukan karakter '{' dalam string response")
    
    brace_count = 0
    in_quote = False
    escaped = False
    for i in range(start_idx, len(s)):
        char = s[i]
        if char == '"' and not escaped:
            in_quote = not in_quote
        if char == '\\' and not escaped:
            escaped = True
        else:
            escaped = False
            
        if not in_quote:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return s[start_idx:i+1]
    raise ValueError("Jumlah kurung kurawal '{' dan '}' tidak seimbang")

def build_cluster_profile_text(df: pd.DataFrame, active_features: list) -> str:
    """
    Menyusun ringkasan statistik per klaster secara dinamis untuk prompt LLM.
    - Fitur Numerik  : Mean
    - Fitur Kategorik: Mode
    """
    num_cols = df[active_features].select_dtypes(include=['number']).columns.tolist()
    cat_cols = df[active_features].select_dtypes(include=['object', 'category']).columns.tolist()

    profile_text = ""
    grouped = df.groupby('cluster_label')

    for label, group in grouped:
        member_count = len(group)
        profile_text += f"- **Klaster {label}** ({member_count} Kabupaten/Kota):\n"
        
        # Ringkasan Numerik
        for col in num_cols:
            mean_val = group[col].mean()
            col_label = col.replace("_", " ").title()
            if "nilai" in col or "simpanan" in col:
                profile_text += f"  - Rata-rata {col_label}: Rp {mean_val:,.2f}\n"
            else:
                profile_text += f"  - Rata-rata {col_label}: {mean_val:,.2f}\n"

        # Ringkasan Kategorik
        for col in cat_cols:
            mode_series = group[col].mode()
            mode_val = mode_series.iloc[0] if not mode_series.empty else "N/A"
            col_label = col.replace("_", " ").title()
            profile_text += f"  - Modus {col_label}: {mode_val}\n"

        profile_text += "\n"

    return profile_text

def main():
    logger.info(f"Memulai Tahap Interpretasi AI dengan Cloudflare Workers AI ({MODEL_NAME})...")
    load_env()
    
    account_id = os.environ.get("CF_ACCOUNT_ID")
    api_token = os.environ.get("CF_API_TOKEN")
    
    if not account_id or not api_token:
        logger.error("CF_ACCOUNT_ID atau CF_API_TOKEN tidak ditemukan di environment.")
        sys.exit(1)
        
    if not os.path.exists(CLUSTERED_REGENCIES_CSV) or not os.path.exists(MODEL_METRICS_JSON):
        logger.error("Data terklasterisasi atau metrik evaluasi tidak ditemukan.")
        sys.exit(1)
        
    # Read files
    df = pd.read_csv(CLUSTERED_REGENCIES_CSV)
    with open(MODEL_METRICS_JSON, encoding='utf-8') as f:
        metrics = json.load(f)

    # 1. Menentukan Fitur Aktif secara Dinamis
    if SELECTED_FEATURES:
        active_features = [col for col in SELECTED_FEATURES if col in df.columns]
    else:
        active_features = [col for col in df.columns if col not in IGNORED_FEATURES]

    # 2. Generate Teks Deskripsi Profil Klaster
    profile_text = build_cluster_profile_text(df, active_features)

    # 3. Menyusun Prompt LLM
    clustering_metrics = metrics.get('clustering_metrics', {})
    num_clusters = clustering_metrics.get('number_of_clusters', len(df['cluster_label'].unique()))
    sil_score = clustering_metrics.get('silhouette_score', 'N/A')

    prompt = f"""
Anda adalah pakar analis data koperasi Indonesia.
Analisis hasil pengelompokan (clustering) koperasi kabupaten/kota di Indonesia berikut:

Karakteristik Klaster (Berdasarkan Fitur Terpilih):
{profile_text}

Metrik Nasional:
- Jumlah klaster: {num_clusters}
- Silhouette Score: {sil_score}

Harap keluarkan hasil analisis dalam format JSON murni dengan struktur berikut:
{{
  "labels": {{
    "0": {{
      "label_name": "Klaster 0 - [Berikan Nama Klaster yang Representatif dan Profesional]",
      "description": "Klaster ini mencakup..."
    }},
    "1": {{
      "label_name": "Klaster 1 - [Berikan Nama Klaster yang Representatif dan Profesional]",
      "description": "Klaster ini mencakup..."
    }}
  }},
  "report": "# Laporan Interpretasi AI\\n\\n[Tulis laporan analisis eksekutif komprehensif, minimal 2 paragraf singkat. Jelaskan karakteristik unik dari klaster-klaster tersebut dan rekomendasi kebijakan pembangunan daerah. Gunakan format Markdown untuk isi laporan ini.]"
}}

Pastikan output hanya berupa JSON valid tanpa format markdown tambahan (seperti ```json ... ```) di luar JSON tersebut.
PENTING: Jangan gunakan karakter baris baru (enter/newline) asli di dalam nilai string JSON; jika Anda ingin membuat baris baru di dalam teks laporan atau deskripsi, gunakan escape character '\\n'.
DILARANG KERAS menggunakan emoji, simbol grafis sejenis, maupun separator garis horizontal (seperti `---`) di dalam nama klaster, deskripsi, maupun laporan markdown yang Anda hasilkan.
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
                
                # Cek struktur chat completions
                choices = result_obj.get("choices")
                ai_text = None
                if choices and len(choices) > 0:
                    ai_text = choices[0].get("message", {}).get("content")
                
                if not ai_text:
                    ai_text = result_obj.get("response") or result_obj.get("text")
                    
                if not ai_text:
                    logger.error("Response text tidak ditemukan dalam result API:")
                    logger.error(str(res_data))
                    sys.exit(1)
                
                # Pembersihan format markdown code block
                clean_text = ai_text.strip()
                if clean_text.startswith("```"):
                    clean_text = re.sub(r"^```(?:json)?\n", "", clean_text)
                    clean_text = re.sub(r"\n```$", "", clean_text)
                
                clean_text = sanitize_json_string(clean_text)
                
                try:
                    clean_text = extract_json_object(clean_text)
                    result_json = json.loads(clean_text)
                    report_text = result_json.get("report", "")
                    labels_dict = result_json.get("labels", {})
                    
                    replacements = {
                        "{{ai_report}}": report_text
                    }
                    generate_report_from_template(AI_REPORT_TEMPLATE_MD, AI_REPORT_MD, replacements)
                    
                    with open(AI_LABELS_JSON, "w", encoding="utf-8") as f:
                        json.dump(labels_dict, f, indent=2, ensure_ascii=False)
                    logger.info(f"Cluster Labels JSON -> {AI_LABELS_JSON}")
                except Exception as parse_err:
                    logger.error(f"Gagal mem-parse output AI ke JSON: {parse_err}")
                    logger.error("Output raw dari AI:")
                    logger.error(ai_text.encode('ascii', errors='backslashreplace').decode('ascii'))
                    sys.exit(1)
            else:
                logger.error(f"Gagal: {res_data.get('errors')}")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()