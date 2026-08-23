import pyodbc
import psycopg2
from psycopg2.extras import execute_batch
import traceback
import sys

MSSQL_CONN = "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=source_db;UID=sa;PWD=pass"
PG_CONN = "host=localhost port=5432 dbname=target_db user=postgres password=pass"

def run_instrumented_migration():
    try:
        ms_conn = pyodbc.connect(MSSQL_CONN)
        pg_conn = psycopg2.connect(PG_CONN)
        ms_cur = ms_conn.cursor()
        pg_cur = pg_conn.cursor()

        # Step 8: Source Count
        ms_cur.execute("SELECT COUNT(*) FROM test;")
        source_count = ms_cur.fetchone()[0]
        print(f"Source count: {source_count}")

        # Step 1: Verify Extraction
        ms_cur.execute("SELECT Id, FLAG, Name, CreatedAt, UpdatedAt, TimeZoneValue FROM test;")
        rows = ms_cur.fetchall()
        print("Rows fetched:", len(rows))
        
        print("\n--- First 10 Rows & Types ---")
        for r in rows[:10]:
            print("Row:", r)
            print("Type of TimeZoneValue:", type(r.TimeZoneValue))
            print("Type of CreatedAt:", type(r.CreatedAt))

        # Prepare Batch
        insert_query = """
            INSERT INTO test (id, flag, name, createdat, updatedat, timezonevalue)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        batch_data = [(r.Id, r.FLAG, r.Name, r.CreatedAt, r.UpdatedAt, r.TimeZoneValue) for r in rows]

        # Step 3: Transaction State
        print(f"\npg_conn.autocommit is: {pg_conn.autocommit}")

        inserted_count = 0
        failed_count = 0
        skipped_count = 0

        # Step 6: Batch Diagnosis
        try:
            print(f"\nAttempting execute_batch with {len(batch_data)} rows...")
            execute_batch(pg_cur, insert_query, batch_data)
            pg_conn.commit()
            print("pg_conn.commit() executed for batch")
            inserted_count += len(batch_data)
        except Exception as batch_e:
            pg_conn.rollback()
            print("pg_conn.rollback() executed for batch")
            print("Batch failed. Falling back to row-by-row debugging...\n")
            
            for row in batch_data:
                try:
                    # Step 2: Verify insertion per row
                    print("Insert values:", row)
                    pg_cur.execute(insert_query, row)
                    inserted_count += pg_cur.rowcount
                    pg_conn.commit()
                    print("pg_conn.commit() executed for row")
                except Exception as e:
                    pg_conn.rollback()
                    print("pg_conn.rollback() executed for row")
                    failed_count += 1
                    
                    # Step 4: Capture ALL exceptions
                    print("\n!!! INSERT FAILED !!!")
                    print(traceback.format_exc())
                    
                    # Step 5: Datatype Proof
                    print("Offending values:", row)
                    print("TimeZoneValue representation:", repr(row[5]))
                    print("TimeZoneValue type:", type(row[5]))
                    
                    if hasattr(e, 'pgcode'):
                        print("SQLSTATE:", e.pgcode)

        # Step 8: Compare Counts
        pg_cur.execute("SELECT COUNT(*) FROM test;")
        target_count = pg_cur.fetchone()[0]
        
        print("\n--- Final Verification ---")
        print(f"Source count: {source_count}")
        print(f"Inserted count: {inserted_count}")
        print(f"Failed count: {failed_count}")
        print(f"Skipped count: {skipped_count}")
        print(f"Target count: {target_count}")

    except Exception as fatal_e:
        print("Fatal Error:", traceback.format_exc())
    finally:
        if 'ms_conn' in locals(): ms_conn.close()
        if 'pg_conn' in locals(): pg_conn.close()

if __name__ == "__main__":
    run_instrumented_migration()
