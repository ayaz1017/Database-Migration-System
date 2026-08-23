import mysql.connector
from faker import Faker
import random
import time
import argparse
import sys
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)
random.seed(42)

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'migrator',
    'password': 'Ayaz@123'
}

def create_database(cursor):
    cursor.execute("CREATE DATABASE IF NOT EXISTS stress_test_db")
    cursor.execute("USE stress_test_db")

def create_tables(cursor):
    tables = [
        """
        CREATE TABLE IF NOT EXISTS product_categories (
            category_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at DATETIME NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            category_id INT NOT NULL,
            name VARCHAR(255) NOT NULL,
            sku VARCHAR(50) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (category_id) REFERENCES product_categories(category_id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(50),
            status ENUM('ACTIVE', 'INACTIVE', 'SUSPENDED') DEFAULT 'ACTIVE',
            created_at DATETIME NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS addresses (
            address_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            address_line1 VARCHAR(255) NOT NULL,
            city VARCHAR(100) NOT NULL,
            state VARCHAR(100),
            zip_code VARCHAR(20) NOT NULL,
            country VARCHAR(100) NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            order_date DATETIME NOT NULL,
            total_amount DECIMAL(12,2) NOT NULL,
            status ENUM('PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED') DEFAULT 'PENDING',
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            order_id BIGINT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS payments (
            payment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            order_id BIGINT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            payment_date DATETIME NOT NULL,
            payment_method ENUM('CREDIT_CARD', 'PAYPAL', 'BANK_TRANSFER', 'CRYPTO'),
            status ENUM('SUCCESS', 'FAILED', 'PENDING', 'REFUNDED'),
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            product_id INT NOT NULL,
            rating TINYINT NOT NULL,
            review_text TEXT,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS inventory_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            quantity_changed INT NOT NULL,
            reason VARCHAR(255),
            logged_at DATETIME NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            audit_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT,
            action VARCHAR(255) NOT NULL,
            entity_type VARCHAR(100) NOT NULL,
            entity_id BIGINT,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
        )
        """
    ]
    
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    # Drop existing tables to ensure idempotent runs
    tables_to_drop = ['audit_logs', 'inventory_logs', 'reviews', 'payments', 'order_items', 'orders', 'addresses', 'customers', 'products', 'product_categories']
    for t in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {t}")
        
    for q in tables:
        cursor.execute(q)
    cursor.execute("SET FOREIGN_KEY_CHECKS=1")

def create_indexes(cursor):
    indexes = [
        "CREATE INDEX idx_category_name ON product_categories(name)",
        "CREATE INDEX idx_category_created ON product_categories(created_at)",
        "CREATE INDEX idx_product_sku ON products(sku)",
        "CREATE INDEX idx_product_category ON products(category_id)",
        "CREATE INDEX idx_customer_email ON customers(email)",
        "CREATE INDEX idx_customer_status ON customers(status)",
        "CREATE INDEX idx_address_customer ON addresses(customer_id)",
        "CREATE INDEX idx_address_city ON addresses(city)",
        "CREATE INDEX idx_order_customer ON orders(customer_id)",
        "CREATE INDEX idx_order_date ON orders(order_date)",
        "CREATE INDEX idx_order_item_order ON order_items(order_id)",
        "CREATE INDEX idx_order_item_product ON order_items(product_id)",
        "CREATE INDEX idx_payment_order ON payments(order_id)",
        "CREATE INDEX idx_payment_date ON payments(payment_date)",
        "CREATE INDEX idx_review_customer ON reviews(customer_id)",
        "CREATE INDEX idx_review_product ON reviews(product_id)",
        "CREATE INDEX idx_inventory_product ON inventory_logs(product_id)",
        "CREATE INDEX idx_inventory_date ON inventory_logs(logged_at)",
        "CREATE INDEX idx_audit_customer ON audit_logs(customer_id)",
        "CREATE INDEX idx_audit_action ON audit_logs(action)"
    ]
    print("\nCreating indexes...")
    for idx_q in indexes:
        cursor.execute(idx_q)

