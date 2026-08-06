import os
import sys
import json
import urllib.request
import urllib.error
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DATA_MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "model")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")

CLUSTERED_REGENCIES_CSV = os.path.join(DATA_MODEL_DIR, "clustered_regencies.csv")
MODEL_METRICS_JSON = os.path.join(REPORTS_DIR, "model_metrics.json")

CLUSTER_LABELS_JSON = os.path.join(REPORTS_DIR, "cluster_labels.json")
AI_INTERPRETATION_MD = os.path.join(REPORTS_DIR, "ai_interpretation.md")

CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID") or os.environ.get("CLOUDFLARE_ACCOUNT_ID") or "d506d851c5b269e38a2a0efd6cbf9a01"
CF_API_TOKEN = os.environ.get("CF_API_TOKEN") or os.environ.get("CLOUDFLARE_API_TOKEN")

# Model Llama 3.1 8B Instruct di Cloudflare Workers AI
CF_MODEL_NAME = "@cf/meta/llama-3.1-8b-instruct"

def call_cloudflare_ai(prompt, system_prompt="Anda adalah pakar analis data koperasi Indonesia yang memberikan laporan analitis formal tanpa emoji."):
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        print("[!] Token Kredensial Cloudflare AI tidak terdeteksi. Menggunakan mode analisis statistik aturan internal.")
        return None

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_MODEL_NAME}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1500
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            if res_json.get("success") and "result" in res_json:
                return res_json["result"].get("response") or res_json["result"].get("text")
    except Exception as e:
        print(f"[!] Error saat menghubungi Cloudflare AI API: {e}")
    
    return None

def generate_fallback_labels(cluster_summary):
    labels = {}
    for cluster_id, row in cluster_summary.iterrows():
        jml = row['jumlah_koperasi']
        nilai = row['nilai_transaksi']
        rat = row['koperasi_rat']
        
        if nilai > 50000000000 or jml > 500:
            name = "Klaster Utama: Koperasi Skala Besar & Volume Transaksi Tinggi"
        elif rat > 200:
            name = "Klaster Berkembang: Koperasi Produktif Kepatuhan RAT Tinggi"
        elif jml < 150:
            name = "Klaster Perintis: Koperasi Skala Mikro/Rintisan"
        else:
            name = "Klaster Menengah: Koperasi Skala Operasional Standar"
        
        labels[str(cluster_id)] = {
            "label_name": f"Klaster {cluster_id} - {name}",
            "description": f"Klaster ini mencakup rata-rata {jml:.0f} koperasi per kabupaten/kota dengan rata-rata nilai transaksi Rp {nilai:,.0f}."
        }
    return labels

def main():
    print("[+] Memulai Stage Interpretasi AI (Cloudflare Workers AI)...")
    os.makedirs(REPORTS_DIR, exist_ok=True)

    if not os.path.exists(CLUSTERED_REGENCIES_CSV):
        raise FileNotFoundError(f"Berkas {CLUSTERED_REGENCIES_CSV} tidak ditemukan.")

    df = pd.read_csv(CLUSTERED_REGENCIES_CSV)
    
    # Ringkasan Statistik per Klaster
    cluster_summary = df.groupby('cluster_label').agg({
        'jumlah_koperasi': 'mean',
        'koperasi_nib': 'mean',
        'koperasi_npwp': 'mean',
        'koperasi_rat': 'mean',
        'nilai_transaksi': 'mean',
        'simpanan_pokok': 'mean',
        'simpanan_wajib': 'mean',
        'regency_name': 'count'
    }).rename(columns={'regency_name': 'jumlah_kabupaten'}).round(2)

    stats_str = ""
    for cid, r in cluster_summary.iterrows():
        stats_str += f"- Klaster {cid} ({r['jumlah_kabupaten']} Kab/Kota): Rata-rata Koperasi={r['jumlah_koperasi']:.0f}, NIB={r['koperasi_nib']:.0f}, RAT={r['koperasi_rat']:.0f}, Transaksi=Rp {r['nilai_transaksi']:,.0f}\n"

    prompt = f"""Diberikan hasil pengelompokan (clustering) 514 kabupaten/kota di Indonesia berdasarkan data SIMKOPDES:

Statistik Klaster:
{stats_str}

Berikan interpretasi dalam 2 tugas:
TUGAS 1: Berikan label deskriptif singkat untuk masing-masing Klaster berdasarkan profil kinerjanya.
TUGAS 2: Tuliskan laporan analisis eksekutif komprehensif (3-4 paragraf) yang menjelaskan implikasi strategis dari hasil klasterisasi ini bagi Kementerian Koperasi dan UKM dalam pembinaan daerah.

Gunakan bahasa Indonesia formal baku dan TANPA emoji.
"""

    ai_response = call_cloudflare_ai(prompt)

    if ai_response:
        print("[OK] Interpretasi AI dari Cloudflare Workers AI berhasil diterima.")
        interpretation_text = ai_response.strip()
    else:
        print("[*] Menggenerate laporan interpretasi otomatis berbasis statistik...")
        fallback_labels = generate_fallback_labels(cluster_summary)
        interpretation_text = "# Laporan Interpretasi Analisis Klaster SIMKOPDES\n\n## Tugas 1: Penamaan dan Pelabelan Klaster\n\n"
        for cid, info in fallback_labels.items():
            interpretation_text += f"### {info['label_name']}\n{info['description']}\n\n"
        
        interpretation_text += "## Tugas 2: Analisis Eksekutif Komprehensif\n\n"
        interpretation_text += "Hasil pengelompokan menunjukkan disparitas kapasitas operasional dan kepatuhan hukum koperasi antar wilayah kabupaten/kota di Indonesia. Wilayah dengan konsentrasi klaster utama memperlihatkan aktivitas ekonomi yang kuat dengan nilai transaksi dan tingkat kepatuhan RAT yang tinggi.\n\n"
        interpretation_text += "Sebaliknya, wilayah yang tergolong dalam klaster perintis memerlukan intervensi kebijakan yang difokuskan pada pendampingan tata kelola internal, penguatan kelembagaan melalui pembentukan NIB dan NPWP, serta dorongan pelaksanaan Rapat Anggota Tahunan secara berkala.\n\n"
        interpretation_text += "Strategi pembinaan berbasis klaster ini memungkinkan Kementerian Koperasi dan UKM untuk mengalokasikan sumber daya dan program bantuan secara lebih presisi, efisien, dan berdampak langsung pada penguatan ekonomi desa berbasis koperasi."

    # Simpan JSON Cluster Labels
    cluster_labels_dict = generate_fallback_labels(cluster_summary)
    with open(CLUSTER_LABELS_JSON, "w", encoding="utf-8") as f:
        json.dump(cluster_labels_dict, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] Cluster Labels JSON -> {CLUSTER_LABELS_JSON}")

    # Simpan Markdown AI Interpretation
    with open(AI_INTERPRETATION_MD, "w", encoding="utf-8") as f:
        f.write(interpretation_text)
    print(f"[SAVED] Laporan Interpretasi AI Markdown -> {AI_INTERPRETATION_MD}")

    print("[DONE] Stage Interpretasi AI selesai.")

if __name__ == "__main__":
    main()
