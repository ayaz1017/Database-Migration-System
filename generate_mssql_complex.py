import pyodbc
from faker import Faker
import random
from datetime import datetime

# Connection details
SERVER = '127.0.0.1'
USERNAME = 'sa'
PASSWORD = 'Ayaz@123'
DB_NAME = 'ComplexDB'

connection_string_master = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};UID={USERNAME};PWD={PASSWORD};DATABASE=master;TrustServerCertificate=yes;"
connection_string_db = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};UID={USERNAME};PWD={PASSWORD};DATABASE={DB_NAME};TrustServerCertificate=yes;"

try:
    print("Connecting to master to create DB...")
    conn = pyodbc.connect(connection_string_master, autocommit=True)
    cursor = conn.cursor()

    # Drop DB if exists and create
    cursor.execute(f"IF EXISTS (SELECT name FROM sys.databases WHERE name = N'{DB_NAME}') ALTER DATABASE [{DB_NAME}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    cursor.execute(f"IF EXISTS (SELECT name FROM sys.databases WHERE name = N'{DB_NAME}') DROP DATABASE [{DB_NAME}]")
    cursor.execute(f"CREATE DATABASE [{DB_NAME}]")
    cursor.close()
    conn.close()
except pyodbc.Error as e:
    print(f"Error connecting to master: {e}")
    exit(1)

print(f"Connecting to {DB_NAME} to create schema...")
conn = pyodbc.connect(connection_string_db)
cursor = conn.cursor()

schema = """
CREATE TABLE Departments (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Budget DECIMAL(18,2) NOT NULL
);

CREATE TABLE Employees (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    DeptId INT FOREIGN KEY REFERENCES Departments(Id),
    FirstName VARCHAR(100) NOT NULL,
    LastName VARCHAR(100) NOT NULL,
    Salary DECIMAL(18,2) NOT NULL,
    HireDate DATETIME NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

CREATE TABLE Customers (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name VARCHAR(200) NOT NULL,
    Email VARCHAR(200) NOT NULL,
    Region VARCHAR(50) NOT NULL
);

CREATE TABLE Orders (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    CustomerId INT FOREIGN KEY REFERENCES Customers(Id),
    OrderDate DATETIME NOT NULL,
    TotalAmount DECIMAL(18,2) NOT NULL
);

CREATE TABLE AuditLogs (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    TableName VARCHAR(100) NOT NULL,
    Action VARCHAR(100) NOT NULL,
    Timestamp DATETIME DEFAULT GETDATE()
);
"""

cursor.execute(schema)
conn.commit()

triggers_and_views = [
    """
    CREATE TRIGGER trg_Employees_Insert
    ON Employees
    AFTER INSERT
    AS
    BEGIN
        INSERT INTO AuditLogs (TableName, Action) VALUES ('Employees', 'INSERT');
    END
    """,
    """
    CREATE TRIGGER trg_Orders_Insert
    ON Orders
    AFTER INSERT
    AS
    BEGIN
        INSERT INTO AuditLogs (TableName, Action) VALUES ('Orders', 'INSERT');
    END
    """,
    """
    CREATE VIEW vw_ActiveEmployees AS
    SELECT e.Id, e.FirstName, e.LastName, d.Name AS DepartmentName, e.Salary
    FROM Employees e
    JOIN Departments d ON e.DeptId = d.Id
    WHERE e.IsActive = 1;
    """,
    """
    CREATE VIEW vw_DepartmentSummary AS
    SELECT d.Name AS DepartmentName, COUNT(e.Id) AS EmployeeCount, SUM(e.Salary) AS TotalSalary
    FROM Departments d
    LEFT JOIN Employees e ON d.Id = e.DeptId
    GROUP BY d.Name;
    """,
    """
    CREATE PROCEDURE sp_GiveRaise
        @DeptId INT,
        @Percentage DECIMAL(5,2)
    AS
    BEGIN
        UPDATE Employees
        SET Salary = Salary + (Salary * @Percentage / 100)
        WHERE DeptId = @DeptId;
    END
    """,
    """
    CREATE PROCEDURE sp_GetCustomerOrders
        @CustomerId INT
    AS
    BEGIN
        SELECT Id, OrderDate, TotalAmount
        FROM Orders
        WHERE CustomerId = @CustomerId;
    END
    """
]

for tv in triggers_and_views:
    cursor.execute(tv)
    
conn.commit()
print("Schema, views, procedures, and triggers created.")

# Data Generation
print("Generating data...")
cursor.fast_executemany = True
fake = Faker()

# 1. Departments (10)
depts = []
for i in range(10):
    depts.append((fake.company()[:100], round(random.uniform(500000, 5000000), 2)))
cursor.executemany("INSERT INTO Departments (Name, Budget) VALUES (?, ?)", depts)
conn.commit()

# 2. Employees (20,000)
emps = []
for i in range(20000):
    emps.append((
        random.randint(1, 10),
        fake.first_name()[:100],
        fake.last_name()[:100],
        round(random.uniform(40000, 200000), 2),
        fake.date_time_between(start_date='-10y', end_date='now'),
        random.choice([1, 1, 1, 0])
    ))
print("Inserting 20,000 Employees...")
chunk_size = 5000
for i in range(0, len(emps), chunk_size):
    cursor.executemany("INSERT INTO Employees (DeptId, FirstName, LastName, Salary, HireDate, IsActive) VALUES (?, ?, ?, ?, ?, ?)", emps[i:i+chunk_size])
conn.commit()

# 3. Customers (30,000)
custs = []
for i in range(30000):
    custs.append((
        fake.name()[:200],
        fake.email()[:200],
        random.choice(['North', 'South', 'East', 'West', 'Central'])
    ))
print("Inserting 30,000 Customers...")
for i in range(0, len(custs), chunk_size):
    cursor.executemany("INSERT INTO Customers (Name, Email, Region) VALUES (?, ?, ?)", custs[i:i+chunk_size])
conn.commit()

# 4. Orders (50,000)
orders = []
for i in range(50000):
    orders.append((
        random.randint(1, 30000),
        fake.date_time_between(start_date='-5y', end_date='now'),
        round(random.uniform(10, 5000), 2)
    ))
print("Inserting 50,000 Orders...")
for i in range(0, len(orders), chunk_size):
    cursor.executemany("INSERT INTO Orders (CustomerId, OrderDate, TotalAmount) VALUES (?, ?, ?)", orders[i:i+chunk_size])
conn.commit()

cursor.close()
conn.close()
print("Data generation complete! Total ~100K records.")