def insert_batch(cursor, table, columns, data):
    if not data: return
    col_str = ', '.join(columns)
    placeholders = '(' + ', '.join(['%s'] * len(columns)) + ')'
    query = f"INSERT INTO {table} ({col_str}) VALUES " + ', '.join([placeholders] * len(data))
    flat_data = [item for row in data for item in row]
    cursor.execute(query, flat_data)

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def generate_data(conn, cursor, scale_factor=1.0):
    base_counts = {
        'product_categories': 500,
        'products': 40000,
        'customers': 400000,
        'addresses': 600000,
        'orders': 4000000,
        'order_items': 10000000,
        'payments': 4000000,
        'reviews': 500000,
        'inventory_logs': 400000,
        'audit_logs': 59500
    }
    
    counts = {k: max(1, int(v * scale_factor)) for k, v in base_counts.items()}
    # Ensure realistic minimums for dry-run
    if counts['product_categories'] < 5: counts['product_categories'] = 5
    if counts['products'] < 10: counts['products'] = 10
    if counts['customers'] < 10: counts['customers'] = 10
    if counts['orders'] < 10: counts['orders'] = 10
    
    batch_size = 50000
    if scale_factor < 1.0:
        batch_size = 5000

    print("Generation Strategy:")
    for k, v in counts.items():
        print(f"  {k}: {v} rows")
        
    start_time_all = time.time()
    times = {}

    cursor.execute("SET autocommit=0")
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")

    # Fast data generation setup
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 12, 31)
    
    words = [fake.word() for _ in range(1000)]
    cities = [fake.city() for _ in range(100)]
    countries = [fake.country() for _ in range(50)]
    fnames = [fake.first_name() for _ in range(500)]
    lnames = [fake.last_name() for _ in range(500)]
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'example.com']

    # 1. product_categories
    start = time.time()
    table = 'product_categories'
    cols = ['name', 'description', 'created_at']
    batch = []
    for i in range(1, counts[table] + 1):
        batch.append((
            f"{random.choice(words)} {i}", 
            "Description for " + str(i), 
            random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S')
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    # 2. products
    start = time.time()
    table = 'products'
    cols = ['category_id', 'name', 'sku', 'price', 'is_active', 'created_at']
    batch = []
    for i in range(1, counts[table] + 1):
        batch.append((
            random.randint(1, counts['product_categories']),
            f"{random.choice(words)} {random.choice(words)} {i}",
            f"SKU-{random.randint(1000, 9999)}-{i}",
            round(random.uniform(10.0, 1000.0), 2),
            random.choice([0, 1]),
            random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S')
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
            if i % 500000 == 0:
                print(f"  {table}: {i} rows...", end='\r')
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    # 3. customers
    start = time.time()
    table = 'customers'
    cols = ['first_name', 'last_name', 'email', 'phone', 'status', 'created_at']
    batch = []
    statuses = ['ACTIVE', 'ACTIVE', 'ACTIVE', 'INACTIVE', 'SUSPENDED']
    for i in range(1, counts[table] + 1):
        fn = random.choice(fnames)
        ln = random.choice(lnames)
        batch.append((
            fn, ln,
            f"{fn.lower()}.{ln.lower()}{i}@{random.choice(domains)}",
            f"+1{random.randint(1000000000, 9999999999)}",
            random.choice(statuses),
            random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S')
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
            if i % 500000 == 0:
                print(f"  {table}: {i} rows... ({i/(time.time()-start):.0f} rows/sec)", end='\r')
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    # 4. addresses
    start = time.time()
    table = 'addresses'
    cols = ['customer_id', 'address_line1', 'city', 'state', 'zip_code', 'country', 'is_primary']
    batch = []
    for i in range(1, counts[table] + 1):
        batch.append((
            random.randint(1, counts['customers']),
            f"{random.randint(100, 9999)} {random.choice(words).title()} St",
            random.choice(cities),
            random.choice(words)[:2].upper(),
            f"{random.randint(10000, 99999)}",
            random.choice(countries),
            random.choice([0, 1])
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
            if i % 500000 == 0:
                print(f"  {table}: {i} rows... ({i/(time.time()-start):.0f} rows/sec)", end='\r')
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    # 5. orders
    start = time.time()
    table = 'orders'
    cols = ['customer_id', 'order_date', 'total_amount', 'status']
    batch = []
    order_statuses = ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'DELIVERED', 'CANCELLED']
    for i in range(1, counts[table] + 1):
        batch.append((
            random.randint(1, counts['customers']),
            random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S'),
            round(random.uniform(20.0, 5000.0), 2),
            random.choice(order_statuses)
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
            if i % 500000 == 0:
                print(f"  {table}: {i} rows... ({i/(time.time()-start):.0f} rows/sec)", end='\r')
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    # 6. order_items
    start = time.time()
    table = 'order_items'
    cols = ['order_id', 'product_id', 'quantity', 'unit_price']
    batch = []
    for i in range(1, counts[table] + 1):
        batch.append((
            random.randint(1, counts['orders']),
            random.randint(1, counts['products']),
            random.randint(1, 5),
            round(random.uniform(10.0, 500.0), 2)
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
            if i % 500000 == 0:
                print(f"  {table}: {i} rows... ({i/(time.time()-start):.0f} rows/sec)", end='\r')
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    # 7. payments
    start = time.time()
    table = 'payments'
    cols = ['order_id', 'amount', 'payment_date', 'payment_method', 'status']
    batch = []
    payment_methods = ['CREDIT_CARD', 'PAYPAL', 'BANK_TRANSFER', 'CRYPTO']
    payment_statuses = ['SUCCESS', 'SUCCESS', 'FAILED', 'PENDING', 'REFUNDED']
    for i in range(1, counts[table] + 1):
        batch.append((
            random.randint(1, counts['orders']),
            round(random.uniform(20.0, 5000.0), 2),
            random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S'),
            random.choice(payment_methods),
            random.choice(payment_statuses)
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
            if i % 500000 == 0:
                print(f"  {table}: {i} rows... ({i/(time.time()-start):.0f} rows/sec)", end='\r')
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    # 8. reviews
    start = time.time()
    table = 'reviews'
    cols = ['customer_id', 'product_id', 'rating', 'review_text', 'created_at']
    batch = []
    for i in range(1, counts[table] + 1):
        batch.append((
            random.randint(1, counts['customers']),
            random.randint(1, counts['products']),
            random.randint(1, 5),
            f"{random.choice(words)} {random.choice(words)}",
            random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S')
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
            if i % 500000 == 0:
                print(f"  {table}: {i} rows... ({i/(time.time()-start):.0f} rows/sec)", end='\r')
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    # 9. inventory_logs
    start = time.time()
    table = 'inventory_logs'
    cols = ['product_id', 'quantity_changed', 'reason', 'logged_at']
    batch = []
    for i in range(1, counts[table] + 1):
        batch.append((
            random.randint(1, counts['products']),
            random.randint(-50, 50),
            random.choice(['Restock', 'Sale', 'Return', 'Damage']),
            random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S')
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
            if i % 500000 == 0:
                print(f"  {table}: {i} rows... ({i/(time.time()-start):.0f} rows/sec)", end='\r')
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    # 10. audit_logs
    start = time.time()
    table = 'audit_logs'
    cols = ['customer_id', 'action', 'entity_type', 'entity_id', 'created_at']
    batch = []
    for i in range(1, counts[table] + 1):
        batch.append((
            random.randint(1, counts['customers']),
            random.choice(['LOGIN', 'LOGOUT', 'UPDATE_PROFILE', 'VIEW_ITEM']),
            random.choice(['User', 'Order', 'Product']),
            random.randint(1, 10000),
            random_date(start_date, end_date).strftime('%Y-%m-%d %H:%M:%S')
        ))
        if len(batch) >= batch_size:
            insert_batch(cursor, table, cols, batch)
            conn.commit()
            batch = []
            if i % 500000 == 0:
                print(f"  {table}: {i} rows... ({i/(time.time()-start):.0f} rows/sec)", end='\r')
    if batch:
        insert_batch(cursor, table, cols, batch)
        conn.commit()
    times[table] = time.time() - start
    print(f"Loaded {counts[table]} {table} in {times[table]:.2f}s")

    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    conn.commit()
    
    print(f"\nAll data inserted in {time.time() - start_time_all:.2f}s")
    
    # Analyze tables
    for table in counts.keys():
        cursor.execute(f"ANALYZE TABLE {table}")
        cursor.fetchall()
        
    print("\nSummary:")
    print(f"{'Table':<20} | {'Rows':<10} | {'Time (s)':<10}")
    print("-" * 45)
    for t in counts.keys():
        print(f"{t:<20} | {counts[t]:<10} | {times[t]:<10.2f}")

def main():
    parser = argparse.ArgumentParser(description="Generate 20M row test data")
    parser.add_argument('--dry-run', action='store_true', help='Generate scaled-down data')
    args = parser.parse_args()

    scale_factor = 0.0001 if args.dry_run else 1.0 # 0.0001 reduces 20M to 2,000

    print("Connecting to MySQL...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Creating Database...")
        create_database(cursor)
        
        print("Creating Tables...")
        create_tables(cursor)
        
        print("Generating Data...")
        generate_data(conn, cursor, scale_factor)
        
        print("Creating Indexes (Post-Load)...")
        start_idx = time.time()
        create_indexes(cursor)
        print(f"Indexes created in {time.time() - start_idx:.2f}s")
        
        conn.close()
        print("\nProcess Completed Successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
