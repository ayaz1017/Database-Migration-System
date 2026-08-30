import pyodbc
import random
import string
import time
from datetime import datetime, timedelta

def get_connection(dbname="master"):
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.30.228.160,1433;"
        "UID=sa;"
        "PWD=Ayaz@123;"
        f"DATABASE={dbname};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str, autocommit=True)

def create_schema():
    print("Connecting to master to create database...")
    conn = get_connection("master")
    cursor = conn.cursor()
    
    try:
        cursor.execute("DROP DATABASE ComplexDB_500K")
    except Exception:
        pass
        
    cursor.execute("CREATE DATABASE ComplexDB_500K")
    conn.close()
    
    print("Creating tables, views, triggers, and procedures...")
    conn = get_connection("ComplexDB_500K")
    cursor = conn.cursor()
    
    schema_sql = """
    CREATE TABLE Departments (
        DepartmentID INT IDENTITY(1,1) PRIMARY KEY,
        Name VARCHAR(100) NOT NULL,
        Location VARCHAR(100)
    );

    CREATE TABLE Employees (
        EmployeeID INT IDENTITY(1,1) PRIMARY KEY,
        DepartmentID INT FOREIGN KEY REFERENCES Departments(DepartmentID),
        FirstName VARCHAR(50) NOT NULL,
        LastName VARCHAR(50) NOT NULL,
        Email VARCHAR(100) UNIQUE,
        Salary DECIMAL(10, 2),
        HireDate DATE
    );

    CREATE TABLE Customers (
        CustomerID INT IDENTITY(1,1) PRIMARY KEY,
        FirstName VARCHAR(50) NOT NULL,
        LastName VARCHAR(50) NOT NULL,
        Email VARCHAR(100) UNIQUE,
        RegistrationDate DATETIME
    );

    CREATE TABLE Products (
        ProductID INT IDENTITY(1,1) PRIMARY KEY,
        Name VARCHAR(100) NOT NULL,
        Category VARCHAR(50),
        Price DECIMAL(10, 2),
        StockQuantity INT
    );

    CREATE TABLE Orders (
        OrderID INT IDENTITY(1,1) PRIMARY KEY,
        CustomerID INT FOREIGN KEY REFERENCES Customers(CustomerID),
        OrderDate DATETIME DEFAULT GETDATE(),
        TotalAmount DECIMAL(12, 2) DEFAULT 0,
        Status VARCHAR(20)
    );

    CREATE TABLE OrderItems (
        OrderItemID INT IDENTITY(1,1) PRIMARY KEY,
        OrderID INT FOREIGN KEY REFERENCES Orders(OrderID),
        ProductID INT FOREIGN KEY REFERENCES Products(ProductID),
        Quantity INT,
        UnitPrice DECIMAL(10, 2)
    );
    
    CREATE TABLE AuditLog (
        LogID INT IDENTITY(1,1) PRIMARY KEY,
        TableName VARCHAR(50),
        Action VARCHAR(50),
        ActionDate DATETIME DEFAULT GETDATE()
    );
    """
    cursor.execute(schema_sql)
    
    print("Creating Views...")
    cursor.execute("""
    CREATE VIEW vw_CustomerOrders AS
    SELECT 
        c.CustomerID, c.FirstName, c.LastName,
        o.OrderID, o.OrderDate, o.TotalAmount
    FROM Customers c
    JOIN Orders o ON c.CustomerID = o.CustomerID;
    """)

    cursor.execute("""
    CREATE VIEW vw_ProductSales AS
    SELECT 
        p.ProductID, p.Name,
        SUM(oi.Quantity) AS TotalSold,
        SUM(oi.Quantity * oi.UnitPrice) AS TotalRevenue
    FROM Products p
    JOIN OrderItems oi ON p.ProductID = oi.ProductID
    GROUP BY p.ProductID, p.Name;
    """)
    
    print("Creating Triggers...")
    cursor.execute("""
    CREATE TRIGGER trg_AfterOrderInsert
    ON Orders
    AFTER INSERT
    AS
    BEGIN
        INSERT INTO AuditLog (TableName, Action)
        VALUES ('Orders', 'INSERT');
    END;
    """)
    
    cursor.execute("""
    CREATE TRIGGER trg_UpdateStock
    ON OrderItems
    AFTER INSERT
    AS
    BEGIN
        UPDATE p
        SET p.StockQuantity = p.StockQuantity - i.Quantity
        FROM Products p
        INNER JOIN inserted i ON p.ProductID = i.ProductID;
    END;
    """)
    
    print("Creating Stored Procedures...")
    cursor.execute("""
    CREATE PROCEDURE sp_GetCustomerOrderHistory
        @CustomerID INT
    AS
    BEGIN
        SELECT OrderID, OrderDate, TotalAmount, Status
        FROM Orders
        WHERE CustomerID = @CustomerID
        ORDER BY OrderDate DESC;
    END;
    """)

    cursor.execute("""
    CREATE PROCEDURE sp_UpdateOrderTotal
        @OrderID INT
    AS
    BEGIN
        DECLARE @Total DECIMAL(12,2);
        
        SELECT @Total = SUM(Quantity * UnitPrice)
        FROM OrderItems
        WHERE OrderID = @OrderID;
        
        UPDATE Orders
        SET TotalAmount = @Total
        WHERE OrderID = @OrderID;
    END;
    """)
    
    conn.close()

