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

DB_NAME = "enterprise_500k_db"

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def main():
    total_start_time = time.time()
    print("=" * 70)
    print(f"  CREATING ADVANCED MYSQL DATABASE: {DB_NAME}")
    print(f"  Target: ~500,000+ records, multiple tables, views, triggers, procedures")
    print("=" * 70)

    print(f"\n[1/6] Connecting to MySQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Drop and recreate database
    print(f"  Dropping existing database '{DB_NAME}' if present...")
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE {DB_NAME}")

    # Temporarily disable checks for rapid bulk loading
    cursor.execute("SET unique_checks=0")
    cursor.execute("SET foreign_key_checks=0")
    cursor.execute("SET sql_log_bin=0")

    print("\n[2/6] Creating Schema (Tables & Constraints)...")

    # Table 1: categories (~500 records)
    cursor.execute("""
        CREATE TABLE categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_code VARCHAR(32) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            parent_id INT DEFAULT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    print("  + Table: categories")

    # Table 2: customers (~100,000 records)
    cursor.execute("""
        CREATE TABLE customers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_uuid CHAR(36) NOT NULL,
            first_name VARCHAR(60) NOT NULL,
            last_name VARCHAR(60) NOT NULL,
            email VARCHAR(150) NOT NULL,
            phone VARCHAR(30),
            tier ENUM('standard', 'silver', 'gold', 'platinum') DEFAULT 'standard',
            credit_limit DECIMAL(12, 2) DEFAULT 1000.00,
            account_balance DECIMAL(12, 4) DEFAULT 0.0000,
            preferences JSON,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    print("  + Table: customers")

    # Table 3: products (~50,000 records)
    cursor.execute("""
        CREATE TABLE products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sku VARCHAR(64) NOT NULL,
            name VARCHAR(200) NOT NULL,
            category_id INT,
            base_price DECIMAL(10, 2) NOT NULL,
            discount_price DECIMAL(10, 2),
            cost_price DECIMAL(10, 2),
            weight_kg DECIMAL(6, 2) DEFAULT 1.0,
            specs JSON,
            status ENUM('active', 'discontinued', 'out_of_stock') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    print("  + Table: products")

    # Table 4: inventory (~50,000 records)
    cursor.execute("""
        CREATE TABLE inventory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            warehouse_code VARCHAR(30) NOT NULL,
            stock_quantity INT DEFAULT 0,
            safety_stock INT DEFAULT 20,
            last_restocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    print("  + Table: inventory")

    # Table 5: orders (~150,000 records)
    cursor.execute("""
        CREATE TABLE orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_number CHAR(36) NOT NULL,
            customer_id INT NOT NULL,
            total_amount DECIMAL(12, 2) NOT NULL,
            tax_amount DECIMAL(10, 2) DEFAULT 0.00,
            shipping_fee DECIMAL(10, 2) DEFAULT 0.00,
            status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
            shipping_address LONGTEXT,
            payment_metadata JSON,
            order_date DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    print("  + Table: orders")

    # Table 6: order_items (~100,000 records)
    cursor.execute("""
        CREATE TABLE order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            unit_price DECIMAL(10, 2) NOT NULL,
            discount DECIMAL(10, 2) DEFAULT 0.00,
            subtotal DECIMAL(12, 2) NOT NULL
        ) ENGINE=InnoDB
    """)
    print("  + Table: order_items")

    # Table 7: payments (~50,000 records)
    cursor.execute("""
        CREATE TABLE payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            payment_ref VARCHAR(64) NOT NULL,
            order_id INT NOT NULL,
            amount DECIMAL(12, 2) NOT NULL,
            payment_method ENUM('credit_card', 'paypal', 'bank_transfer', 'crypto') DEFAULT 'credit_card',
            status ENUM('authorized', 'captured', 'refunded', 'failed') DEFAULT 'captured',
            paid_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    print("  + Table: payments")

    # Table 8: product_reviews (~50,000 records)
    cursor.execute("""
        CREATE TABLE product_reviews (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            customer_id INT NOT NULL,
            rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review_title VARCHAR(150),
            review_body LONGTEXT,
            is_verified_purchase BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    print("  + Table: product_reviews")

    # Table 9: audit_logs (will receive trigger logs)
    cursor.execute("""
        CREATE TABLE audit_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INT NOT NULL,
            action VARCHAR(100) NOT NULL,
            details JSON,
            logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)
    print("  + Table: audit_logs")

    # Helper function for exponential doubling population
    def populate_table(table_name, target_rows, seed_insert_query, seed_data_generator, select_double_query, initial_seed=1000):
        print(f"\nPopulating '{table_name}' (Target: {target_rows:,} rows)...")
        start_t = time.time()
        
        seed_count = min(initial_seed, target_rows)
        seed_rows = [seed_data_generator() for _ in range(seed_count)]
        cursor.executemany(seed_insert_query, seed_rows)
        conn.commit()
        
        current_rows = seed_count
        iteration = 1
        while current_rows < target_rows:
            t0 = time.time()
            limit = min(current_rows, target_rows - current_rows)
            cursor.execute(select_double_query.format(limit=limit))
            conn.commit()
            inserted = cursor.rowcount
            current_rows += inserted
            print(f"  [{table_name}] Iteration {iteration}: +{inserted:,} -> Total {current_rows:,} ({time.time()-t0:.2f}s)")
            iteration += 1
        print(f"  -> Finished '{table_name}' with {current_rows:,} rows in {time.time()-start_t:.2f}s.")

    print("\n[3/6] Populating Tables with 500,000+ Records...")

    # Populate Categories (500 rows)
    populate_table(
        table_name="categories",
        target_rows=500,
        initial_seed=50,
        seed_insert_query="INSERT INTO categories (category_code, name, description, is_active) VALUES (%s, %s, %s, %s)",
        seed_data_generator=lambda: (
            f"CAT-{random_string(6).upper()}",
            f"Category {random_string(6)}",
            f"Description for category {random_string(12)}",
            True
        ),
        select_double_query="""
            INSERT INTO categories (category_code, name, description, is_active)
            SELECT CONCAT('CAT-', SUBSTRING(MD5(RAND()), 1, 8)), CONCAT(name, ' Sub'), description, is_active
            FROM categories LIMIT {limit}
        """
    )

    # Populate Customers (100,000 rows)
    tiers = ['standard', 'silver', 'gold', 'platinum']
    first_names = ['James', 'Emma', 'Oliver', 'Sophia', 'Liam', 'Ava', 'Noah', 'Isabella', 'William', 'Mia']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Wilson', 'Anderson', 'Taylor']
    populate_table(
        table_name="customers",
        target_rows=100_000,
        initial_seed=1000,
        seed_insert_query="INSERT INTO customers (customer_uuid, first_name, last_name, email, phone, tier, credit_limit, account_balance, preferences, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            str(uuid.uuid4()),
            random.choice(first_names),
            random.choice(last_names),
            f"user_{random_string(8)}@enterprise.io",
            f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            random.choice(tiers),
            round(random.uniform(500.0, 20000.0), 2),
            round(random.uniform(0.0, 5000.0), 4),
            json.dumps({"newsletter": True, "theme": random.choice(["dark", "light", "auto"]), "currency": "USD"}),
            random.choice([True, True, True, False])
        ),
        select_double_query="""
            INSERT INTO customers (customer_uuid, first_name, last_name, email, phone, tier, credit_limit, account_balance, preferences, is_active)
            SELECT UUID(), first_name, last_name, CONCAT(SUBSTRING(MD5(RAND()), 1, 8), '@enterprise.io'), phone, tier, credit_limit + RAND(), account_balance + RAND(), preferences, is_active
            FROM customers LIMIT {limit}
        """
    )

    # Populate Products (50,000 rows)
    product_prefixes = ['Quantum', 'Apex', 'Hyper', 'Nova', 'Ultra', 'Core', 'Vortex', 'Prime', 'Titan', 'Pulse']
    product_types = ['Laptop', 'Headphones', 'Monitor', 'Keyboard', 'Mouse', 'Server', 'Router', 'Smartwatch', 'Drone', 'Camera']
    populate_table(
        table_name="products",
        target_rows=50_000,
        initial_seed=1000,
        seed_insert_query="INSERT INTO products (sku, name, category_id, base_price, discount_price, cost_price, weight_kg, specs, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            f"PRD-{random_string(8).upper()}",
            f"{random.choice(product_prefixes)} {random.choice(product_types)} {random.randint(100, 999)}",
            random.randint(1, 500),
            round(random.uniform(20.0, 3000.0), 2),
            round(random.uniform(15.0, 2500.0), 2),
            round(random.uniform(10.0, 1500.0), 2),
            round(random.uniform(0.2, 25.0), 2),
            json.dumps({"color": random.choice(["Space Gray", "Silver", "Midnight Black", "Arctic White"]), "warranty_months": random.choice([12, 24, 36])}),
            random.choice(['active', 'active', 'active', 'out_of_stock', 'discontinued'])
        ),
        select_double_query="""
            INSERT INTO products (sku, name, category_id, base_price, discount_price, cost_price, weight_kg, specs, status)
            SELECT CONCAT('PRD-', SUBSTRING(MD5(RAND()), 1, 8)), CONCAT(name, ' Pro'), FLOOR(1 + (RAND() * 499)), base_price + (RAND() * 20), discount_price, cost_price, weight_kg, specs, status
            FROM products LIMIT {limit}
        """
    )

    # Populate Inventory (50,000 rows)
    warehouses = ['WH-EAST-01', 'WH-WEST-02', 'WH-CENTRAL-03', 'WH-EU-01', 'WH-APAC-02']
    populate_table(
        table_name="inventory",
        target_rows=50_000,
        initial_seed=1000,
        seed_insert_query="INSERT INTO inventory (product_id, warehouse_code, stock_quantity, safety_stock) VALUES (%s, %s, %s, %s)",
        seed_data_generator=lambda: (
            random.randint(1, 50_000),
            random.choice(warehouses),
            random.randint(0, 1500),
            random.randint(10, 50)
        ),
        select_double_query="""
            INSERT INTO inventory (product_id, warehouse_code, stock_quantity, safety_stock)
            SELECT FLOOR(1 + (RAND() * 49999)), warehouse_code, FLOOR(RAND() * 1500), safety_stock
            FROM inventory LIMIT {limit}
        """
    )

    # Populate Orders (150,000 rows)
    order_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    populate_table(
        table_name="orders",
        target_rows=150_000,
        initial_seed=1000,
        seed_insert_query="INSERT INTO orders (order_number, customer_id, total_amount, tax_amount, shipping_fee, status, shipping_address, payment_metadata) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            str(uuid.uuid4()),
            random.randint(1, 100_000),
            round(random.uniform(25.0, 4500.0), 2),
            round(random.uniform(2.0, 350.0), 2),
            round(random.uniform(5.0, 50.0), 2),
            random.choice(order_statuses),
            f"{random.randint(100, 9999)} Industrial Blvd, Suite {random.randint(1, 500)}, Metro City, USA",
            json.dumps({"gateway": random.choice(["Stripe", "PayPal", "Square", "Adyen"]), "tx_ref": random_string(16)})
        ),
        select_double_query="""
            INSERT INTO orders (order_number, customer_id, total_amount, tax_amount, shipping_fee, status, shipping_address, payment_metadata)
            SELECT UUID(), FLOOR(1 + (RAND() * 99999)), total_amount + (RAND() * 10), tax_amount, shipping_fee, status, shipping_address, payment_metadata
            FROM orders LIMIT {limit}
        """
    )

    # Populate Order Items (100,000 rows)
    populate_table(
        table_name="order_items",
        target_rows=100_000,
        initial_seed=1000,
        seed_insert_query="INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount, subtotal) VALUES (%s, %s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            random.randint(1, 150_000),
            random.randint(1, 50_000),
            random.randint(1, 5),
            round(random.uniform(10.0, 500.0), 2),
            0.00,
            round(random.uniform(10.0, 2500.0), 2)
        ),
        select_double_query="""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount, subtotal)
            SELECT FLOOR(1 + (RAND() * 149999)), FLOOR(1 + (RAND() * 49999)), quantity, unit_price, discount, unit_price * quantity
            FROM order_items LIMIT {limit}
        """
    )

    # Populate Payments (50,000 rows)
    payment_methods = ['credit_card', 'paypal', 'bank_transfer', 'crypto']
    payment_statuses = ['authorized', 'captured', 'refunded', 'failed']
    populate_table(
        table_name="payments",
        target_rows=50_000,
        initial_seed=1000,
        seed_insert_query="INSERT INTO payments (payment_ref, order_id, amount, payment_method, status) VALUES (%s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            f"PAY-{random_string(12).upper()}",
            random.randint(1, 150_000),
            round(random.uniform(25.0, 4500.0), 2),
            random.choice(payment_methods),
            random.choice(payment_statuses)
        ),
        select_double_query="""
            INSERT INTO payments (payment_ref, order_id, amount, payment_method, status)
            SELECT CONCAT('PAY-', SUBSTRING(MD5(RAND()), 1, 12)), FLOOR(1 + (RAND() * 149999)), amount, payment_method, status
            FROM payments LIMIT {limit}
        """
    )

    # Populate Product Reviews (50,000 rows)
    review_titles = ['Outstanding quality!', 'Worth every penny', 'Decent product', 'Could be better', 'Exceeded expectations', 'Fast delivery, great item']
    populate_table(
        table_name="product_reviews",
        target_rows=50_000,
        initial_seed=1000,
        seed_insert_query="INSERT INTO product_reviews (product_id, customer_id, rating, review_title, review_body, is_verified_purchase) VALUES (%s, %s, %s, %s, %s, %s)",
        seed_data_generator=lambda: (
            random.randint(1, 50_000),
            random.randint(1, 100_000),
            random.randint(1, 5),
            random.choice(review_titles),
            f"I have been using this product for a while now. Quality and craftsmanship are solid. Performance index is {random.randint(80, 99)}%.",
            random.choice([True, True, True, False])
        ),
        select_double_query="""
            INSERT INTO product_reviews (product_id, customer_id, rating, review_title, review_body, is_verified_purchase)
            SELECT FLOOR(1 + (RAND() * 49999)), FLOOR(1 + (RAND() * 99999)), FLOOR(1 + (RAND() * 5)), review_title, review_body, is_verified_purchase
            FROM product_reviews LIMIT {limit}
        """
    )

    # Re-enable database checks
    cursor.execute("SET unique_checks=1")
    cursor.execute("SET foreign_key_checks=1")

    # Add useful indexes for performance
    print("\nAdding performance indexes...")
    cursor.execute("CREATE INDEX idx_customers_email ON customers(email)")
    cursor.execute("CREATE INDEX idx_products_category ON products(category_id)")
    cursor.execute("CREATE INDEX idx_orders_customer ON orders(customer_id)")
    cursor.execute("CREATE INDEX idx_orders_status ON orders(status)")
    cursor.execute("CREATE INDEX idx_order_items_order ON order_items(order_id)")
    cursor.execute("CREATE INDEX idx_order_items_product ON order_items(product_id)")
    cursor.execute("CREATE INDEX idx_inventory_product ON inventory(product_id)")
    cursor.execute("CREATE INDEX idx_reviews_product ON product_reviews(product_id)")
    print("  + Indexes created successfully.")

    # 4. CREATING VIEWS
    print("\n[4/6] Creating Database Views...")
    
    # View 1: active_customers_summary_view
    cursor.execute("""
        CREATE VIEW active_customers_summary_view AS
        SELECT 
            id, 
            customer_uuid, 
            CONCAT(first_name, ' ', last_name) AS full_name, 
            email, 
            tier, 
            credit_limit, 
            account_balance, 
            created_at
        FROM customers
        WHERE is_active = TRUE
    """)
    print("  + VIEW: active_customers_summary_view")

    # View 2: top_selling_products_view
    cursor.execute("""
        CREATE VIEW top_selling_products_view AS
        SELECT 
            p.id AS product_id,
            p.sku,
            p.name AS product_name,
            c.name AS category_name,
            p.base_price,
            COUNT(oi.id) AS total_sales_count,
            SUM(oi.quantity) AS total_units_sold,
            SUM(oi.subtotal) AS total_revenue
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN order_items oi ON p.id = oi.product_id
        GROUP BY p.id, p.sku, p.name, c.name, p.base_price
    """)
    print("  + VIEW: top_selling_products_view")

    # View 3: low_stock_inventory_view
    cursor.execute("""
        CREATE VIEW low_stock_inventory_view AS
        SELECT 
            i.id AS inventory_id,
            i.product_id,
            p.name AS product_name,
            p.sku,
            i.warehouse_code,
            i.stock_quantity,
            i.safety_stock,
            (i.safety_stock - i.stock_quantity) AS stock_deficit
        FROM inventory i
        JOIN products p ON i.product_id = p.id
        WHERE i.stock_quantity <= i.safety_stock
    """)
    print("  + VIEW: low_stock_inventory_view")

    # View 4: customer_order_insights_view
    cursor.execute("""
        CREATE VIEW customer_order_insights_view AS
        SELECT 
            c.id AS customer_id,
            CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
            c.tier,
            COUNT(o.id) AS order_count,
            COALESCE(SUM(o.total_amount), 0.00) AS total_spend,
            COALESCE(AVG(o.total_amount), 0.00) AS avg_order_value,
            MAX(o.order_date) AS last_order_date
        FROM customers c
        LEFT JOIN orders o ON c.id = o.customer_id
        GROUP BY c.id, c.first_name, c.last_name, c.tier
    """)
    print("  + VIEW: customer_order_insights_view")

    # View 5: monthly_sales_revenue_view
    cursor.execute("""
        CREATE VIEW monthly_sales_revenue_view AS
        SELECT 
            DATE_FORMAT(order_date, '%Y-%m') AS sales_month,
            status,
            COUNT(*) AS total_orders,
            SUM(total_amount) AS gross_revenue,
            SUM(tax_amount) AS total_tax,
            SUM(shipping_fee) AS total_shipping
        FROM orders
        GROUP BY DATE_FORMAT(order_date, '%Y-%m'), status
    """)
    print("  + VIEW: monthly_sales_revenue_view")

    # 5. CREATING TRIGGERS
    print("\n[5/6] Creating Database Triggers...")

    # Trigger 1: after_customer_insert_audit
    cursor.execute("""
        CREATE TRIGGER after_customer_insert_audit
        AFTER INSERT ON customers
        FOR EACH ROW
        BEGIN
            INSERT INTO audit_logs (entity_type, entity_id, action, details)
            VALUES (
                'CUSTOMER', 
                NEW.id, 
                'CUSTOMER_REGISTERED', 
                JSON_OBJECT('email', NEW.email, 'tier', NEW.tier, 'uuid', NEW.customer_uuid)
            );
        END;
    """)
    print("  + TRIGGER: after_customer_insert_audit")

    # Trigger 2: after_order_status_update_audit
    cursor.execute("""
        CREATE TRIGGER after_order_status_update_audit
        AFTER UPDATE ON orders
        FOR EACH ROW
        BEGIN
            IF OLD.status != NEW.status THEN
                INSERT INTO audit_logs (entity_type, entity_id, action, details)
                VALUES (
                    'ORDER', 
                    NEW.id, 
                    'STATUS_CHANGED', 
                    JSON_OBJECT('old_status', OLD.status, 'new_status', NEW.status, 'order_number', NEW.order_number)
                );
            END IF;
        END;
    """)
    print("  + TRIGGER: after_order_status_update_audit")

    # Trigger 3: before_order_items_insert_calc
    cursor.execute("""
        CREATE TRIGGER before_order_items_insert_calc
        BEFORE INSERT ON order_items
        FOR EACH ROW
        BEGIN
            SET NEW.subtotal = (NEW.quantity * NEW.unit_price) - COALESCE(NEW.discount, 0.00);
        END;
    """)
    print("  + TRIGGER: before_order_items_insert_calc")

    # Trigger 4: after_review_insert_audit
    cursor.execute("""
        CREATE TRIGGER after_review_insert_audit
        AFTER INSERT ON product_reviews
        FOR EACH ROW
        BEGIN
            INSERT INTO audit_logs (entity_type, entity_id, action, details)
            VALUES (
                'PRODUCT_REVIEW', 
                NEW.id, 
                'REVIEW_SUBMITTED', 
                JSON_OBJECT('product_id', NEW.product_id, 'customer_id', NEW.customer_id, 'rating', NEW.rating)
            );
        END;
    """)
    print("  + TRIGGER: after_review_insert_audit")

    # 6. CREATING STORED PROCEDURES
    print("\n[6/6] Creating Stored Procedures...")

    # Procedure 1: update_order_status
    cursor.execute("""
        CREATE PROCEDURE update_order_status(
            IN p_order_id INT, 
            IN p_status VARCHAR(20)
        )
        BEGIN
            UPDATE orders 
            SET status = p_status 
            WHERE id = p_order_id;
        END;
    """)
    print("  + PROCEDURE: update_order_status")

    # Procedure 2: get_customer_metrics
    cursor.execute("""
        CREATE PROCEDURE get_customer_metrics(
            IN p_customer_id INT, 
            OUT p_order_count INT, 
            OUT p_total_spent DECIMAL(12, 2)
        )
        BEGIN
            SELECT 
                COUNT(*), 
                COALESCE(SUM(total_amount), 0.00) 
            INTO 
                p_order_count, 
                p_total_spent
            FROM orders
            WHERE customer_id = p_customer_id;
        END;
    """)
    print("  + PROCEDURE: get_customer_metrics")

    # Procedure 3: restock_low_inventory
    cursor.execute("""
        CREATE PROCEDURE restock_low_inventory(
            IN p_min_threshold INT, 
            IN p_add_amount INT
        )
        BEGIN
            UPDATE inventory 
            SET stock_quantity = stock_quantity + p_add_amount,
                last_restocked_at = NOW()
            WHERE stock_quantity < p_min_threshold;
        END;
    """)
    print("  + PROCEDURE: restock_low_inventory")

    # Procedure 4: process_bulk_discount
    cursor.execute("""
        CREATE PROCEDURE process_bulk_discount(
            IN p_category_id INT, 
            IN p_discount_percent DECIMAL(5, 2)
        )
        BEGIN
            UPDATE products 
            SET discount_price = ROUND(base_price * (1 - (p_discount_percent / 100)), 2)
            WHERE category_id = p_category_id AND status = 'active';
        END;
    """)
    print("  + PROCEDURE: process_bulk_discount")

    # =========================================================================
    # TESTING & VERIFICATION
    # =========================================================================
    print("\n" + "=" * 70)
    print("  RUNNING VERIFICATION TESTS ON TRIGGERS & PROCEDURES")
    print("=" * 70)

    print("1. Testing Trigger 'after_customer_insert_audit'...")
    cursor.execute("""
        INSERT INTO customers (customer_uuid, first_name, last_name, email, phone, tier)
        VALUES (UUID(), 'TestAudited', 'Customer', 'test.trigger@enterprise.io', '+1-555-0199', 'platinum')
    """)
    conn.commit()

    print("2. Testing Stored Procedure 'update_order_status' (which also fires order trigger)...")
    cursor.execute("CALL update_order_status(1, 'delivered')")
    conn.commit()

    print("3. Testing Stored Procedure 'get_customer_metrics'...")
    cursor.execute("SET @order_cnt = 0, @tot_spent = 0.00")
    cursor.execute("CALL get_customer_metrics(1, @order_cnt, @tot_spent)")
    cursor.execute("SELECT @order_cnt, @tot_spent")
    metric_res = cursor.fetchone()
    print(f"   Customer #1 Metrics: Orders={metric_res[0]}, Total Spent=${metric_res[1]}")

    print("4. Testing Procedure 'restock_low_inventory'...")
    cursor.execute("CALL restock_low_inventory(5, 50)")
    conn.commit()
    print(f"   Restocked low inventory items.")

    print("5. Checking Trigger-generated Audit Logs...")
    cursor.execute("SELECT log_id, entity_type, entity_id, action, details FROM audit_logs ORDER BY log_id DESC LIMIT 3")
    for log_row in cursor.fetchall():
        print(f"   Audit Log #{log_row[0]}: [{log_row[1]}] {log_row[3]} -> {log_row[4]}")

    # =========================================================================
    # SUMMARY REPORT
    # =========================================================================
    print("\n" + "=" * 70)
    print("  FINAL DATABASE SUMMARY REPORT")
    print("=" * 70)
    
    tables = [
        "categories",
        "customers",
        "products",
        "inventory",
        "orders",
        "order_items",
        "payments",
        "product_reviews",
        "audit_logs"
    ]
    
    total_records = 0
    for tbl in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cursor.fetchone()[0]
        total_records += cnt
        print(f"  * Table: {tbl:<20} -> {cnt:>10,d} rows")

    print("-" * 70)
    print(f"  TOTAL RECORDS GENERATED: {total_records:>18,d}")
    print("=" * 70)

    # List Views
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM information_schema.VIEWS 
        WHERE TABLE_SCHEMA = %s
    """, (DB_NAME,))
    views = [v[0] for v in cursor.fetchall()]
    print(f"\nViews ({len(views)}): {', '.join(views)}")

    # List Triggers
    cursor.execute("""
        SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE 
        FROM information_schema.TRIGGERS 
        WHERE TRIGGER_SCHEMA = %s
    """, (DB_NAME,))
    triggers = cursor.fetchall()
    print(f"\nTriggers ({len(triggers)}):")
    for t in triggers:
        print(f"  * {t[0]} ({t[1]} ON {t[2]})")

    # List Procedures
    cursor.execute("""
        SELECT ROUTINE_NAME 
        FROM information_schema.ROUTINES 
        WHERE ROUTINE_SCHEMA = %s AND ROUTINE_TYPE = 'PROCEDURE'
    """, (DB_NAME,))
    procedures = [p[0] for p in cursor.fetchall()]
    print(f"\nProcedures ({len(procedures)}): {', '.join(procedures)}")

    print(f"\n[SUCCESS] Completed in {time.time() - total_start_time:.2f} seconds!")

    conn.close()

if __name__ == "__main__":
    main()
