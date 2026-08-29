import os
import re
import json
import urllib.request
import urllib.error
import pandas as pd

from utils.env_utils import load_env
from utils.log_utils import get_logger
from utils.config_utils import get_params
from utils.report_utils import generate_report_from_template
from config import (
    CLUSTERED_REGENCIES_CSV,
    EVALUATE_METRICS_JSON,
    INTERPRET_REPORT_MD,
    INTERPRET_LABELS_JSON,
    INTERPRET_REPORT_TEMPLATE_MD,
    IGNORED_METADATA_COLUMNS
)

logger = get_logger("evaluation.interpret")

def sanitize_json_string(s: str) -> str:
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
    start_idx = s.find('{')
    if start_idx == -1:
        raise ValueError("Tidak ditemukan karakter '{' dalam respons")

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
    num_cols = df[active_features].select_dtypes(include=['number']).columns.tolist()

    profile_text = ""
    grouped = df.groupby('cluster_label')

    for label, group in grouped:
        member_count = len(group)
        profile_text += f"- **Klaster {label}** ({member_count} Kabupaten/Kota):\n"

        for col in num_cols:
            mean_val = group[col].mean()
            col_label = col.replace("_", " ").title()
            if "nilai" in col or "simpanan" in col:
                profile_text += f"  - Rata-rata {col_label}: Rp {mean_val:,.2f}\n"
            elif "rasio" in col:
                profile_text += f"  - Rata-rata {col_label}: {mean_val:.2f}%\n"
            else:
                profile_text += f"  - Rata-rata {col_label}: {mean_val:,.2f}\n"

        profile_text += "\n"

    return profile_text

def run_interpret():
    logger.info("Menjalankan CRISP-DM: Evaluation - AI Interpretation with Cloudflare Workers AI...")
    load_env()

    i_params = get_params('interpret')
    m_params = get_params('modeling')
    model_name = i_params.get('model', "@cf/openai/gpt-oss-120b")
    max_tokens = i_params.get('max_tokens', 3000)
    selected_features = m_params.get('selected_features', [])

    account_id = os.environ.get("CF_ACCOUNT_ID")
    api_token = os.environ.get("CF_API_TOKEN")

    if not account_id or not api_token:
        logger.warning("CF_ACCOUNT_ID atau CF_API_TOKEN tidak ditemukan di environment. Menghasilkan fallback label default.")
        fallback_labels = {
            "0": {"label_name": "Klaster 0 - Pertumbuhan Moderat", "description": "Wilayah dengan karakteristik operasional berkembang."},
            "1": {"label_name": "Klaster 1 - Sentra Transaksi Tinggi", "description": "Wilayah dengan volume dan nilai perputaran transaksi tinggi."},
            "2": {"label_name": "Klaster 2 - Kapasitas Kelembagaan Dasar", "description": "Wilayah dengan rasio NIB dan RAT yang memerlukan akselerasi."},
            "3": {"label_name": "Klaster 3 - Akumulasi Simpanan Signifikan", "description": "Wilayah dengan basis simpanan pokok dan wajib yang kuat."}
        }
        os.makedirs(os.path.dirname(INTERPRET_LABELS_JSON), exist_ok=True)
        with open(INTERPRET_LABELS_JSON, "w", encoding="utf-8") as f:
            json.dump(fallback_labels, f, indent=2, ensure_ascii=False)
        return

    if not os.path.exists(CLUSTERED_REGENCIES_CSV) or not os.path.exists(EVALUATE_METRICS_JSON):
        logger.error("Data terklasterisasi atau metrik evaluasi tidak ditemukan.")
        sys.exit(1)

    df = pd.read_csv(CLUSTERED_REGENCIES_CSV)
    with open(EVALUATE_METRICS_JSON, encoding='utf-8') as f:
        metrics = json.load(f)

    if selected_features:
        active_features = [col for col in selected_features if col in df.columns]
    else:
        active_features = [col for col in df.columns if col not in IGNORED_METADATA_COLUMNS]

    profile_text = build_cluster_profile_text(df, active_features)
    clustering_metrics = metrics.get('clustering_metrics', {})
    num_clusters = clustering_metrics.get('number_of_clusters', len(df['cluster_label'].unique()))
    sil_score = clustering_metrics.get('silhouette_score', 'N/A')

    prompt = f"""
Anda adalah pakar analis data koperasi dan kebijakan pembangunan wilayah Indonesia.
Analisis hasil pengelompokan (K-Means Clustering) koperasi kabupaten/kota di Indonesia berikut:

Karakteristik Klaster (Berdasarkan Fitur Operasional & Finansial):
{profile_text}

Metrik Kinerja Klasterisasi:
- Jumlah klaster: {num_clusters}
- Silhouette Coefficient: {sil_score}

Keluarkan hasil analisis dalam format JSON murni dengan struktur persis berikut:
{{
  "labels": {{
    "0": {{
      "label_name": "Klaster 0 - [Nama Tipologi yang Representatif & Profesional]",
      "description": "Klaster ini mencakup..."
    }},
    "1": {{
      "label_name": "Klaster 1 - [Nama Tipologi yang Representatif & Profesional]",
      "description": "Klaster ini mencakup..."
    }}
  }},
  "report": "# Laporan Interpretasi AI Klaster Koperasi Wilayah\\n\\n[Tuliskan laporan eksekutif komprehensif, minimal 2-3 paragraf. Uraikan karakteristik pembeda utama antarklaster, potensi penguatan kelembagaan (NIB/RAT), serta rekomendasi kebijakan strategis berbasis data untuk Kementerian Koperasi dan UKM serta Dinas Koperasi Daerah.]"
}}

PENTING:
1. Format output HANYA JSON valid.
2. Jangan gunakan enter asli di dalam string JSON, gunakan escape '\\n'.
3. DILARANG menggunakan emoji atau separator '---' di dalam JSON.
"""

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model_name}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": [
            {"role": "system", "content": "Anda adalah pakar analis data koperasi Indonesia yang merespons dalam format JSON murni."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_data = json.loads(res_body)

            if res_data.get("success"):
                result_obj = res_data.get("result", {})
                choices = result_obj.get("choices")
                ai_text = None
                if choices and len(choices) > 0:
                    ai_text = choices[0].get("message", {}).get("content")

                if not ai_text:
                    ai_text = result_obj.get("response") or result_obj.get("text")

                if not ai_text:
                    logger.error(f"Response text tidak ditemukan: {res_data}")
                    sys.exit(1)

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
                    generate_report_from_template(INTERPRET_REPORT_TEMPLATE_MD, INTERPRET_REPORT_MD, replacements)

                    os.makedirs(os.path.dirname(INTERPRET_LABELS_JSON), exist_ok=True)
                    with open(INTERPRET_LABELS_JSON, "w", encoding="utf-8") as f:
                        json.dump(labels_dict, f, indent=2, ensure_ascii=False)
                    logger.info(f"Cluster Labels JSON -> {INTERPRET_LABELS_JSON}")
                    logger.info(f"AI Interpretation Report -> {INTERPRET_REPORT_MD}")
                except Exception as parse_err:
                    logger.error(f"Gagal mem-parse output AI: {parse_err}")
                    logger.error(ai_text)
                    sys.exit(1)
            else:
                logger.error(f"API Error: {res_data.get('errors')}")
                sys.exit(1)
    except Exception as e:
        logger.error(f"HTTP/API Error saat interpretasi AI: {e}")
        sys.exit(1)

def main():
    run_interpret()

if __name__ == "__main__":
    main()
