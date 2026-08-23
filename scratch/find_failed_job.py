import sqlite3
import json

conn = sqlite3.connect("migrations.db")
cursor = conn.cursor()
cursor.execute("SELECT id, status, full_payload FROM migration_jobs WHERE status = 'FAILED' OR status = 'failed'")
rows = cursor.fetchall()
conn.close()

for r in rows:
    job_id, status, payload_str = r
    try:
        payload = json.loads(payload_str)
        error = payload.get("error", "No error field")
        print(f"Job: {job_id} | Error: {error}")
    except Exception as e:
        print(f"Error parsing payload for {job_id}: {e}")
