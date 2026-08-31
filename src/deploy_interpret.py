import os
import json
from config import INTERPRETATION_JSON, AI_REPORT_MD
from deploy_store_util import load_merged_deployment_data
from deploy_interpret_util import generate_cluster_typology

print("=== Menjalankan Analisis Interpretasi & Tipologi Klaster ===")

provinces_df, regencies_df, selected_features = load_merged_deployment_data()

cluster_labels_map, complete_report_markdown, cluster_profiles_df = generate_cluster_typology(
    regencies_df, selected_features
)

os.makedirs(os.path.dirname(INTERPRETATION_JSON), exist_ok=True)

open(AI_REPORT_MD, "w", encoding="utf-8").write(complete_report_markdown)
print(f"Laporan interpretasi tersimpan di : {AI_REPORT_MD}")

interpretation_metadata = {
    "labels_map": cluster_labels_map,
    "profile_summary": cluster_profiles_df.to_dict(orient="index"),
}

json.dump(interpretation_metadata, open(INTERPRETATION_JSON, "w", encoding="utf-8"), indent=2)
print(f"Metadata tipologi tersimpan di    : {INTERPRETATION_JSON}")

print("\nTipologi Klaster Terbentuk:")
for cluster_id, cluster_description in cluster_labels_map.items():
    print(f"  [{cluster_id}] -> {cluster_description}")
