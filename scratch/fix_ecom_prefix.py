import sqlite3, json, re

DB_FILE = 'migrations.db'
JOB_ID = 'mig_1782888879177'

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("SELECT full_payload FROM migration_jobs WHERE id = ?", (JOB_ID,))
row = cursor.fetchone()
payload = json.loads(row[0])

translations = payload['object_translations']

changed = []
for t in translations:
    name = t['object_name']
    td = t.get('translated_definition', '')
    
    if not td:
        continue
    
    # Strip all variations of ecom_sample. prefix:
    #   "ecom_sample"."table"  -> "table"
    #   "ecom_sample".         -> (removed)
    #   ecom_sample.           -> (removed)
    new_td = td
    
    # Pattern 1: "ecom_sample"."identifier" -> "identifier"
    new_td = re.sub(r'"ecom_sample"\s*\.\s*', '', new_td)
    
    # Pattern 2: ecom_sample.identifier (unquoted) -> identifier
    new_td = re.sub(r'\becom_sample\s*\.\s*', '', new_td)
    
    if new_td != td:
        print(f"\n=== CHANGED: {name} ===")
        print(f"BEFORE:\n{td}")
        print(f"\nAFTER:\n{new_td}")
        t['translated_definition'] = new_td
        changed.append(name)
    else:
        print(f"  {name}: no ecom_sample references found, unchanged")

if changed:
    payload['object_translations'] = translations
    cursor.execute("""
        UPDATE migration_jobs 
        SET full_payload = ?
        WHERE id = ?
    """, (json.dumps(payload), JOB_ID))
    conn.commit()
    print(f"\n✅ Updated {len(changed)} object(s) in job {JOB_ID}: {changed}")
else:
    print("\nNo changes needed.")

conn.close()
