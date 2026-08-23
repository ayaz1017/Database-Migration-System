import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ayaz@123",
    "port": 3306,
    "database": "db_50k"
}

def main():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("--- Database `db_50k` Verification ---")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\nTables/Views found: {[t[0] for t in tables]}")
        
        cursor.execute("SELECT COUNT(*) FROM users")
        print(f"Users table row count: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        print(f"Orders table row count: {cursor.fetchone()[0]}")
        
        cursor.execute("SHOW TRIGGERS")
        triggers = cursor.fetchall()
        print(f"\nTriggers found: {[t[0] for t in triggers]}")
        
        cursor.execute("SHOW PROCEDURE STATUS WHERE Db = 'db_50k'")
        procedures = cursor.fetchall()
        print(f"Stored Procedures found: {[p[1] for p in procedures]}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
