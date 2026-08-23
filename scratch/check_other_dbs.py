import sqlite3, json

# Check backend/migrations.db too
for db_path in ['backend/migrations.db']:
    print(f"\n=== Checking {db_path} ===")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_payload FROM migration_jobs")
    rows = cursor.fetchall()
    for row in rows:
        job_id = row[0]
        payload = json.loads(row[1]) if row[1] else None
        if payload and 'object_translations' in payload:
            translations = payload['object_translations']
            has_ecom = any('ecom_sample' in t.get('translated_definition', '') 
                          for t in translations 
                          if not all(line.strip().startswith('--') for line in t.get('translated_definition', '').split('\n') if 'ecom_sample' in line))
            if has_ecom:
                print(f"  Job {job_id}: HAS ecom_sample in SQL")
            else:
                print(f"  Job {job_id}: {len(translations)} translations, clean")
    conn.close()
