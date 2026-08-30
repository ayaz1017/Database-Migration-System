#!/usr/bin/env python3
"""
PostgreSQL Enterprise Data Generator
Generates ~250K - 300K rows across multiple normalized tables with
Views, Triggers (PL/pgSQL), and Stored Procedures / Functions.

Credentials:
  User: postgres
  Password: Ayaz@123
  Host: 127.0.0.1
  Port: 5432
"""

import sys
import time
import argparse
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from datetime import datetime

# Default Connection Settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5432
DEFAULT_USER = "postgres"
DEFAULT_PASS = "Ayaz@123"
DEFAULT_DBNAME = "enterprise_postgres_300k"

def get_connection(dbname="postgres", host=DEFAULT_HOST, port=DEFAULT_PORT, user=DEFAULT_USER, password=DEFAULT_PASS):
    """Establish and return a connection to PostgreSQL."""
    conn = psycopg2.connect(
        dbname=dbname,
        host=host,
        port=port,
        user=user,
        password=password
    )
    conn.autocommit = True
    return conn

def create_database(dbname, host, port, user, password):
    """Create target database if it does not exist, or recreate cleanly."""
    print(f"\n[*] Connecting to system database 'postgres' to prepare '{dbname}'...")
    conn = get_connection(dbname="postgres", host=host, port=port, user=user, password=password)
    cur = conn.cursor()

    # Terminate active connections to the database if exists
    cur.execute("""
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = %s AND pid <> pg_backend_pid();
    """, (dbname,))

    cur.execute(f"DROP DATABASE IF EXISTS {sql.Identifier(dbname).as_string(conn)};")
    print(f"[+] Dropped old database '{dbname}' (if existed).")
    
    cur.execute(f"CREATE DATABASE {sql.Identifier(dbname).as_string(conn)};")
    print(f"[+] Created database '{dbname}' successfully.")
    
    cur.close()
    conn.close()

