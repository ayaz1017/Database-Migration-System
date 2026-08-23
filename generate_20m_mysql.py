import mysql.connector
import random
import string
import time

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ayaz@123",
    "port": 3306
}

DB_NAME = "large_test_db"
NUM_TABLES = 10
ROWS_PER_TABLE = 2_000_000

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def main():
    print(f"Connecting to MySQL at {DB_CONFIG['host']}...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Create Database
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")
    
    total_start = time.time()

    for i in range(1, NUM_TABLES + 1):
        table_name = f"table_{i}"
        print(f"\n--- Processing {table_name} ---")
        
        # 1. Create Table
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                status VARCHAR(50),
                created_at DATETIME,
                random_data VARCHAR(255)
            ) ENGINE=InnoDB
        """)
        
        # 2. Insert initial seed data (1,000 rows)
        print("Inserting 1,000 seed rows...")
        insert_query = f"INSERT INTO {table_name} (user_id, status, created_at, random_data) VALUES (%s, %s, NOW(), %s)"
        seed_data = [
            (random.randint(1, 10000), random.choice(['active', 'pending', 'inactive']), random_string(50))
            for _ in range(1000)
        ]
        
        # Disable foreign key checks & unique checks temporarily for speed
        cursor.execute("SET unique_checks=0")
        cursor.execute("SET foreign_key_checks=0")
        
        cursor.executemany(insert_query, seed_data)
        conn.commit()

        # 3. Exponential row doubling (1,000 -> 2,000,000)
        # 11 iterations: 1k -> 2k -> 4k -> 8k -> 16k -> 32k -> 64k -> 128k -> 256k -> 512k -> 1.02M -> 2.04M
        print("Starting exponential row doubling (this is extremely fast)...")
        current_rows = 1000
        iteration = 1
        
        while current_rows < ROWS_PER_TABLE:
            start_time = time.time()
            cursor.execute(f"""
                INSERT INTO {table_name} (user_id, status, created_at, random_data)
                SELECT user_id, status, created_at, random_data FROM {table_name}
            """)
            conn.commit()
            
            inserted = cursor.rowcount
            current_rows += inserted
            elapsed = time.time() - start_time
            print(f"  Iteration {iteration}: Doubled to {current_rows:,} rows (took {elapsed:.2f}s)")
            iteration += 1

        cursor.execute("SET unique_checks=1")
        cursor.execute("SET foreign_key_checks=1")
        print(f"✅ Finished {table_name} with {current_rows:,} rows.")

    conn.close()
    print(f"\n🎉 Successfully created {NUM_TABLES} tables with ~{ROWS_PER_TABLE:,} rows each.")
    print(f"Total time elapsed: {time.time() - total_start:.2f} seconds.")

if __name__ == "__main__":
    main()
