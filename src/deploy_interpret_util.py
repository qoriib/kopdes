import os
import json
import re
import urllib.request
import urllib.error
import pandas as pd
from config import (
    CLOUDFLARE_ACCOUNT_ID,
    CLOUDFLARE_API_TOKEN,
    CLOUDFLARE_AI_GATEWAY_ID,
    CLOUDFLARE_AI_MODEL,
    PROMPT_MD,
)


# FUNGSI MENGHITUNG STATISTIK DESKRIPTIF KLASTER
def compute_cluster_descriptive_stats(regencies_df: pd.DataFrame, selected_features: list) -> pd.DataFrame:
    active_features = [f for f in selected_features if f in regencies_df.columns]
    grouped_data = regencies_df.groupby("cluster_label")[active_features]
    stats_df = grouped_data.agg(["mean", "std", "median", "min", "max"]).round(2)
    return stats_df


# FUNGSI MEMFORMAT STATISTIK DESKRIPTIF KE MARKDOWN
def format_descriptive_stats_markdown(stats_df: pd.DataFrame, regencies_df: pd.DataFrame) -> str:
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


# FUNGSI MEMANGGIL CLOUDFLARE AI GATEWAY / WORKERS AI
def call_cloudflare_ai_gateway(prompt_text: str) -> dict | None:
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        print("[AI Gateway] Kredensial CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN tidak ditemukan di environment. Menggunakan analisis statistik deterministik.")
        return None

    # Daftar URL endpoint: Coba AI Gateway terlebih dahulu, lalu fallback ke direct Workers AI
    endpoints = []
    if CLOUDFLARE_AI_GATEWAY_ID:
        endpoints.append((
            "AI Gateway",
            f"https://gateway.ai.cloudflare.com/v1/{CLOUDFLARE_ACCOUNT_ID}/{CLOUDFLARE_AI_GATEWAY_ID}/workers-ai/{CLOUDFLARE_AI_MODEL}"
        ))
    endpoints.append((
        "Direct Workers AI",
        f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{CLOUDFLARE_AI_MODEL}"
    ))

    system_instruction = (
        "Anda adalah Chief Data Scientist dan Analis Kebijakan Koperasi di Kementerian Koperasi dan UKM RI.\n"
        "Tugas Anda adalah menelaah statistik deskriptif klaster koperasi dan memberikan output dalam format JSON valid "
        "yang berisi penamaan tipologi klaster, deskripsi profil, rekomendasi kebijakan, serta laporan naratif eksekutif."
    )

    request_payload = {
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "SIMKOPDES-Pipeline/1.0"
    }

    data_bytes = json.dumps(request_payload).encode("utf-8")

    for provider_name, url in endpoints:
        try:
            print(f"[AI Gateway] Mencoba pemanggilan interpretasi via {provider_name} ({CF_AI_MODEL})...")
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as response:
                if response.status == 200:
                    resp_json = json.loads(response.read().decode("utf-8"))
                    result = resp_json.get("result", {})
                    response_text = result.get("response", "")
                    if response_text:
                        print(f"[AI Gateway] Sukses menerima respons dari {provider_name}.")
                        # Ekstrak JSON dari response text
                        return parse_ai_json_response(response_text)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            print(f"[AI Gateway] {provider_name} HTTP Error {e.code}: {error_body[:200]}")
        except Exception as e:
            print(f"[AI Gateway] {provider_name} Gagal: {str(e)[:200]}")

    return None


# FUNGSI PARSER JSON RESPON AI
def parse_ai_json_response(text: str) -> dict | None:
    try:
        # Coba parse langsung
        return json.loads(text)
    except Exception:
        # Coba ekstrak codeblock json ```json ... ```
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        
        # Coba regex menemukan kurung kurawal terluar
        brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(1))
            except Exception:
                pass

    return None


