import mysql.connector
import random
import string
import time
import json
import uuid
import sys
import io

# Ensure UTF-8 output for console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Ayaz@123",
    "port": 3306
}

DB_NAME = "enterprise_1m_db"

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def main():
    total_start_time = time.time()
    print(f"Connecting to MySQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 1. Create Database
    print(f"Creating database '{DB_NAME}'...")
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")

    # Disable checks for super fast bulk insertion
    cursor.execute("SET unique_checks=0")
    cursor.execute("SET foreign_key_checks=0")
    cursor.execute("SET sql_log_bin=0")  # Speeds up local inserts if binary logging is on

    print("\n--- 1. CREATING TABLES WITH COMPLEX DATA TYPES ---")
    
    # Table 1: users (~200,000 rows)
    cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            uuid_col CHAR(36) NOT NULL,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(150),
            role ENUM('admin', 'customer', 'vendor', 'support') DEFAULT 'customer',
            account_balance DECIMAL(12, 4),
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            profile_data JSON,
            bio LONGTEXT
        ) ENGINE=InnoDB
    """)

    # Table 2: products (~50,000 rows)
    cursor.execute("""
        CREATE TABLE products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sku VARCHAR(64) NOT NULL,
            name VARCHAR(200) NOT NULL,
            category VARCHAR(100),
            price DECIMAL(10, 2),
            stock_quantity INT DEFAULT 0,
            attributes JSON,
            is_available BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)

    # Table 3: orders (~500,000 rows)
    cursor.execute("""
        CREATE TABLE orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_uuid CHAR(36) NOT NULL,
            user_id INT,
            total_amount DECIMAL(12, 2),
            status ENUM('pending', 'processing', 'completed', 'cancelled') DEFAULT 'pending',
            order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            shipping_address LONGTEXT,
            payment_info JSON
        ) ENGINE=InnoDB
    """)

    # Table 4: order_items (~250,000 rows)
    cursor.execute("""
        CREATE TABLE order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT,
            product_id INT,
            quantity INT,
            unit_price DECIMAL(10, 2),
            subtotal DECIMAL(12, 2)
        ) ENGINE=InnoDB
    """)

    # Table 5: audit_logs (will receive trigger generated logs)
    cursor.execute("""
        CREATE TABLE audit_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            entity_type VARCHAR(50),
            entity_id INT,
            action VARCHAR(100),
            log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)

    print("Tables created successfully.")

    # Helper function for exponential doubling
    def populate_table(table_name, target_rows, seed_insert_query, seed_data_generator, select_double_query):
        print(f"\nPopulating '{table_name}' (Target: {target_rows:,} rows)...")
        start_t = time.time()
        
        # Insert initial 1,000 seed rows
        seed_rows = [seed_data_generator() for _ in range(1000)]
        cursor.executemany(seed_insert_query, seed_rows)
        conn.commit()
        
        current_rows = 1000
        iteration = 1
        while current_rows < target_rows:
            t0 = time.time()
            limit = min(current_rows, target_rows - current_rows)
            cursor.execute(select_double_query.format(limit=limit))
            conn.commit()
            inserted = cursor.rowcount
            current_rows += inserted
            print(f"  [{table_name}] Iteration {iteration}: Added {inserted:,} -> Total {current_rows:,} ({time.time()-t0:.2f}s)")
            iteration += 1
        print(f"[SUCCESS] Finished '{table_name}' with {current_rows:,} rows in {time.time()-start_t:.2f}s.")

    # Populate Users (200,000 rows)
    roles = ['admin', 'customer', 'vendor', 'support']
    populate_table(
        table_name="users",
        target_rows=200_000,
        seed_insert_query="INSERT INTO users (uuid_col, username, email, role, account_balance, is_active, profile_data, bio) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            str(uuid.uuid4()),
            f"user_{random_string(8)}",
            f"{random_string(6)}@example.com",
            random.choice(roles),
            round(random.uniform(0.0, 10000.0), 4),
            random.choice([True, True, True, False]),
            json.dumps({"theme": random.choice(["dark", "light"]), "notifications": True}),
            "User biography and long text content " * 5
        ),
        select_double_query="""
            INSERT INTO users (uuid_col, username, email, role, account_balance, is_active, profile_data, bio)
            SELECT UUID(), CONCAT(username, '_', SUBSTRING(MD5(RAND()), 1, 4)), email, role, account_balance + RAND(), is_active, profile_data, bio
            FROM users LIMIT {limit}
        """
    )

    # Populate Products (50,000 rows)
    categories = ['Electronics', 'Books', 'Clothing', 'Home', 'Toys', 'Sports']
    populate_table(
        table_name="products",
        target_rows=50_000,
        seed_insert_query="INSERT INTO products (sku, name, category, price, stock_quantity, attributes, is_available) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            f"SKU-{random_string(8).upper()}",
            f"Product {random_string(10)}",
            random.choice(categories),
            round(random.uniform(5.0, 2000.0), 2),
            random.randint(0, 1000),
            json.dumps({"color": random.choice(["Red", "Blue", "Black", "White"]), "weight": random.randint(1, 10)}),
            random.choice([True, True, False])
        ),
        select_double_query="""
            INSERT INTO products (sku, name, category, price, stock_quantity, attributes, is_available)
            SELECT CONCAT('SKU-', SUBSTRING(MD5(RAND()), 1, 8)), CONCAT(name, ' V2'), category, price + (RAND() * 10), stock_quantity, attributes, is_available
            FROM products LIMIT {limit}
        """
    )

    # Populate Orders (500,000 rows)
    statuses = ['pending', 'processing', 'completed', 'cancelled']
    populate_table(
        table_name="orders",
        target_rows=500_000,
        seed_insert_query="INSERT INTO orders (order_uuid, user_id, total_amount, status, shipping_address, payment_info) VALUES (%s, %s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            str(uuid.uuid4()),
            random.randint(1, 200_000),
            round(random.uniform(15.0, 5000.0), 2),
            random.choice(statuses),
            f"{random.randint(100, 9999)} Main St, City {random_string(5)}, Country",
            json.dumps({"method": random.choice(["credit_card", "paypal", "crypto"]), "verified": True})
        ),
        select_double_query="""
            INSERT INTO orders (order_uuid, user_id, total_amount, status, shipping_address, payment_info)
            SELECT UUID(), FLOOR(1 + (RAND() * 199999)), total_amount + (RAND() * 5), status, shipping_address, payment_info
            FROM orders LIMIT {limit}
        """
    )

    # Populate Order Items (250,000 rows)
    populate_table(
        table_name="order_items",
        target_rows=250_000,
        seed_insert_query="INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES (%s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            random.randint(1, 500_000),
            random.randint(1, 50_000),
            random.randint(1, 10),
            round(random.uniform(10.0, 500.0), 2),
            round(random.uniform(10.0, 5000.0), 2)
        ),
        select_double_query="""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
            SELECT FLOOR(1 + (RAND() * 499999)), FLOOR(1 + (RAND() * 49999)), quantity, unit_price, unit_price * quantity
            FROM order_items LIMIT {limit}
        """
    )

    # Re-enable database checks
    cursor.execute("SET unique_checks=1")
    cursor.execute("SET foreign_key_checks=1")

    print("\n--- 2. CREATING VIEWS ---")
    cursor.execute("""
        CREATE VIEW active_users_view AS
        SELECT id, uuid_col, username, email, role, account_balance, created_at
        FROM users
        WHERE is_active = TRUE
    """)
    print("  Created VIEW: active_users_view")

    cursor.execute("""
        CREATE VIEW completed_orders_summary_view AS
        SELECT id, order_uuid, user_id, total_amount, order_date
        FROM orders
        WHERE status = 'completed'
    """)
    print("  Created VIEW: completed_orders_summary_view")

    cursor.execute("""
        CREATE VIEW high_value_products_view AS
        SELECT id, sku, name, category, price, stock_quantity
        FROM products
        WHERE price > 500.00 AND is_available = TRUE
    """)
    print("  Created VIEW: high_value_products_view")

    print("\n--- 3. CREATING TRIGGERS ---")
    cursor.execute("""
        CREATE TRIGGER after_user_insert
        AFTER INSERT ON users
        FOR EACH ROW
        BEGIN
            INSERT INTO audit_logs (entity_type, entity_id, action)
            VALUES ('USER', NEW.id, 'USER_CREATED');
        END;
    """)
    print("  Created TRIGGER: after_user_insert")

    cursor.execute("""
        CREATE TRIGGER after_order_update
        AFTER UPDATE ON orders
        FOR EACH ROW
        BEGIN
            IF OLD.status != NEW.status THEN
                INSERT INTO audit_logs (entity_type, entity_id, action)
                VALUES ('ORDER', NEW.id, CONCAT('STATUS_CHANGED_TO_', NEW.status));
            END IF;
        END;
    """)
    print("  Created TRIGGER: after_order_update")

    print("\n--- 4. CREATING STORED PROCEDURES ---")
    cursor.execute("""
        CREATE PROCEDURE update_order_status(IN p_order_id INT, IN p_status VARCHAR(20))
        BEGIN
            UPDATE orders SET status = p_status WHERE id = p_order_id;
        END;
    """)
    print("  Created PROCEDURE: update_order_status")

    cursor.execute("""
        CREATE PROCEDURE get_user_stats(IN p_user_id INT, OUT p_total_orders INT, OUT p_total_spent DECIMAL(12, 2))
        BEGIN
            SELECT COUNT(*), COALESCE(SUM(total_amount), 0.00) 
            INTO p_total_orders, p_total_spent
            FROM orders
            WHERE user_id = p_user_id AND status = 'completed';
        END;
    """)
    print("  Created PROCEDURE: get_user_stats")

    print("\n--- 5. TESTING TRIGGERS AND PROCEDURES ---")
    print("Testing TRIGGER by inserting 1 new user...")
    cursor.execute("INSERT INTO users (uuid_col, username, email, role) VALUES (%s, %s, %s, %s)",
                   (str(uuid.uuid4()), "trigger_test_user", "trigger@test.com", "customer"))
    conn.commit()

    print("Testing STORED PROCEDURE by calling update_order_status(1, 'completed')...")
    cursor.execute("CALL update_order_status(1, 'completed')")
    conn.commit()

    # Check audit logs generated by trigger
    cursor.execute("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 5")
    logs = cursor.fetchall()
    print(f"Audit Logs count: {len(logs)} (Sample: {logs[0] if logs else 'None'})")

    # Verify total row count across all tables
    print("\n--- SUMMARY REPORT ---")
    total_rows = 0
    for tbl in ["users", "products", "orders", "order_items", "audit_logs"]:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cursor.fetchone()[0]
        total_rows += cnt
        print(f"  Table '{tbl}': {cnt:,} rows")
    
    print(f"\n[SUCCESS] Created database '{DB_NAME}' with a total of {total_rows:,} rows across multiple tables, views, triggers, and stored procedures!")
    print(f"Total time elapsed: {time.time() - total_start_time:.2f} seconds.")

    conn.close()

if __name__ == "__main__":
    main()
