import sqlite3, json, re

DB_FILE = 'migrations.db'

# Fix all jobs that have ecom_sample in translated_definitions
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("SELECT id, full_payload FROM migration_jobs")
rows = cursor.fetchall()

for row in rows:
    job_id = row[0]
    payload = json.loads(row[1]) if row[1] else None
    if not payload or 'object_translations' not in payload:
        continue
    
    translations = payload['object_translations']
    job_changed = False
    
    for t in translations:
        td = t.get('translated_definition', '')
        if not td:
            continue
        
        new_td = td
        # Strip "ecom_sample". prefix (quoted)
        new_td = re.sub(r'"ecom_sample"\s*\.\s*', '', new_td)
        # Strip ecom_sample. prefix (unquoted)
        new_td = re.sub(r'\becom_sample\s*\.\s*', '', new_td)
        
        if new_td != td:
            t['translated_definition'] = new_td
            job_changed = True
            print(f"  Fixed {t['object_name']} in job {job_id}")
    
    if job_changed:
        payload['object_translations'] = translations
        cursor.execute("UPDATE migration_jobs SET full_payload = ? WHERE id = ?",
                       (json.dumps(payload), job_id))
        conn.commit()
        print(f"  -> Saved job {job_id}")

print("\nDone - all jobs checked and fixed.")
conn.close()
