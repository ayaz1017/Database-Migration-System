import sqlite3
import json
conn = sqlite3.connect('migrations.db')
cursor = conn.cursor()
cursor.execute("SELECT timestamp, source_db, target_db, tables_migrated, rows_migrated FROM migration_jobs ORDER BY timestamp DESC LIMIT 5")
for row in cursor.fetchall():
    print(row)
conn.close()