def random_string(length):
    return ''.join(random.choices(string.ascii_letters, k=length))

def generate_data():
    conn = get_connection("ComplexDB_500K")
    cursor = conn.cursor()
    cursor.fast_executemany = True
    
    print("Generating data (Target: ~500k rows)...")
    
    # 1. Departments (100 rows)
    print("Inserting 100 Departments...")
    depts = [(f"Dept_{i}", f"Location_{random.choice(['NY', 'SF', 'LA', 'CHI', 'TX'])}") for i in range(1, 101)]
    cursor.executemany("INSERT INTO Departments (Name, Location) VALUES (?, ?)", depts)
    
    # 2. Employees (5,000 rows)
    print("Inserting 5,000 Employees...")
    emps = []
    for i in range(5000):
        emps.append((
            random.randint(1, 100),
            f"FN_{random_string(5)}",
            f"LN_{random_string(7)}",
            f"emp_{i}_{random_string(5)}@company.com",
            round(random.uniform(30000, 150000), 2),
            (datetime.now() - timedelta(days=random.randint(1, 3650))).strftime("%Y-%m-%d")
        ))
    cursor.executemany("INSERT INTO Employees (DepartmentID, FirstName, LastName, Email, Salary, HireDate) VALUES (?, ?, ?, ?, ?, ?)", emps)
    
    # 3. Products (10,000 rows)
    print("Inserting 10,000 Products...")
    prods = []
    for i in range(10000):
        prods.append((
            f"Product_{random_string(8)}",
            random.choice(['Electronics', 'Clothing', 'Food', 'Toys', 'Books']),
            round(random.uniform(5, 1000), 2),
            random.randint(1000, 10000)
        ))
    cursor.executemany("INSERT INTO Products (Name, Category, Price, StockQuantity) VALUES (?, ?, ?, ?)", prods)
    
    # 4. Customers (80,000 rows)
    print("Inserting 80,000 Customers...")
    custs = []
    for i in range(80000):
        custs.append((
            f"CFN_{random_string(4)}",
            f"CLN_{random_string(6)}",
            f"cust_{i}_{random_string(4)}@email.com",
            (datetime.now() - timedelta(days=random.randint(1, 1000))).strftime("%Y-%m-%d %H:%M:%S")
        ))
    
    # Insert customers in chunks
    chunk_size = 10000
    for i in range(0, len(custs), chunk_size):
        cursor.executemany("INSERT INTO Customers (FirstName, LastName, Email, RegistrationDate) VALUES (?, ?, ?, ?)", custs[i:i+chunk_size])

    # 5. Orders (104,900 rows)
    print("Inserting 104,900 Orders...")
    orders = []
    for i in range(104900):
        orders.append((
            random.randint(1, 80000),
            (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d %H:%M:%S"),
            0.0, # TotalAmount calculated later
            random.choice(['Pending', 'Shipped', 'Delivered', 'Cancelled'])
        ))
    
    for i in range(0, len(orders), chunk_size):
        cursor.executemany("INSERT INTO Orders (CustomerID, OrderDate, TotalAmount, Status) VALUES (?, ?, ?, ?)", orders[i:i+chunk_size])

    # 6. OrderItems (300,000 rows)
    print("Inserting 300,000 OrderItems...")
    items = []
    for i in range(300000):
        order_id = random.randint(1, 104900)
        product_id = random.randint(1, 10000)
        quantity = random.randint(1, 5)
        # Using a dummy unit price, trigger/procedures update totals
        unit_price = round(random.uniform(5, 500), 2) 
        items.append((order_id, product_id, quantity, unit_price))
        
    for i in range(0, len(items), chunk_size):
        cursor.executemany("INSERT INTO OrderItems (OrderID, ProductID, Quantity, UnitPrice) VALUES (?, ?, ?, ?)", items[i:i+chunk_size])
        if (i + chunk_size) % 50000 == 0:
            print(f"Inserted {i + chunk_size} OrderItems...")

    print("Data generation complete!")
    print("Summary of rows:")
    print(f"Departments: 100")
    print(f"Employees: 5,000")
    print(f"Products: 10,000")
    print(f"Customers: 80,000")
    print(f"Orders: 104,900")
    print(f"OrderItems: 300,000")
    print(f"Total rows (approx): 500,000")
    
    conn.close()

if __name__ == "__main__":
    start_time = time.time()
    try:
        create_schema()
        generate_data()
        print(f"Total execution time: {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print(f"Error: {e}")
