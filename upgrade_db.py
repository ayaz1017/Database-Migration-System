import sqlite3
import json
import sys
import os

# Add backend to path so we can import utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
from utils import scrub_credentials

DB_PATH = 'data/fluxline.db'

def upgrade():
    print(f"Opening database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Fetch all jobs
    cursor.execute("SELECT id, full_payload FROM migration_jobs")
    rows = cursor.fetchall()
    
    updates = 0
    for row_id, payload_str in rows:
        if not payload_str:
            continue
            
        try:
            payload = json.loads(payload_str)
            # Scrub it
            scrubbed = scrub_credentials(payload)
            scrubbed_str = json.dumps(scrubbed)
            
            # If changed, update it
            if scrubbed_str != payload_str:
                cursor.execute("UPDATE migration_jobs SET full_payload = ? WHERE id = ?", (scrubbed_str, row_id))
                updates += 1
        except Exception as e:
            print(f"Failed to process job {row_id}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Database upgrade complete. Scrubbed credentials from {updates} jobs.")

if __name__ == '__main__':
    upgrade()
