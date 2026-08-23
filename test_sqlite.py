import sqlite3
import json
conn = sqlite3.connect('migrations.db')
cursor = conn.cursor()
cursor.execute("SELECT source_db, target_db, full_payload, tables_migrated, rows_migrated FROM migration_jobs ORDER BY timestamp DESC LIMIT 3")
for row in cursor.fetchall():
    payload = json.loads(row[2])
    print('SOURCE:', row[0], 'TARGET:', row[1], 'TABLES:', row[3], 'ROWS:', row[4])
    if payload.get('validation_report', {}).get('error'):
        print('Validation Error:', payload['validation_report']['error'])
    else:
        for t in payload.get('validation_report', {}).get('tables', []):
            print(f"Table {t['table']}: target_rows={t.get('target_row_count')}, source_rows={t.get('source_row_count')}")
conn.close()