def create_schema(dbname, host, port, user, password):
    """Create normalized tables, indexes, views, triggers, and stored procedures."""
    print(f"\n[*] Connecting to '{dbname}' to create schema objects...")
    conn = get_connection(dbname=dbname, host=host, port=port, user=user, password=password)
    cur = conn.cursor()

    print("[*] Creating Tables & Foreign Keys...")
    cur.execute("""
    -- 1. Departments Table
    CREATE TABLE departments (
        department_id SERIAL PRIMARY KEY,
        department_name VARCHAR(100) NOT NULL,
        location VARCHAR(100) NOT NULL,
        budget NUMERIC(14, 2) DEFAULT 500000.00,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- 2. Employees Table
    CREATE TABLE employees (
        employee_id SERIAL PRIMARY KEY,
        department_id INT REFERENCES departments(department_id) ON DELETE SET NULL,
        first_name VARCHAR(60) NOT NULL,
        last_name VARCHAR(60) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        salary NUMERIC(10, 2) NOT NULL CHECK (salary >= 20000),
        status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'ON_LEAVE', 'TERMINATED')),
        hire_date DATE NOT NULL
    );

    -- 3. Customers Table
    CREATE TABLE customers (
        customer_id SERIAL PRIMARY KEY,
        first_name VARCHAR(60) NOT NULL,
        last_name VARCHAR(60) NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        phone VARCHAR(30),
        city VARCHAR(80) NOT NULL,
        country VARCHAR(60) DEFAULT 'United States',
        credit_limit NUMERIC(12, 2) DEFAULT 5000.00,
        registered_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- 4. Products Table
    CREATE TABLE products (
        product_id SERIAL PRIMARY KEY,
        product_name VARCHAR(150) NOT NULL,
        category VARCHAR(60) NOT NULL,
        sku VARCHAR(40) UNIQUE NOT NULL,
        unit_price NUMERIC(10, 2) NOT NULL CHECK (unit_price > 0),
        stock_quantity INT NOT NULL DEFAULT 1000,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- 5. Orders Table
    CREATE TABLE orders (
        order_id SERIAL PRIMARY KEY,
        customer_id INT NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
        employee_id INT REFERENCES employees(employee_id) ON DELETE SET NULL,
        order_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(25) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED')),
        total_amount NUMERIC(14, 2) DEFAULT 0.00,
        shipping_city VARCHAR(80) NOT NULL
    );

    -- 6. Order Items Table
    CREATE TABLE order_items (
        item_id SERIAL PRIMARY KEY,
        order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
        product_id INT NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
        quantity INT NOT NULL CHECK (quantity > 0),
        unit_price NUMERIC(10, 2) NOT NULL,
        discount_percent NUMERIC(5, 2) DEFAULT 0.00,
        line_total NUMERIC(12, 2) NOT NULL
    );

    -- 7. Payments Table
    CREATE TABLE payments (
        payment_id SERIAL PRIMARY KEY,
        order_id INT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
        payment_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        payment_method VARCHAR(30) NOT NULL CHECK (payment_method IN ('CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'WIRE_TRANSFER', 'CRYPTO')),
        amount NUMERIC(14, 2) NOT NULL,
        status VARCHAR(20) DEFAULT 'COMPLETED' CHECK (status IN ('COMPLETED', 'PENDING', 'FAILED', 'REFUNDED'))
    );

    -- 8. Audit Log Table
    CREATE TABLE audit_logs (
        log_id SERIAL PRIMARY KEY,
        table_name VARCHAR(50) NOT NULL,
        operation VARCHAR(20) NOT NULL,
        record_id INT,
        action_timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        details TEXT
    );

    -- Performance Indexes
    CREATE INDEX idx_emp_dept ON employees(department_id);
    CREATE INDEX idx_emp_salary ON employees(salary);
    CREATE INDEX idx_cust_city ON customers(city);
    CREATE INDEX idx_cust_email ON customers(email);
    CREATE INDEX idx_prod_category ON products(category);
    CREATE INDEX idx_orders_cust ON orders(customer_id);
    CREATE INDEX idx_orders_date ON orders(order_date);
    CREATE INDEX idx_orders_status ON orders(status);
    CREATE INDEX idx_items_order ON order_items(order_id);
    CREATE INDEX idx_items_product ON order_items(product_id);
    CREATE INDEX idx_pay_order ON payments(order_id);
    """)
    print("[+] Created 8 Tables and Indexes.")

    # ----------------------------------------------------
    # Views
    # ----------------------------------------------------
    print("[*] Creating Analytical Views...")
    cur.execute("""
    -- View 1: Customer Order Summary
    CREATE OR REPLACE VIEW vw_customer_order_summary AS
    SELECT 
        c.customer_id,
        c.first_name || ' ' || c.last_name AS customer_name,
        c.email,
        c.city,
        c.country,
        COUNT(o.order_id) AS total_orders,
        COALESCE(SUM(o.total_amount), 0.00) AS lifetime_spend,
        MAX(o.order_date) AS last_order_date
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.email, c.city, c.country;

    -- View 2: Product Sales & Inventory Analytics
    CREATE OR REPLACE VIEW vw_product_sales_analytics AS
    SELECT 
        p.product_id,
        p.product_name,
        p.category,
        p.unit_price,
        p.stock_quantity,
        COALESCE(SUM(oi.quantity), 0) AS units_sold,
        COALESCE(SUM(oi.line_total), 0.00) AS total_revenue
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    GROUP BY p.product_id, p.product_name, p.category, p.unit_price, p.stock_quantity;

    -- View 3: Department Payroll Overview
    CREATE OR REPLACE VIEW vw_department_payroll AS
    SELECT 
        d.department_id,
        d.department_name,
        d.location,
        d.budget,
        COUNT(e.employee_id) AS total_employees,
        COALESCE(SUM(e.salary), 0.00) AS total_payroll,
        ROUND(COALESCE(AVG(e.salary), 0.00), 2) AS avg_salary,
        (d.budget - COALESCE(SUM(e.salary), 0.00)) AS remaining_budget
    FROM departments d
    LEFT JOIN employees e ON d.department_id = e.department_id AND e.status = 'ACTIVE'
    GROUP BY d.department_id, d.department_name, d.location, d.budget;
    """)
    print("[+] Created 3 Views: vw_customer_order_summary, vw_product_sales_analytics, vw_department_payroll.")

    # ----------------------------------------------------
    # Trigger Functions & Triggers (PL/pgSQL)
    # ----------------------------------------------------
    print("[*] Creating Triggers and Trigger Functions...")
    cur.execute("""
    -- Trigger Function 1: Audit Orders modifications
    CREATE OR REPLACE FUNCTION fn_audit_orders()
    RETURNS TRIGGER AS $$
    BEGIN
        IF (TG_OP = 'INSERT') THEN
            INSERT INTO audit_logs (table_name, operation, record_id, details)
            VALUES ('orders', 'INSERT', NEW.order_id, 'Created order for customer ' || NEW.customer_id || ' status ' || NEW.status);
            RETURN NEW;
        ELSIF (TG_OP = 'UPDATE') THEN
            INSERT INTO audit_logs (table_name, operation, record_id, details)
            VALUES ('orders', 'UPDATE', NEW.order_id, 'Status changed from ' || OLD.status || ' to ' || NEW.status || ', Total: ' || NEW.total_amount);
            RETURN NEW;
        END IF;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_audit_orders
    AFTER INSERT OR UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_audit_orders();

    -- Trigger Function 2: Adjust product stock after order_items insert
    CREATE OR REPLACE FUNCTION fn_update_product_stock()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE products
        SET stock_quantity = stock_quantity - NEW.quantity
        WHERE product_id = NEW.product_id;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_update_stock
    AFTER INSERT ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION fn_update_product_stock();
    """)
    print("[+] Created Triggers: trg_audit_orders and trg_update_stock.")

    # ----------------------------------------------------
    # Stored Procedures and PL/pgSQL Functions
    # ----------------------------------------------------
    print("[*] Creating Stored Procedures and PL/pgSQL Functions...")
    cur.execute("""
    -- Function 1: Get total customer spend
    CREATE OR REPLACE FUNCTION fn_get_customer_spend(p_cust_id INT)
    RETURNS NUMERIC(14, 2) AS $$
    DECLARE
        v_total NUMERIC(14, 2);
    BEGIN
        SELECT COALESCE(SUM(total_amount), 0.00) INTO v_total
        FROM orders
        WHERE customer_id = p_cust_id AND status <> 'CANCELLED';
        RETURN v_total;
    END;
    $$ LANGUAGE plpgsql;

    -- Stored Procedure 1: Recalculate Department Budgets
    CREATE OR REPLACE PROCEDURE sp_recalculate_department_budgets(p_min_headcount INT DEFAULT 10)
    LANGUAGE plpgsql
    AS $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN 
            SELECT department_id, SUM(salary) AS total_sal
            FROM employees
            WHERE status = 'ACTIVE'
            GROUP BY department_id
            HAVING COUNT(employee_id) >= p_min_headcount
        LOOP
            UPDATE departments
            SET budget = r.total_sal * 1.25
            WHERE department_id = r.department_id;
        END LOOP;
        
        INSERT INTO audit_logs (table_name, operation, record_id, details)
        VALUES ('departments', 'PROCEDURE', NULL, 'sp_recalculate_department_budgets completed successfully');
    END;
    $$;

    -- Stored Procedure 2: Complete order and process payment
    CREATE OR REPLACE PROCEDURE sp_mark_order_delivered(p_order_id INT)
    LANGUAGE plpgsql
    AS $$
    BEGIN
        UPDATE orders
        SET status = 'DELIVERED'
        WHERE order_id = p_order_id;

        UPDATE payments
        SET status = 'COMPLETED'
        WHERE order_id = p_order_id;
    END;
    $$;
    """)
    print("[+] Created Stored Procedures and Functions: fn_get_customer_spend, sp_recalculate_department_budgets, sp_mark_order_delivered.")

    cur.close()
    conn.close()

