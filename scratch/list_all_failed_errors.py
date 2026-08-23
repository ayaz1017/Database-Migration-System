import sqlite3
import json

conn = sqlite3.connect("migrations.db")
cursor = conn.cursor()
cursor.execute("SELECT id, status, full_payload FROM migration_jobs")
rows = cursor.fetchall()
conn.close()

failed_errors = {}
for r in rows:
    job_id, status, payload_str = r
    if "FAIL" in status.upper():
        try:
            payload = json.loads(payload_str)
            error = payload.get("error", "No error message")
            failed_errors[job_id] = (status, error)
        except Exception as e:
            failed_errors[job_id] = (status, f"Error parsing: {payload_str}")

count = 0
for job_id in sorted(failed_errors.keys(), reverse=True):
    if count >= 35:
        break
    status, error = failed_errors[job_id]
    # Truncate error if too long
    err_snippet = error if len(error) < 150 else error[:150] + "..."
    print(f"{count+1:02d}. Job: {job_id} | Status: {status} | Error: {err_snippet}")
    count += 1
