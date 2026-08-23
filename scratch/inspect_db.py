import sqlite3, json

conn = sqlite3.connect('migrations.db')
cursor = conn.cursor()

cursor.execute("SELECT full_payload FROM migration_jobs WHERE id='mig_1782888879177'")
row = cursor.fetchone()
payload = json.loads(row[0])

translations = payload['object_translations']
for t in translations:
    name = t.get('object_name', '?')
    td = t.get('translated_definition', '')
    sd = t.get('source_definition', '')
    print(f"\n{'='*60}")
    print(f"=== {name} ({t.get('object_type','?')}) ===")
    print(f"Status: {t.get('status', 'N/A')}")
    print(f"Compile status: {t.get('compile_status', 'N/A')}")
    print(f"Contains 'ecom_sample' in translated: {'ecom_sample' in td}")
    print(f"\n--- translated_definition ---")
    print(td if td else "(empty)")
    print(f"\n--- source_definition ---")
    print(sd[:500] if sd else "(empty)")

conn.close()
