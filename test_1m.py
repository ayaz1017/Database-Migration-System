import mysql.connector
import time
import random
import string

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ayaz@123",
    "port": 3306
}

def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS large_test_db")
    cursor.execute("USE large_test_db")
    for tname in ["test_1m_a", "test_1m_b"]:
        cursor.execute(f"DROP TABLE IF EXISTS {tname}")
        cursor.execute(f"""
            CREATE TABLE {tname} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                val VARCHAR(255)
            )
        """)
        print(f"Inserting 1000 rows into {tname}...")
        data = [(f"val_{i}",) for i in range(1000)]
        cursor.executemany(f"INSERT INTO {tname} (val) VALUES (%s)", data)
        conn.commit()

        rows = 1000
        while rows < 1000000:
            cursor.execute(f"INSERT INTO {tname} (val) SELECT val FROM {tname}")
            conn.commit()
            rows += cursor.rowcount
            print(f"Rows now: {rows}")

    print("Done generating 1M rows.")
    conn.close()

if __name__ == "__main__":
    main()