# FUNGSI SINTESIS TIPOLOGI BERBASIS STATISTIK (DETERMINISTIK / FALLBACK)
def generate_rule_based_typology(
    regencies_df: pd.DataFrame,
    cluster_profiles_df: pd.DataFrame,
    total_regencies: int
) -> tuple[dict, str]:
    cluster_labels_map = {}
    cluster_sections = []

    # Hitung peringkat metrik utama antar-klaster
    simpanan_means = cluster_profiles_df.get("simpanan_pokok", pd.Series(dtype=float))
    transaksi_means = cluster_profiles_df.get("nilai_transaksi", pd.Series(dtype=float))
    rat_means = cluster_profiles_df.get("koperasi_rat", pd.Series(dtype=float))

    for cluster_label in sorted(cluster_profiles_df.index):
        group_data = regencies_df[regencies_df["cluster_label"] == cluster_label]
        count = len(group_data)
        percentage = round((count / total_regencies) * 100, 1)

        simpanan_val = simpanan_means.get(cluster_label, 0)
        transaksi_val = transaksi_means.get(cluster_label, 0)
        rat_val = rat_means.get(cluster_label, 0)

        # Logika penentuan tipologi berbasis peringkat relatif
        is_highest_capital = (simpanan_val == simpanan_means.max())
        is_highest_transaksi = (transaksi_val == transaksi_means.max())
        is_lowest_rat = (rat_val == rat_means.min())
        is_lowest_capital = (simpanan_val == simpanan_means.min())

        if is_highest_capital or is_highest_transaksi:
            label_name = "Sentra Koperasi Maju & Mandiri"
            description = (
                "Wilayah dengan tingkat kepatuhan tata kelola RAT tinggi, kapasitas permodalan simpanan anggota solid, "
                "serta volume dan perputaran nilai transaksi ekonomi yang sangat aktif."
            )
            recommendation = (
                "Penguatan hilirisasi kemitraan pasar, digitalisasi pelaporan enterprise, dan integrasi rantai pasok industri."
            )
        elif is_lowest_rat or is_lowest_capital:
            label_name = "Koperasi Rintisan & Akselerasi Tata Kelola"
            description = (
                "Wilayah dengan ekosistem koperasi tahap rintisan, keaktifan RAT dan rasio legalitas perlu didorong, "
                "serta akumulasi permodalan simpanan yang masih terbatas."
            )
            recommendation = (
                "Pendampingan kelembagaan intensif, fasilitasi bimbingan teknis administrasi RAT, dan stimulus modal awal."
            )
        else:
            label_name = "Permodalan Tumbuh & Aktivasi Transaksi"
            description = (
                "Wilayah dengan permodalan simpanan dan kepatuhan manajerial cukup berkembang, namun aktivitas transaksi "
                "usaha dan hilirisasi operasional koperasi masih minim atau pasif."
            )
            recommendation = (
                "Pelatihan aktivasi unit usaha produktif, inkubasi bisnis koperasi desa, dan kemitraan off-taker komoditas."
            )

        cluster_labels_map[str(cluster_label)] = {
            "label_name": label_name,
            "short_name": f"Klaster {cluster_label}",
            "count": count,
            "percentage": percentage,
            "description": description,
            "recommendation": recommendation,
        }

        section_text = (
            f"### Klaster {cluster_label}: {label_name} ({count} Kab/Kota — {percentage}%)\n"
            f"**Karakteristik Wilayah:**\n{description}\n\n"
            f"**Profil Statistik Rata-rata:**\n"
            f"- Koperasi Telah RAT: **{rat_val:.1f} unit/wilayah**\n"
            f"- Simpanan Pokok: **Rp {simpanan_val:,.2f}**\n"
            f"- Nilai Transaksi: **Rp {transaksi_val:,.2f}**\n\n"
            f"**Rekomendasi Kebijakan:**\n{recommendation}"
        )
        cluster_sections.append(section_text)

    prompt_template = open(PROMPT_MD, "r", encoding="utf-8").read() if os.path.exists(PROMPT_MD) else ""
    if "{cluster_sections}" in prompt_template:
        complete_report_markdown = prompt_template.format(
            cluster_descriptive_stats=format_descriptive_stats_markdown(
                compute_cluster_descriptive_stats(regencies_df, ["koperasi_rat", "simpanan_pokok", "simpanan_wajib", "nilai_transaksi", "volume_transaksi"]),
                regencies_df
            ),
            total_regencies=total_regencies,
            cluster_sections="\n\n".join(cluster_sections),
        )
    else:
        complete_report_markdown = (
            f"# Laporan Interpretasi Hasil Klasterisasi Koperasi Desa (SIMKOPDES)\n\n"
            f"Berdasarkan analisis segmentasi terhadap **{total_regencies} Kabupaten/Kota** di Indonesia, diperoleh klasifikasi tipologi sebagai berikut:\n\n"
            + "\n\n---\n\n".join(cluster_sections)
            + "\n\n## Rekomendasi Kebijakan Strategis Nasional:\n"
            "1. **Peningkatan Kapasitas & Tata Kelola**: Penguatan kepatuhan RAT tahunan dan transparansi pelaporan keuangan koperasi.\n"
            "2. **Akselerasi Legalitas & Transformasi Digital**: Fasilitasi kemudahan izin NIB/NPWP dan adopsi pencatatan digital terintegrasi.\n"
            "3. **Ekspansi Pembiayaan & Kemitraan Rantai Pasok**: Menghubungkan koperasi berkinerja produktif dengan perbankan dan ekosistem off-taker nasional."
        )

    return cluster_labels_map, complete_report_markdown


