import random
import datetime

# Target rows:
# customers: 2,000
# products: 500
# orders: 8,000
# order_items: 15,000
# Total: ~25,500 rows

def escape_string(val):
    return val.replace("'", "''")

def generate_sql():
    sql = []
    
    # 1. Database Creation
    sql.append("-- Create Database")
    sql.append("DROP DATABASE IF EXISTS ecom_sample;")
    sql.append("CREATE DATABASE ecom_sample;")
    sql.append("USE ecom_sample;\n")
    
    # 2. Table Creation
    sql.append("-- Create Tables")
    sql.append("""
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

    sql.append("""
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT DEFAULT 0
);
""")

    sql.append("""
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'PENDING',
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
""")

    sql.append("""
CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
""")

    sql.append("""
CREATE TABLE price_audit_log (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")
    sql.append("\n")

    # 3. Insert Data
    print("Generating data...")
    
    # Generate Customers (2000)
    sql.append("-- Insert Customers")
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    
    customer_inserts = []
    for i in range(1, 2001):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}.{i}@example.com"
        date = datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 1000))
        customer_inserts.append(f"('{fn}', '{ln}', '{email}', '{date.strftime('%Y-%m-%d %H:%M:%S')}')")
        
        if len(customer_inserts) == 500:
            sql.append(f"INSERT INTO customers (first_name, last_name, email, created_at) VALUES {','.join(customer_inserts)};")
            customer_inserts = []

    # Generate Products (500)
    sql.append("-- Insert Products")
    categories = ["Electronics", "Clothing", "Home", "Books", "Sports"]
    product_inserts = []
    for i in range(1, 501):
        name = f"Product {i}"
        category = random.choice(categories)
        price = round(random.uniform(5.0, 500.0), 2)
        stock = random.randint(10, 1000)
        product_inserts.append(f"('{name}', '{category}', {price}, {stock})")
        
        if len(product_inserts) == 250:
            sql.append(f"INSERT INTO products (name, category, price, stock_quantity) VALUES {','.join(product_inserts)};")
            product_inserts = []
            
    # Generate Orders (8000)
    sql.append("-- Insert Orders")
    order_inserts = []
    statuses = ['PENDING', 'SHIPPED', 'DELIVERED', 'CANCELLED']
    for i in range(1, 8001):
        customer_id = random.randint(1, 2000)
        date = datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 365))
        status = random.choice(statuses)
        order_inserts.append(f"({customer_id}, '{date.strftime('%Y-%m-%d %H:%M:%S')}', '{status}', 0)")
        
        if len(order_inserts) == 1000:
            sql.append(f"INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES {','.join(order_inserts)};")
            order_inserts = []
            
    # Generate Order Items (15000)
    sql.append("-- Insert Order Items")
    item_inserts = []
    for i in range(1, 15001):
        order_id = random.randint(1, 8000)
        product_id = random.randint(1, 500)
        quantity = random.randint(1, 5)
        # Random unit price for simplicity (in reality would match product)
        unit_price = round(random.uniform(5.0, 500.0), 2)
        item_inserts.append(f"({order_id}, {product_id}, {quantity}, {unit_price})")
        
        if len(item_inserts) == 1000:
            sql.append(f"INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES {','.join(item_inserts)};")
            item_inserts = []

    sql.append("\n")

    # 4. Create Views
    sql.append("-- Create Views")
    sql.append("""
CREATE VIEW v_customer_order_summary AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as lifetime_value
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name;
""")

    sql.append("""
CREATE VIEW v_product_sales_stats AS
SELECT 
    p.product_id,
    p.name,
    p.category,
    SUM(oi.quantity) as total_units_sold,
    SUM(oi.quantity * oi.unit_price) as total_revenue
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.name, p.category;
""")
    sql.append("\n")

    # 5. Create Triggers
    sql.append("-- Create Triggers")
    sql.append("DELIMITER //\n")
    
    sql.append("""
CREATE TRIGGER before_insert_order_items
BEFORE INSERT ON order_items
FOR EACH ROW
BEGIN
    IF NEW.quantity <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quantity must be greater than zero';
    END IF;
END //
""")

    sql.append("""
CREATE TRIGGER after_insert_order_items
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE orders 
    SET total_amount = total_amount + (NEW.quantity * NEW.unit_price)
    WHERE order_id = NEW.order_id;
    
    UPDATE products
    SET stock_quantity = stock_quantity - NEW.quantity
    WHERE product_id = NEW.product_id;
END //
""")
    sql.append("DELIMITER ;\n")

    # 6. Create Procedures
    sql.append("-- Create Procedures")
    sql.append("DELIMITER //\n")
    
    sql.append("""
CREATE PROCEDURE CreateOrder(
    IN p_customer_id INT,
    IN p_product_id INT,
    IN p_quantity INT,
    OUT p_order_id INT
)
BEGIN
    DECLARE v_unit_price DECIMAL(10,2);
    
    -- Get product price
    SELECT price INTO v_unit_price FROM products WHERE product_id = p_product_id;
    
    -- Create order
    INSERT INTO orders (customer_id, status) VALUES (p_customer_id, 'PENDING');
    SET p_order_id = LAST_INSERT_ID();
    
    -- Create item (this will trigger after_insert_order_items to update total_amount)
    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
    VALUES (p_order_id, p_product_id, p_quantity, v_unit_price);
END //
""")

    sql.append("""
CREATE PROCEDURE UpdateProductPrice(
    IN p_product_id INT,
    IN p_new_price DECIMAL(10,2)
)
BEGIN
    DECLARE v_old_price DECIMAL(10,2);
    
    -- Get old price
    SELECT price INTO v_old_price FROM products WHERE product_id = p_product_id;
    
    IF v_old_price != p_new_price THEN
        -- Log the change
        INSERT INTO price_audit_log (product_id, old_price, new_price)
        VALUES (p_product_id, v_old_price, p_new_price);
        
        -- Update the price
        UPDATE products SET price = p_new_price WHERE product_id = p_product_id;
    END IF;
END //
""")
    
    sql.append("DELIMITER ;\n")
    
    with open("sample_mysql_database.sql", "w") as f:
        f.write("\n".join(sql))
        
    print("Database SQL generated successfully in 'sample_mysql_database.sql'")
    print("Total rows generated: 2,000 customers + 500 products + 8,000 orders + 15,000 order items = 25,500 rows.")

if __name__ == "__main__":
    generate_sql()