def generate_data(dbname, host, port, user, password):
    """
    Populate ~250K - 300K rows with realistic data using high-speed
    PostgreSQL generation queries.
    """
    print(f"\n[*] Generating ~250K - 300K rows into '{dbname}'...")
    conn = get_connection(dbname=dbname, host=host, port=port, user=user, password=password)
    cur = conn.cursor()

    # Temporarily disable order audit trigger during bulk insert for maximum throughput
    cur.execute("ALTER TABLE orders DISABLE TRIGGER trg_audit_orders;")
    cur.execute("ALTER TABLE order_items DISABLE TRIGGER trg_update_stock;")

    start_total = time.time()

    # 1. Departments (100 rows)
    print("  -> Inserting 100 Departments...")
    cur.execute("""
        INSERT INTO departments (department_name, location, budget)
        SELECT 
            'Department ' || i,
            (ARRAY['New York', 'San Francisco', 'Chicago', 'Austin', 'Seattle', 'London', 'Berlin', 'Tokyo', 'Toronto', 'Sydney'])[(i % 10) + 1],
            (500000 + (i * 12500))::NUMERIC(14,2)
        FROM generate_series(1, 100) AS i;
    """)

    # 2. Employees (5,000 rows)
    print("  -> Inserting 5,000 Employees...")
    cur.execute("""
        INSERT INTO employees (department_id, first_name, last_name, email, salary, status, hire_date)
        SELECT 
            ((i % 100) + 1),
            (ARRAY['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica'])[(i % 16) + 1],
            (ARRAY['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas'])[(i % 16) + 1],
            'emp_' || i || '_' || substr(md5(random()::text), 1, 6) || '@company.org',
            (35000 + (random() * 95000))::NUMERIC(10,2),
            (ARRAY['ACTIVE', 'ACTIVE', 'ACTIVE', 'ON_LEAVE', 'TERMINATED'])[(i % 5) + 1],
            CURRENT_DATE - ((i % 3650) || ' days')::INTERVAL
        FROM generate_series(1, 5000) AS i;
    """)

    # 3. Customers (40,000 rows)
    print("  -> Inserting 40,000 Customers...")
    cur.execute("""
        INSERT INTO customers (first_name, last_name, email, phone, city, country, credit_limit, registered_at)
        SELECT 
            (ARRAY['Alexander', 'Emily', 'Daniel', 'Sophia', 'Matthew', 'Olivia', 'Ethan', 'Emma', 'Andrew', 'Ava', 'Lucas', 'Isabella', 'Benjamin', 'Mia', 'Henry', 'Charlotte'])[(i % 16) + 1],
            (ARRAY['Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young'])[(i % 16) + 1],
            'customer_' || i || '_' || substr(md5(random()::text), 1, 6) || '@email.com',
            '+1-' || (200 + (i % 700)) || '-' || (100 + (i % 899)) || '-' || lpad((i % 10000)::text, 4, '0'),
            (ARRAY['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville', 'Columbus', 'Indianapolis', 'Charlotte', 'Seattle'])[(i % 16) + 1],
            'United States',
            (2500 + ((i % 20) * 500))::NUMERIC(12,2),
            CURRENT_TIMESTAMP - ((i % 1800) || ' days')::INTERVAL
        FROM generate_series(1, 40000) AS i;
    """)

    # 4. Products (10,000 rows)
    print("  -> Inserting 10,000 Products...")
    cur.execute("""
        INSERT INTO products (product_name, category, sku, unit_price, stock_quantity)
        SELECT 
            (ARRAY['Pro', 'Ultra', 'Smart', 'Eco', 'Elite', 'Max', 'Prime', 'Apex'])[(i % 8) + 1] || ' ' ||
            (ARRAY['Widget', 'Sensor', 'Display', 'Connector', 'Battery', 'Controller', 'Module', 'Adapter', 'Router', 'Hub'])[(i % 10) + 1] || ' #' || i,
            (ARRAY['Electronics', 'Hardware', 'Networking', 'Accessories', 'Power Supplies', 'Components', 'Peripherals'])[(i % 7) + 1],
            'SKU-' || upper(substr(md5(i::text), 1, 8)) || '-' || i,
            (9.99 + (random() * 490.00))::NUMERIC(10,2),
            (50 + (i % 5000))
        FROM generate_series(1, 10000) AS i;
    """)

    # 5. Orders (80,000 rows)
    print("  -> Inserting 80,000 Orders...")
    cur.execute("""
        INSERT INTO orders (customer_id, employee_id, order_date, status, total_amount, shipping_city)
        SELECT 
            ((i % 40000) + 1),
            ((i % 5000) + 1),
            CURRENT_TIMESTAMP - ((i % 730) || ' days')::INTERVAL - ((i % 86400) || ' seconds')::INTERVAL,
            (ARRAY['DELIVERED', 'DELIVERED', 'SHIPPED', 'PROCESSING', 'PENDING', 'CANCELLED'])[(i % 6) + 1],
            0.00,
            (ARRAY['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose'])[(i % 10) + 1]
        FROM generate_series(1, 80000) AS i;
    """)

    # 6. Order Items (120,000 rows)
    print("  -> Inserting 120,000 Order Items...")
    cur.execute("""
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_percent, line_total)
        SELECT 
            ((i % 80000) + 1) AS order_id,
            ((i % 10000) + 1) AS product_id,
            ((i % 5) + 1) AS quantity,
            (19.99 + ((i % 50) * 4.50))::NUMERIC(10,2) AS unit_price,
            (CASE WHEN i % 4 = 0 THEN 10.00 WHEN i % 7 = 0 THEN 15.00 ELSE 0.00 END)::NUMERIC(5,2) AS discount_percent,
            (((i % 5) + 1) * (19.99 + ((i % 50) * 4.50)) * (1.0 - (CASE WHEN i % 4 = 0 THEN 0.10 WHEN i % 7 = 0 THEN 0.15 ELSE 0.0 END)))::NUMERIC(12,2) AS line_total
        FROM generate_series(1, 120000) AS i;
    """)

    # Update orders.total_amount from order_items
    print("  -> Calculating and updating Order totals...")
    cur.execute("""
        UPDATE orders o
        SET total_amount = sub.sum_total
        FROM (
            SELECT order_id, SUM(line_total) AS sum_total
            FROM order_items
            GROUP BY order_id
        ) sub
        WHERE o.order_id = sub.order_id;
    """)

    # 7. Payments (50,000 rows)
    print("  -> Inserting 50,000 Payments...")
    cur.execute("""
        INSERT INTO payments (order_id, payment_date, payment_method, amount, status)
        SELECT 
            i AS order_id,
            CURRENT_TIMESTAMP - ((i % 365) || ' days')::INTERVAL,
            (ARRAY['CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'WIRE_TRANSFER', 'CRYPTO'])[(i % 5) + 1],
            (50.00 + ((i % 100) * 12.50))::NUMERIC(14,2),
            (ARRAY['COMPLETED', 'COMPLETED', 'COMPLETED', 'PENDING', 'REFUNDED'])[(i % 5) + 1]
        FROM generate_series(1, 50000) AS i;
    """)

    # Re-enable triggers and fire a test trigger
    print("  -> Re-enabling triggers and writing audit entries...")
    cur.execute("ALTER TABLE orders ENABLE TRIGGER trg_audit_orders;")
    cur.execute("ALTER TABLE order_items ENABLE TRIGGER trg_update_stock;")

    # Insert a sample order to test the active trigger
    cur.execute("""
        INSERT INTO orders (customer_id, employee_id, order_date, status, total_amount, shipping_city)
        VALUES (1, 1, CURRENT_TIMESTAMP, 'PENDING', 250.00, 'New York');
    """)

    # Execute stored procedure to verify functionality
    print("  -> Executing stored procedure 'sp_recalculate_department_budgets'...")
    cur.execute("CALL sp_recalculate_department_budgets(5);")

    duration = time.time() - start_total
    print(f"[+] Bulk data generation completed in {duration:.2f} seconds.")

    # Verification summary
    print("\n========================================================")
    print("            DATABASE VERIFICATION SUMMARY               ")
    print("========================================================")
    tables = [
        "departments",
        "employees",
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
        "audit_logs"
    ]
    total_rows = 0
    for tbl in tables:
        cur.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cur.fetchone()[0]
        total_rows += cnt
        print(f" Table: {tbl:<16} | Rows: {cnt:>8,}")

    print("--------------------------------------------------------")
    print(f" TOTAL ROWS GENERATED: {total_rows:,}")
    print("========================================================")

    # Test View query
    cur.execute("SELECT customer_name, total_orders, lifetime_spend FROM vw_customer_order_summary LIMIT 3;")
    view_rows = cur.fetchall()
    print("\nSample View Query [vw_customer_order_summary]:")
    for vr in view_rows:
        print(f"  Customer: {vr[0]} | Orders: {vr[1]} | Spend: ${vr[2]:,.2f}")

    cur.close()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Generate 200K-300K sample dataset in PostgreSQL.")
    parser.add_argument("--dbname", default=DEFAULT_DBNAME, help=f"Database name (default: {DEFAULT_DBNAME})")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--user", default=DEFAULT_USER, help=f"Username (default: {DEFAULT_USER})")
    parser.add_argument("--password", default=DEFAULT_PASS, help=f"Password (default: {DEFAULT_PASS})")

    args = parser.parse_args()

    print("========================================================")
    print("   PostgreSQL 200K-300K Enterprise Data Generator       ")
    print("========================================================")
    print(f" Host:     {args.host}:{args.port}")
    print(f" User:     {args.user}")
    print(f" Database: {args.dbname}")

    try:
        create_database(args.dbname, args.host, args.port, args.user, args.password)
        create_schema(args.dbname, args.host, args.port, args.user, args.password)
        generate_data(args.dbname, args.host, args.port, args.user, args.password)
        print("\n[SUCCESS] PostgreSQL schema and data successfully created!")
    except Exception as e:
        print(f"\n[ERROR] Process failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