# FUNGSI UTAMA GENERATE TIPOLOGI & LAPORAN
def generate_cluster_typology(regencies_df: pd.DataFrame, selected_features: list) -> tuple[dict, str, pd.DataFrame]:
    stats_df = compute_cluster_descriptive_stats(regencies_df, selected_features)
    stats_markdown = format_descriptive_stats_markdown(stats_df, regencies_df)

    active_features = [f for f in selected_features if f in regencies_df.columns]
    cluster_profiles_df = regencies_df.groupby("cluster_label")[active_features].mean().round(2)
    total_regencies = len(regencies_df)

    # Susun prompt untuk Cloudflare AI Gateway
    ai_prompt = f"""
Telaah data statistik deskriptif berikut dari {total_regencies} Kabupaten/Kota di Indonesia:

{stats_markdown}

Berikan respons HANYA dalam format JSON valid dengan struktur:
{{
  "clusters": {{
    "0": {{
      "label_name": "<Nama Tipologi Unik & Profesional>",
      "description": "<Deskripsi mendalam karakter koperasi di klaster ini>",
      "recommendation": "<Rekomendasi intervensi kebijakan khusus>"
    }},
    "1": {{
      "label_name": "<Nama Tipologi Unik & Profesional>",
      "description": "<Deskripsi mendalam karakter koperasi di klaster ini>",
      "recommendation": "<Rekomendasi intervensi kebijakan khusus>"
    }},
    "2": {{
      "label_name": "<Nama Tipologi Unik & Profesional>",
      "description": "<Deskripsi mendalam karakter koperasi di klaster ini>",
      "recommendation": "<Rekomendasi intervensi kebijakan khusus>"
    }}
  }},
  "executive_summary_markdown": "<Laporan naratif lengkap dalam format Markdown>"
}}
"""

    ai_result = call_cloudflare_ai_gateway(ai_prompt)

    if ai_result and "clusters" in ai_result:
        print("[AI Gateway] Berhasil memproses tipologi klaster via Cloudflare AI.")
        cluster_labels_map = {}
        ai_clusters = ai_result["clusters"]

        for cluster_key, data in ai_clusters.items():
            cluster_num = int(cluster_key) if cluster_key.isdigit() else 0
            count = int(regencies_df["cluster_label"].value_counts().get(cluster_num, 0))
            pct = round((count / total_regencies) * 100, 1)

            cluster_labels_map[str(cluster_key)] = {
                "label_name": data.get("label_name", f"Klaster {cluster_key}"),
                "short_name": f"Klaster {cluster_key}",
                "count": count,
                "percentage": pct,
                "description": data.get("description", ""),
                "recommendation": data.get("recommendation", ""),
            }

        complete_report_markdown = ai_result.get("executive_summary_markdown", "")
        if not complete_report_markdown:
            _, complete_report_markdown = generate_rule_based_typology(regencies_df, cluster_profiles_df, total_regencies)

        return cluster_labels_map, complete_report_markdown, cluster_profiles_df

    print("[AI Gateway] Menggunakan sintesis tipologi berbasis statistik deterministik.")
    cluster_labels_map, complete_report_markdown = generate_rule_based_typology(
        regencies_df, cluster_profiles_df, total_regencies
    )

    return cluster_labels_map, complete_report_markdown, cluster_profiles_df
