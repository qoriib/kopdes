import json
import datetime
import pandas as pd
from config import SEED_INTERPRET_SQL, INTERPRETATION_JSON, AI_REPORT_MD
from deploy_store_util import dump_tables_to_sql

snapshot_date = datetime.date.today().isoformat()
print(f"=== Menyimpan Seeder Interpretasi AI (Snapshot: {snapshot_date}) ===")

complete_report_markdown = open(AI_REPORT_MD, "r", encoding="utf-8").read()
interpretation_metadata = json.load(open(INTERPRETATION_JSON, "r", encoding="utf-8"))
cluster_labels_map = interpretation_metadata.get("labels_map", {})

ai_report_database_df = pd.DataFrame([
    {
        "id": 1,
        "report_text": complete_report_markdown,
        "labels_json": json.dumps(cluster_labels_map, ensure_ascii=False),
        "upload_date": snapshot_date,
    }
])

dump_tables_to_sql(
    {
        "ai_report": ai_report_database_df,
    },
    SEED_INTERPRET_SQL,
    snapshot_date,
)

print(f"File SQL Seed Interpretasi berhasil dibuat : {SEED_INTERPRET_SQL}")
print(f"Total Baris Tabel AI Report                : {len(ai_report_database_df)}")
