import pyodbc
import psycopg2
from psycopg2.extras import execute_batch
import logging
import re
from datetime import datetime

# ==========================================
# 1. Configuration & Setup
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

MSSQL_CONN_STR = "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=source_db;UID=sa;PWD=YourPassword!"
PG_CONN_STR = "host=localhost port=5432 dbname=target_db user=postgres password=YourPassword"

# ==========================================
# 2. Data Type Handling & Normalization
# ==========================================
def handle_datetimeoffset(dto_val):
    """
    Safely converts DATETIMEOFFSET for PostgreSQL, handling the 7 vs 6 fractional seconds issue.
    """
    if dto_val is None:
        return None
        
    # If returned as a string: 'YYYY-MM-DD HH:MM:SS.nnnnnnn +TZ'
    if isinstance(dto_val, str):
        # Truncate 7-digit precision down to 6-digit (microseconds) supported by PostgreSQL
        return re.sub(r'(\.\d{6})\d', r'\1', dto_val)
        
    # If pyodbc successfully maps it to an aware datetime object
    if isinstance(dto_val, datetime):
        return dto_val
        
    # Fallback
    return str(dto_val)

def normalize_row(row):
    """
    Normalizes a pyodbc Row into a standard tuple, fixing datatype mismatches.
    """
    return (
        int(row.Id),
        bool(row.FLAG) if row.FLAG is not None else None,
        str(row.Name) if row.Name is not None else None,
        row.CreatedAt,
        row.UpdatedAt,
        handle_datetimeoffset(row.TimeZoneValue)
    )

# ==========================================
# 3. Migration Verification (Count Match)
# ==========================================
def verify_migration(ms_conn, pg_conn, table_name):
    ms_cur = ms_conn.cursor()
    ms_cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    source_count = ms_cur.fetchone()[0]
    
    pg_cur = pg_conn.cursor()
    pg_cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    target_count = pg_cur.fetchone()[0]
    
    logging.info("=== Migration Verification ===")
    logging.info(f"Source MSSQL Rows: {source_count}")
    logging.info(f"Target PostgreSQL Rows: {target_count}")
    
    if source_count == target_count:
        logging.info("SUCCESS: Row counts match perfectly.")
    else:
        logging.error(f"DISCREPANCY DETECTED: Missing {source_count - target_count} rows.")

# ==========================================
# 4. Core Migration Logic
# ==========================================
def run_migration():
    ms_conn = None
    pg_conn = None
    
    try:
        # Connect to both databases
        logging.info("Connecting to databases...")
        ms_conn = pyodbc.connect(MSSQL_CONN_STR)
        pg_conn = psycopg2.connect(PG_CONN_STR)
        
        ms_cur = ms_conn.cursor()
        pg_cur = pg_conn.cursor()

        # Step 1: Ensure Target Schema Exists
        ddl = """
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER NOT NULL PRIMARY KEY,
                flag BOOLEAN,
                name VARCHAR(100),
                createdat TIMESTAMP WITHOUT TIME ZONE,
                updatedat TIMESTAMP WITHOUT TIME ZONE,
                timezonevalue TIMESTAMPTZ
            );
        """
        pg_cur.execute(ddl)
        pg_conn.commit()
        logging.info("Target schema verified/created.")

        # Step 2: Fetch Data
        query = "SELECT Id, FLAG, Name, CreatedAt, UpdatedAt, TimeZoneValue FROM test;"
        ms_cur.execute(query)
        
        insert_query = """
            INSERT INTO test (id, flag, name, createdat, updatedat, timezonevalue)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """

        batch_size = 1000
        batch_data = []
        total_inserted = 0

        logging.info("Starting data extraction and load...")
        
        while True:
            rows = ms_cur.fetchmany(batch_size)
            if not rows:
                break
                
            logging.info(f"Fetched chunk of {len(rows)} rows from MSSQL.")
            
            # Normalize chunk
            batch_data = [normalize_row(r) for r in rows]

            try:
                # Attempt fast batch insert
                execute_batch(pg_cur, insert_query, batch_data)
                pg_conn.commit() # CRITICAL: Commit the batch!
                total_inserted += len(batch_data)
                logging.info(f"Successfully inserted batch of {len(batch_data)} rows. Total: {total_inserted}")
                
            except Exception as batch_err:
                # BATCH FAILED. Enter Row-Level Debugging Fallback
                pg_conn.rollback() # CRITICAL: Reset aborted transaction state
                logging.warning(f"Batch insert failed! Entering row-by-row debugging mode. Error: {batch_err}")
                
                for row_vals in batch_data:
                    try:
                        pg_cur.execute(insert_query, row_vals)
                        pg_conn.commit()
                        total_inserted += 1
                    except Exception as row_err:
                        pg_conn.rollback()
                        logging.error("--- INSERT FAILED ---")
                        logging.error(f"Error: {row_err}")
                        logging.error(f"Failed Row Values: {row_vals}")
                        logging.error("---------------------")

        logging.info(f"Data streaming complete. Total inserted rows: {total_inserted}")
        
        # Step 3: Verification
        verify_migration(ms_conn, pg_conn, "test")

    except Exception as e:
        logging.error("CRITICAL MIGRATION FAILURE", exc_info=True)
    finally:
        if ms_conn: ms_conn.close()
        if pg_conn: pg_conn.close()
        logging.info("Connections closed.")

if __name__ == "__main__":
    run_migration()
