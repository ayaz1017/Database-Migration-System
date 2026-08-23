import mysql.connector
import random
import string
import time
import json
import uuid

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ayaz@123",
    "port": 3306
}

DB_NAME = "complex_mysql_db"
TARGET_ROWS = 150_000

def random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def main():
    print(f"Connecting to MySQL at {DB_CONFIG['host']}...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Create Database
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    cursor.execute(f"CREATE DATABASE {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")
    
    print("Creating tables with complex datatypes...")
    
    # Create main table
    cursor.execute("""
        CREATE TABLE complex_entities (
            id INT AUTO_INCREMENT PRIMARY KEY,
            uuid_col CHAR(36) NOT NULL,
            status ENUM('active', 'inactive', 'pending', 'archived') DEFAULT 'pending',
            payload JSON,
            price DECIMAL(10, 4),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            is_active BOOLEAN,
            binary_data BLOB,
            location POINT SRID 4326,
            long_text_data LONGTEXT
        ) ENGINE=InnoDB
    """)
    
    # Create logs table
    cursor.execute("""
        CREATE TABLE entity_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            entity_id INT,
            action VARCHAR(50),
            action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
    """)

    print("Creating views...")
    # Create View
    cursor.execute("""
        CREATE VIEW active_entities_view AS
        SELECT id, uuid_col, status, price, created_at, is_active
        FROM complex_entities
        WHERE status = 'active' AND is_active = TRUE
    """)

    print("Creating triggers...")
    # Create Trigger
    # Using execute with multi=False but multiple statements can be tricky.
    # So we execute it directly as a single statement.
    cursor.execute("""
        CREATE TRIGGER after_entity_insert
        AFTER INSERT ON complex_entities
        FOR EACH ROW
        BEGIN
            INSERT INTO entity_logs (entity_id, action)
            VALUES (NEW.id, 'CREATED');
        END;
    """)

    print("Creating procedures...")
    # Create Procedure
    cursor.execute("""
        CREATE PROCEDURE update_entity_status (IN p_id INT, IN p_status VARCHAR(20))
        BEGIN
            UPDATE complex_entities 
            SET status = p_status 
            WHERE id = p_id;
            
            INSERT INTO entity_logs (entity_id, action)
            VALUES (p_id, CONCAT('STATUS_UPDATED_TO_', p_status));
        END;
    """)

    print("Inserting 1,000 seed rows...")
    insert_query = """
        INSERT INTO complex_entities 
        (uuid_col, status, payload, price, is_active, binary_data, location, long_text_data) 
        VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326), %s)
    """
    
    seed_data = []
    statuses = ['active', 'inactive', 'pending', 'archived']
    for _ in range(1000):
        lat, lon = random.uniform(-90, 90), random.uniform(-180, 180)
        point_str = f"POINT({lon} {lat})"
        payload = json.dumps({
            "config": {"theme": random.choice(["dark", "light"]), "retries": random.randint(1, 5)},
            "metadata": {"tags": [random_string(5), random_string(4)], "score": random.random()}
        })
        seed_data.append((
            str(uuid.uuid4()),
            random.choice(statuses),
            payload,
            round(random.uniform(10.0, 5000.0), 4),
            random.choice([True, False]),
            random_string(20).encode('utf-8'),
            point_str,
            "Lorem ipsum " * 10
        ))
    
    cursor.execute("SET unique_checks=0")
    cursor.execute("SET foreign_key_checks=0")
    
    cursor.executemany(insert_query, seed_data)
    conn.commit()

    print("Starting exponential row doubling for 150K target...")
    current_rows = 1000
    iteration = 1
    
    # To avoid trigger overhead during mass insert, we can temporarily drop the trigger
    # But since it's just 150K, trigger execution is perfectly fine and tests the DB nicely.
    
    while current_rows < TARGET_ROWS:
        start_time = time.time()
        
        # Determine how many rows to insert to hit exactly TARGET_ROWS (or close to it)
        limit = min(current_rows, TARGET_ROWS - current_rows)
        
        # We need to regenerate UUIDs if we wanted unique UUIDs, but for test data it's often fine to copy.
        # Let's generate new UUIDs using UUID() in MySQL!
        cursor.execute(f"""
            INSERT INTO complex_entities 
            (uuid_col, status, payload, price, is_active, binary_data, location, long_text_data)
            SELECT 
                UUID(), 
                status, 
                payload, 
                price + RAND(), 
                is_active, 
                binary_data, 
                location, 
                long_text_data 
            FROM complex_entities
            LIMIT {limit}
        """)
        conn.commit()
        
        inserted = cursor.rowcount
        current_rows += inserted
        elapsed = time.time() - start_time
        print(f"  Iteration {iteration}: Inserted {inserted:,} rows. Total: {current_rows:,} (took {elapsed:.2f}s)")
        iteration += 1

    cursor.execute("SET unique_checks=1")
    cursor.execute("SET foreign_key_checks=1")
    
    # Test the procedure
    print("Testing the stored procedure...")
    cursor.execute("CALL update_entity_status(1, 'archived')")
    conn.commit()

    print(f" Finished! Database '{DB_NAME}' created with {current_rows:,} records.")
    
    conn.close()

if __name__ == "__main__":
    main()
