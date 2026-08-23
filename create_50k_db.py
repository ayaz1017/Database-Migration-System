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

DB_NAME = "db_50k"
TARGET_ROWS = 50_000

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def main():
    print(f"Connecting to MySQL at {DB_CONFIG['host']}...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 1. Create Database
    print(f"Creating database {DB_NAME}...")
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")
    
    # 2. Create Tables
    print("Creating tables...")
    cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)

    cursor.execute("""
        CREATE TABLE orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
    """)
    
    # 3. Create a View
    print("Creating view...")
    cursor.execute("""
        CREATE VIEW active_users_orders AS
        SELECT u.id AS user_id, u.username, u.email, o.id AS order_id, o.amount
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
    """)

    # 4. Create a Trigger
    print("Creating trigger...")
    # This trigger will automatically uppercase the username before insert
    cursor.execute("""
        CREATE TRIGGER before_user_insert
        BEFORE INSERT ON users
        FOR EACH ROW
        BEGIN
            SET NEW.username = UPPER(NEW.username);
        END
    """)

    # 5. Create a Stored Procedure
    print("Creating stored procedure...")
    cursor.execute("""
        CREATE PROCEDURE get_user_total_spent(IN p_user_id INT, OUT p_total DECIMAL(10,2))
        BEGIN
            SELECT SUM(amount) INTO p_total FROM orders WHERE user_id = p_user_id;
        END
    """)
    
    # 6. Insert Data (50,000 records)
    print("Inserting 50,000 records...")
    
    # Disable checks for faster insertion
    cursor.execute("SET unique_checks=0")
    cursor.execute("SET foreign_key_checks=0")
    
    # Insert seed data for users (1,000 rows)
    insert_user_query = "INSERT INTO users (username, email, status) VALUES (%s, %s, %s)"
    user_seed_data = [
        (random_string(8), f"{random_string(5)}@example.com", random.choice(['active', 'inactive']))
        for _ in range(1000)
    ]
    cursor.executemany(insert_user_query, user_seed_data)
    conn.commit()
    
    # Exponential doubling for users until 50k
    current_users = 1000
    while current_users < TARGET_ROWS:
        limit = min(current_users, TARGET_ROWS - current_users)
        cursor.execute(f"""
            INSERT INTO users (username, email, status)
            SELECT username, email, status FROM users LIMIT {limit}
        """)
        conn.commit()
        current_users += limit
    
    print(f"Users table filled with {current_users} rows.")

    # Insert seed data for orders (1,000 rows)
    insert_order_query = "INSERT INTO orders (user_id, amount) VALUES (%s, %s)"
    order_seed_data = [
        (random.randint(1, TARGET_ROWS), round(random.uniform(10.0, 500.0), 2))
        for _ in range(1000)
    ]
    cursor.executemany(insert_order_query, order_seed_data)
    conn.commit()

    # Exponential doubling for orders until 50k
    current_orders = 1000
    while current_orders < TARGET_ROWS:
        limit = min(current_orders, TARGET_ROWS - current_orders)
        # We need random user_ids, so we'll just insert from Python or use a SQL trick.
        # Actually doing executemany in chunks of 10,000 is fast enough for 50k.
        batch_size = min(10000, TARGET_ROWS - current_orders)
        batch_data = [
            (random.randint(1, TARGET_ROWS), round(random.uniform(10.0, 500.0), 2))
            for _ in range(batch_size)
        ]
        cursor.executemany(insert_order_query, batch_data)
        conn.commit()
        current_orders += batch_size

    print(f"Orders table filled with {current_orders} rows.")

    cursor.execute("SET unique_checks=1")
    cursor.execute("SET foreign_key_checks=1")
    
    print("Database creation and population complete.")
    conn.close()

if __name__ == "__main__":
    main()
