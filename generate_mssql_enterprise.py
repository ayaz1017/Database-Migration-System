import os
import random
from faker import Faker
from datetime import timedelta, date, datetime
import io

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_FILE = "EnterpriseDB_Complex.sql"

# Configurations
NUM_CUSTOMERS = 10000
NUM_ADDRESSES = 15000
NUM_DEPARTMENTS = 20
NUM_EMPLOYEES = 500
NUM_SUPPLIERS = 300
NUM_CATEGORIES = 100
NUM_PRODUCTS = 3000
NUM_WAREHOUSES = 15
NUM_INVENTORY = 6000
NUM_ORDERS = 12000
NUM_ORDER_ITEMS = 18000
NUM_PAYMENTS = 10000
NUM_SHIPMENTS = 8000
NUM_REVIEWS = 3000
NUM_RETURNS = 1500
NUM_COUPONS = 200
NUM_CUSTOMER_COUPONS = 5000
NUM_ATTENDANCE = 8000
NUM_PAYROLL = 6000
NUM_AUDIT_LOGS = 5000

def write_ddl(f):
    f.write("-- =========================================\n")
    f.write("-- EnterpriseDB_Complex Generation Script\n")
    f.write("-- =========================================\n\n")
    f.write("USE master;\nGO\n")
    f.write("IF DB_ID('EnterpriseDB_Complex') IS NOT NULL\n")
    f.write("BEGIN\n")
    f.write("    ALTER DATABASE EnterpriseDB_Complex SET SINGLE_USER WITH ROLLBACK IMMEDIATE;\n")
    f.write("    DROP DATABASE EnterpriseDB_Complex;\n")
    f.write("END\nGO\n")
    f.write("CREATE DATABASE EnterpriseDB_Complex;\nGO\n")
    f.write("USE EnterpriseDB_Complex;\nGO\n\n")

    f.write("-- 1. Departments\n")
    f.write("CREATE TABLE Departments (\n")
    f.write("    DepartmentID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    DepartmentName NVARCHAR(100) NOT NULL UNIQUE,\n")
    f.write("    Budget DECIMAL(18,2) DEFAULT 0.00\n")
    f.write(");\nGO\n\n")

    f.write("-- 2. Employees\n")
    f.write("CREATE TABLE Employees (\n")
    f.write("    EmployeeID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    FirstName NVARCHAR(50) NOT NULL,\n")
    f.write("    LastName NVARCHAR(50) NOT NULL,\n")
    f.write("    Email NVARCHAR(150) NOT NULL UNIQUE,\n")
    f.write("    DepartmentID INT NOT NULL FOREIGN KEY REFERENCES Departments(DepartmentID),\n")
    f.write("    ManagerID INT NULL FOREIGN KEY REFERENCES Employees(EmployeeID),\n")
    f.write("    HireDate DATE NOT NULL DEFAULT GETDATE(),\n")
    f.write("    Salary DECIMAL(18,2) NOT NULL CHECK (Salary > 0),\n")
    f.write("    Status NVARCHAR(20) DEFAULT 'Active' CHECK (Status IN ('Active', 'On Leave', 'Terminated'))\n")
    f.write(");\nGO\n\n")

    f.write("-- 3. Customers\n")
    f.write("CREATE TABLE Customers (\n")
    f.write("    CustomerID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    FirstName NVARCHAR(50) NOT NULL,\n")
    f.write("    LastName NVARCHAR(50) NOT NULL,\n")
    f.write("    Email NVARCHAR(150) NOT NULL UNIQUE,\n")
    f.write("    Phone NVARCHAR(30),\n")
    f.write("    DOB DATE,\n")
    f.write("    Gender CHAR(1) CHECK (Gender IN ('M', 'F', 'O', 'U')),\n")
    f.write("    LoyaltyPoints INT DEFAULT 0,\n")
    f.write("    CustomerType NVARCHAR(20) DEFAULT 'Standard',\n")
    f.write("    RegistrationDate DATETIME DEFAULT GETDATE(),\n")
    f.write("    Status NVARCHAR(20) DEFAULT 'Active'\n")
    f.write(");\nGO\n\n")

    f.write("-- 4. Addresses\n")
    f.write("CREATE TABLE Addresses (\n")
    f.write("    AddressID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    CustomerID INT NOT NULL FOREIGN KEY REFERENCES Customers(CustomerID) ON DELETE CASCADE,\n")
    f.write("    AddressType NVARCHAR(20) CHECK (AddressType IN ('Billing', 'Shipping')),\n")
    f.write("    StreetAddress NVARCHAR(255) NOT NULL,\n")
    f.write("    City NVARCHAR(100) NOT NULL,\n")
    f.write("    State NVARCHAR(100),\n")
    f.write("    ZipCode NVARCHAR(20),\n")
    f.write("    Country NVARCHAR(100) NOT NULL\n")
    f.write(");\nGO\n\n")

    f.write("-- 5. Suppliers\n")
    f.write("CREATE TABLE Suppliers (\n")
    f.write("    SupplierID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    SupplierName NVARCHAR(150) NOT NULL,\n")
    f.write("    ContactName NVARCHAR(100),\n")
    f.write("    ContactEmail NVARCHAR(150),\n")
    f.write("    Phone NVARCHAR(30),\n")
    f.write("    City NVARCHAR(100),\n")
    f.write("    Country NVARCHAR(100)\n")
    f.write(");\nGO\n\n")

    f.write("-- 6. Categories\n")
    f.write("CREATE TABLE Categories (\n")
    f.write("    CategoryID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    CategoryName NVARCHAR(100) NOT NULL UNIQUE,\n")
    f.write("    Description NVARCHAR(MAX)\n")
    f.write(");\nGO\n\n")

    f.write("-- 7. Products\n")
    f.write("CREATE TABLE Products (\n")
    f.write("    ProductID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    SKU NVARCHAR(50) NOT NULL UNIQUE,\n")
    f.write("    Barcode NVARCHAR(100),\n")
    f.write("    ProductName NVARCHAR(200) NOT NULL,\n")
    f.write("    Brand NVARCHAR(100),\n")
    f.write("    CategoryID INT NOT NULL FOREIGN KEY REFERENCES Categories(CategoryID),\n")
    f.write("    SupplierID INT NOT NULL FOREIGN KEY REFERENCES Suppliers(SupplierID),\n")
    f.write("    CostPrice DECIMAL(18,2) NOT NULL CHECK (CostPrice >= 0),\n")
    f.write("    SellingPrice DECIMAL(18,2) NOT NULL CHECK (SellingPrice >= 0),\n")
    f.write("    Discount DECIMAL(5,2) DEFAULT 0.00 CHECK (Discount >= 0 AND Discount <= 100),\n")
    f.write("    Weight DECIMAL(10,2),\n")
    f.write("    WarrantyMonths INT DEFAULT 12,\n")
    f.write("    StockStatus NVARCHAR(20) DEFAULT 'In Stock',\n")
    f.write("    ProfitMargin AS ((SellingPrice - CostPrice) / NULLIF(CostPrice, 0)) PERSISTED\n")
    f.write(");\nGO\n\n")

    f.write("-- 8. Warehouses\n")
    f.write("CREATE TABLE Warehouses (\n")
    f.write("    WarehouseID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    WarehouseName NVARCHAR(100) NOT NULL,\n")
    f.write("    Location NVARCHAR(200)\n")
    f.write(");\nGO\n\n")

    f.write("-- 9. Inventory\n")
    f.write("CREATE TABLE Inventory (\n")
    f.write("    WarehouseID INT NOT NULL FOREIGN KEY REFERENCES Warehouses(WarehouseID),\n")
    f.write("    ProductID INT NOT NULL FOREIGN KEY REFERENCES Products(ProductID),\n")
    f.write("    Quantity INT NOT NULL DEFAULT 0 CHECK (Quantity >= 0),\n")
    f.write("    LastUpdated DATETIME DEFAULT GETDATE(),\n")
    f.write("    PRIMARY KEY (WarehouseID, ProductID)\n")
    f.write(");\nGO\n\n")

    f.write("-- 10. Coupons\n")
    f.write("CREATE TABLE Coupons (\n")
    f.write("    CouponID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    CouponCode NVARCHAR(50) NOT NULL UNIQUE,\n")
    f.write("    DiscountAmount DECIMAL(18,2) NOT NULL,\n")
    f.write("    IsActive BIT DEFAULT 1,\n")
    f.write("    ExpiryDate DATE\n")
    f.write(");\nGO\n\n")

    f.write("-- 11. CustomerCoupons\n")
    f.write("CREATE TABLE CustomerCoupons (\n")
    f.write("    CustomerID INT NOT NULL FOREIGN KEY REFERENCES Customers(CustomerID),\n")
    f.write("    CouponID INT NOT NULL FOREIGN KEY REFERENCES Coupons(CouponID),\n")
    f.write("    AssignedDate DATETIME DEFAULT GETDATE(),\n")
    f.write("    IsUsed BIT DEFAULT 0,\n")
    f.write("    PRIMARY KEY (CustomerID, CouponID)\n")
    f.write(");\nGO\n\n")

    f.write("-- 12. Orders\n")
    f.write("CREATE TABLE Orders (\n")
    f.write("    OrderID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    CustomerID INT NOT NULL FOREIGN KEY REFERENCES Customers(CustomerID),\n")
    f.write("    OrderDate DATETIME DEFAULT GETDATE(),\n")
    f.write("    TotalAmount DECIMAL(18,2) DEFAULT 0.00,\n")
    f.write("    OrderStatus NVARCHAR(50) DEFAULT 'Pending' CHECK (OrderStatus IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned')),\n")
    f.write("    ShippingAddressID INT FOREIGN KEY REFERENCES Addresses(AddressID),\n")
    f.write("    CouponID INT NULL FOREIGN KEY REFERENCES Coupons(CouponID)\n")
    f.write(");\nGO\n\n")

    f.write("-- 13. OrderItems\n")
    f.write("CREATE TABLE OrderItems (\n")
    f.write("    OrderItemID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    OrderID INT NOT NULL FOREIGN KEY REFERENCES Orders(OrderID) ON DELETE CASCADE,\n")
    f.write("    ProductID INT NOT NULL FOREIGN KEY REFERENCES Products(ProductID),\n")
    f.write("    Quantity INT NOT NULL CHECK (Quantity > 0),\n")
    f.write("    UnitPrice DECIMAL(18,2) NOT NULL,\n")
    f.write("    LineTotal AS (Quantity * UnitPrice) PERSISTED\n")
    f.write(");\nGO\n\n")

    f.write("-- 14. Payments\n")
    f.write("CREATE TABLE Payments (\n")
    f.write("    PaymentID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    OrderID INT NOT NULL FOREIGN KEY REFERENCES Orders(OrderID) ON DELETE CASCADE,\n")
    f.write("    PaymentDate DATETIME DEFAULT GETDATE(),\n")
    f.write("    Amount DECIMAL(18,2) NOT NULL CHECK (Amount >= 0),\n")
    f.write("    PaymentMethod NVARCHAR(50) CHECK (PaymentMethod IN ('Cash', 'Card', 'UPI', 'Net Banking', 'Wallet')),\n")
    f.write("    PaymentStatus NVARCHAR(50) DEFAULT 'Completed' CHECK (PaymentStatus IN ('Pending', 'Completed', 'Failed', 'Refunded'))\n")
    f.write(");\nGO\n\n")

    f.write("-- 15. Shipments\n")
    f.write("CREATE TABLE Shipments (\n")
    f.write("    ShipmentID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    OrderID INT NOT NULL FOREIGN KEY REFERENCES Orders(OrderID),\n")
    f.write("    TrackingNumber NVARCHAR(100),\n")
    f.write("    Carrier NVARCHAR(100),\n")
    f.write("    ShipDate DATETIME,\n")
    f.write("    EstimatedDelivery DATETIME,\n")
    f.write("    ActualDelivery DATETIME,\n")
    f.write("    Status NVARCHAR(50) DEFAULT 'In Transit'\n")
    f.write(");\nGO\n\n")

    f.write("-- 16. Reviews\n")
    f.write("CREATE TABLE Reviews (\n")
    f.write("    ReviewID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    ProductID INT NOT NULL FOREIGN KEY REFERENCES Products(ProductID) ON DELETE CASCADE,\n")
    f.write("    CustomerID INT NOT NULL FOREIGN KEY REFERENCES Customers(CustomerID) ON DELETE CASCADE,\n")
    f.write("    Rating INT CHECK (Rating BETWEEN 1 AND 5),\n")
    f.write("    Comment NVARCHAR(MAX),\n")
    f.write("    ReviewDate DATETIME DEFAULT GETDATE()\n")
    f.write(");\nGO\n\n")

    f.write("-- 17. Returns\n")
    f.write("CREATE TABLE Returns (\n")
    f.write("    ReturnID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    OrderID INT NOT NULL FOREIGN KEY REFERENCES Orders(OrderID),\n")
    f.write("    ProductID INT NOT NULL FOREIGN KEY REFERENCES Products(ProductID),\n")
    f.write("    ReturnDate DATETIME DEFAULT GETDATE(),\n")
    f.write("    Reason NVARCHAR(255),\n")
    f.write("    RefundAmount DECIMAL(18,2),\n")
    f.write("    Status NVARCHAR(50) DEFAULT 'Pending'\n")
    f.write(");\nGO\n\n")

    f.write("-- 18. EmployeeAttendance\n")
    f.write("CREATE TABLE EmployeeAttendance (\n")
    f.write("    AttendanceID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    EmployeeID INT NOT NULL FOREIGN KEY REFERENCES Employees(EmployeeID) ON DELETE CASCADE,\n")
    f.write("    WorkDate DATE NOT NULL,\n")
    f.write("    CheckInTime TIME,\n")
    f.write("    CheckOutTime TIME,\n")
    f.write("    Status NVARCHAR(20) DEFAULT 'Present' CHECK (Status IN ('Present', 'Absent', 'Half Day', 'Leave')),\n")
    f.write("    UNIQUE (EmployeeID, WorkDate)\n")
    f.write(");\nGO\n\n")

    f.write("-- 19. Payroll\n")
    f.write("CREATE TABLE Payroll (\n")
    f.write("    PayrollID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    EmployeeID INT NOT NULL FOREIGN KEY REFERENCES Employees(EmployeeID) ON DELETE CASCADE,\n")
    f.write("    PayPeriodStart DATE NOT NULL,\n")
    f.write("    PayPeriodEnd DATE NOT NULL,\n")
    f.write("    BaseSalary DECIMAL(18,2) NOT NULL,\n")
    f.write("    Bonus DECIMAL(18,2) DEFAULT 0.00,\n")
    f.write("    Deductions DECIMAL(18,2) DEFAULT 0.00,\n")
    f.write("    NetPay AS (BaseSalary + Bonus - Deductions) PERSISTED,\n")
    f.write("    PaymentDate DATETIME\n")
    f.write(");\nGO\n\n")

    f.write("-- 20. AuditLogs\n")
    f.write("CREATE TABLE AuditLogs (\n")
    f.write("    LogID INT IDENTITY(1,1) PRIMARY KEY,\n")
    f.write("    TableName NVARCHAR(100) NOT NULL,\n")
    f.write("    Operation NVARCHAR(50) NOT NULL,\n")
    f.write("    RecordID INT NOT NULL,\n")
    f.write("    OldValue NVARCHAR(MAX),\n")
    f.write("    NewValue NVARCHAR(MAX),\n")
    f.write("    ChangedBy NVARCHAR(100) DEFAULT SYSTEM_USER,\n")
    f.write("    ChangedDate DATETIME DEFAULT GETDATE()\n")
    f.write(");\nGO\n\n")

def write_indexes_and_advanced(f):
    f.write("-- =========================================\n")
    f.write("-- Indexes\n")
    f.write("-- =========================================\n")
    f.write("CREATE NONCLUSTERED INDEX IX_Customers_Email ON Customers(Email);\nGO\n")
    f.write("CREATE NONCLUSTERED INDEX IX_Products_Category ON Products(CategoryID);\nGO\n")
    f.write("CREATE NONCLUSTERED INDEX IX_Orders_Customer ON Orders(CustomerID);\nGO\n")
    f.write("CREATE NONCLUSTERED INDEX IX_OrderItems_Order ON OrderItems(OrderID);\nGO\n")
    f.write("CREATE UNIQUE NONCLUSTERED INDEX UQ_Inventory_Warehouse_Product ON Inventory(WarehouseID, ProductID);\nGO\n")
    f.write("CREATE NONCLUSTERED INDEX IX_Payments_Order ON Payments(OrderID);\nGO\n")
    f.write("CREATE FILTERED INDEX FIX_Orders_Pending ON Orders(OrderStatus) WHERE OrderStatus = 'Pending';\nGO\n\n")

    f.write("-- =========================================\n")
    f.write("-- Views\n")
    f.write("-- =========================================\n")
    f.write("CREATE VIEW vw_OrderSummary AS\n")
    f.write("SELECT o.OrderID, o.OrderDate, c.FirstName + ' ' + c.LastName AS CustomerName, o.TotalAmount, o.OrderStatus\n")
    f.write("FROM Orders o JOIN Customers c ON o.CustomerID = c.CustomerID;\nGO\n\n")
    
    f.write("CREATE VIEW vw_ProductSales AS\n")
    f.write("SELECT p.ProductID, p.ProductName, SUM(oi.Quantity) AS TotalSold, SUM(oi.LineTotal) AS Revenue\n")
    f.write("FROM Products p JOIN OrderItems oi ON p.ProductID = oi.ProductID\n")
    f.write("GROUP BY p.ProductID, p.ProductName;\nGO\n\n")

    f.write("CREATE VIEW vw_EmployeePayroll AS\n")
    f.write("SELECT e.EmployeeID, e.FirstName + ' ' + e.LastName AS EmployeeName, d.DepartmentName, p.PayPeriodStart, p.NetPay\n")
    f.write("FROM Employees e JOIN Departments d ON e.DepartmentID = d.DepartmentID\n")
    f.write("JOIN Payroll p ON e.EmployeeID = p.EmployeeID;\nGO\n\n")

    f.write("CREATE VIEW vw_LowInventory AS\n")
    f.write("SELECT w.WarehouseName, p.ProductName, i.Quantity\n")
    f.write("FROM Inventory i JOIN Warehouses w ON i.WarehouseID = w.WarehouseID\n")
    f.write("JOIN Products p ON i.ProductID = p.ProductID\n")
    f.write("WHERE i.Quantity < 10;\nGO\n\n")

    f.write("-- =========================================\n")
    f.write("-- Functions\n")
    f.write("-- =========================================\n")
    f.write("CREATE FUNCTION fn_TotalOrderValue(@OrderID INT)\n")
    f.write("RETURNS DECIMAL(18,2)\n")
    f.write("AS\nBEGIN\n")
    f.write("    DECLARE @Total DECIMAL(18,2);\n")
    f.write("    SELECT @Total = SUM(LineTotal) FROM OrderItems WHERE OrderID = @OrderID;\n")
    f.write("    RETURN ISNULL(@Total, 0);\n")
    f.write("END;\nGO\n\n")

    f.write("CREATE FUNCTION fn_CustomerLifetimeValue(@CustomerID INT)\n")
    f.write("RETURNS DECIMAL(18,2)\n")
    f.write("AS\nBEGIN\n")
    f.write("    DECLARE @LTV DECIMAL(18,2);\n")
    f.write("    SELECT @LTV = SUM(TotalAmount) FROM Orders WHERE CustomerID = @CustomerID AND OrderStatus = 'Delivered';\n")
    f.write("    RETURN ISNULL(@LTV, 0);\n")
    f.write("END;\nGO\n\n")

    f.write("-- =========================================\n")
    f.write("-- Triggers\n")
    f.write("-- =========================================\n")
    f.write("CREATE TRIGGER trg_AuditProductPrice\n")
    f.write("ON Products\nAFTER UPDATE\nAS\nBEGIN\n")
    f.write("    SET NOCOUNT ON;\n")
    f.write("    IF UPDATE(SellingPrice)\n")
    f.write("    BEGIN\n")
    f.write("        INSERT INTO AuditLogs (TableName, Operation, RecordID, OldValue, NewValue)\n")
    f.write("        SELECT 'Products', 'UPDATE', i.ProductID, CAST(d.SellingPrice AS NVARCHAR), CAST(i.SellingPrice AS NVARCHAR)\n")
    f.write("        FROM inserted i JOIN deleted d ON i.ProductID = d.ProductID\n")
    f.write("        WHERE i.SellingPrice <> d.SellingPrice;\n")
    f.write("    END\n")
    f.write("END;\nGO\n\n")

    f.write("CREATE TRIGGER trg_PreventNegativeStock\n")
    f.write("ON Inventory\nINSTEAD OF UPDATE\nAS\nBEGIN\n")
    f.write("    IF EXISTS (SELECT 1 FROM inserted WHERE Quantity < 0)\n")
    f.write("    BEGIN\n")
    f.write("        RAISERROR('Cannot update inventory to a negative quantity.', 16, 1);\n")
    f.write("        ROLLBACK TRANSACTION;\n")
    f.write("    END\n    ELSE\n    BEGIN\n")
    f.write("        UPDATE Inventory SET Quantity = i.Quantity, LastUpdated = GETDATE()\n")
    f.write("        FROM Inventory inv JOIN inserted i ON inv.ProductID = i.ProductID AND inv.WarehouseID = i.WarehouseID;\n")
    f.write("    END\n")
    f.write("END;\nGO\n\n")

    f.write("-- =========================================\n")
    f.write("-- Stored Procedures\n")
    f.write("-- =========================================\n")
    f.write("CREATE PROCEDURE sp_CreateOrder\n")
    f.write("    @CustomerID INT, @ShippingAddressID INT, @CouponID INT = NULL, @NewOrderID INT OUTPUT\n")
    f.write("AS\nBEGIN\n")
    f.write("    BEGIN TRY\n")
    f.write("        BEGIN TRANSACTION;\n")
    f.write("        INSERT INTO Orders (CustomerID, OrderDate, OrderStatus, ShippingAddressID, CouponID)\n")
    f.write("        VALUES (@CustomerID, GETDATE(), 'Pending', @ShippingAddressID, @CouponID);\n")
    f.write("        SET @NewOrderID = SCOPE_IDENTITY();\n")
    f.write("        COMMIT TRANSACTION;\n")
    f.write("    END TRY\n")
    f.write("    BEGIN CATCH\n")
    f.write("        ROLLBACK TRANSACTION;\n")
    f.write("        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();\n")
    f.write("        RAISERROR(@ErrMsg, 16, 1);\n")
    f.write("    END CATCH\n")
    f.write("END;\nGO\n\n")

def escape_str(s):
    if s is None:
        return 'NULL'
    return f"'{str(s).replace(chr(39), chr(39)+chr(39))}'"

def batch_insert(f, table_name, columns, values_list, batch_size=1000):
    cols_str = ', '.join(columns)
    for i in range(0, len(values_list), batch_size):
        batch = values_list[i:i+batch_size]
        f.write(f"INSERT INTO {table_name} ({cols_str}) VALUES\n")
        f.write(",\n".join([f"({', '.join(map(str, row))})" for row in batch]))
        f.write(";\n")

def generate_data(f):
    f.write("-- =========================================\n")
    f.write("-- Data Generation\n")
    f.write("-- =========================================\n")

    print("Generating Departments...")
    depts = [("HR", 50000), ("IT", 120000), ("Sales", 80000), ("Marketing", 75000), ("Finance", 90000)]
    for i in range(5, NUM_DEPARTMENTS):
        depts.append((fake.company_suffix() + " " + fake.job().split()[0] + " " + str(i), random.randint(10000, 150000)))
    batch_insert(f, "Departments", ["DepartmentName", "Budget"], [(escape_str(d[0]), d[1]) for d in depts])

    print("Generating Employees...")
    emps = []
    for i in range(1, NUM_EMPLOYEES + 1):
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        dept_id = random.randint(1, NUM_DEPARTMENTS)
        mgr_id = random.randint(1, i-1) if i > 1 else 'NULL'
        hire = fake.date_between(start_date='-5y', end_date='today')
        sal = round(random.uniform(40000, 150000), 2)
        status = random.choices(['Active', 'On Leave', 'Terminated'], weights=[90, 5, 5])[0]
        emps.append((escape_str(first), escape_str(last), escape_str(email), dept_id, mgr_id, escape_str(hire), sal, escape_str(status)))
    batch_insert(f, "Employees", ["FirstName", "LastName", "Email", "DepartmentID", "ManagerID", "HireDate", "Salary", "Status"], emps)

    print("Generating Customers...")
    custs = []
    for i in range(1, NUM_CUSTOMERS + 1):
        first = fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}.{last.lower()}{i}@mail.com"
        phone = fake.numerify(text='###-###-####')
        dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
        gen = random.choice(['M', 'F', 'O', 'U'])
        loyalty = random.randint(0, 5000)
        ctype = random.choices(['Standard', 'Premium', 'VIP'], weights=[70, 20, 10])[0]
        reg = fake.date_time_between(start_date='-5y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
        status = random.choices(['Active', 'Inactive'], weights=[95, 5])[0]
        custs.append((escape_str(first), escape_str(last), escape_str(email), escape_str(phone), escape_str(dob), escape_str(gen), loyalty, escape_str(ctype), escape_str(reg), escape_str(status)))
    batch_insert(f, "Customers", ["FirstName", "LastName", "Email", "Phone", "DOB", "Gender", "LoyaltyPoints", "CustomerType", "RegistrationDate", "Status"], custs)

    print("Generating Addresses...")
    addrs = []
    for i in range(NUM_ADDRESSES):
        cid = random.randint(1, NUM_CUSTOMERS)
        atype = random.choice(['Billing', 'Shipping'])
        street = fake.street_address()
        city = fake.city()
        state = fake.state()
        zipc = fake.postcode()
        country = fake.country()
        addrs.append((cid, escape_str(atype), escape_str(street), escape_str(city), escape_str(state), escape_str(zipc), escape_str(country)))
    batch_insert(f, "Addresses", ["CustomerID", "AddressType", "StreetAddress", "City", "State", "ZipCode", "Country"], addrs)

    print("Generating Suppliers...")
    sups = []
    for i in range(NUM_SUPPLIERS):
        name = fake.company()
        cname = fake.name()
        email = fake.company_email()
        phone = fake.numerify(text='###-###-####')
        city = fake.city()
        country = fake.country()
        sups.append((escape_str(name), escape_str(cname), escape_str(email), escape_str(phone), escape_str(city), escape_str(country)))
    batch_insert(f, "Suppliers", ["SupplierName", "ContactName", "ContactEmail", "Phone", "City", "Country"], sups)

    print("Generating Categories...")
    cats = []
    fake.unique.clear()
    for i in range(NUM_CATEGORIES):
        cname = fake.unique.word().capitalize() + " " + str(i)
        desc = fake.sentence()
        cats.append((escape_str(cname), escape_str(desc)))
    batch_insert(f, "Categories", ["CategoryName", "Description"], cats)

    print("Generating Products...")
    prods = []
    fake.unique.clear()
    for i in range(NUM_PRODUCTS):
        sku = f"SKU-{fake.unique.ean8()}"
        bar = fake.ean13()
        pname = fake.catch_phrase()
        brand = fake.company()
        cid = random.randint(1, NUM_CATEGORIES)
        sid = random.randint(1, NUM_SUPPLIERS)
        cost = round(random.uniform(5.0, 500.0), 2)
        sell = round(cost * random.uniform(1.1, 2.5), 2)
        disc = round(random.uniform(0, 30), 2)
        weight = round(random.uniform(0.1, 50.0), 2)
        war = random.choice([0, 6, 12, 24, 36])
        status = random.choices(['In Stock', 'Out of Stock', 'Discontinued'], weights=[80, 15, 5])[0]
        prods.append((escape_str(sku), escape_str(bar), escape_str(pname), escape_str(brand), cid, sid, cost, sell, disc, weight, war, escape_str(status)))
    batch_insert(f, "Products", ["SKU", "Barcode", "ProductName", "Brand", "CategoryID", "SupplierID", "CostPrice", "SellingPrice", "Discount", "Weight", "WarrantyMonths", "StockStatus"], prods)

    print("Generating Warehouses...")
    whs = []
    for i in range(NUM_WAREHOUSES):
        whs.append((escape_str(f"Warehouse {fake.city()}"), escape_str(fake.address().replace('\n', ', '))))
    batch_insert(f, "Warehouses", ["WarehouseName", "Location"], whs)

    print("Generating Inventory...")
    inv = []
    pairs = set()
    while len(inv) < NUM_INVENTORY:
        wid = random.randint(1, NUM_WAREHOUSES)
        pid = random.randint(1, NUM_PRODUCTS)
        if (wid, pid) not in pairs:
            pairs.add((wid, pid))
            qty = random.randint(0, 1000)
            inv.append((wid, pid, qty))
    batch_insert(f, "Inventory", ["WarehouseID", "ProductID", "Quantity"], inv)

    print("Generating Coupons...")
    coupons = []
    for i in range(NUM_COUPONS):
        code = f"PROMO{i}{fake.bothify('??##')}"
        disc = round(random.uniform(5.0, 50.0), 2)
        act = random.choice([1, 0])
        exp = fake.date_between(start_date='today', end_date='+1y')
        coupons.append((escape_str(code), disc, act, escape_str(exp)))
    batch_insert(f, "Coupons", ["CouponCode", "DiscountAmount", "IsActive", "ExpiryDate"], coupons)

    print("Generating CustomerCoupons...")
    cc = []
    cc_pairs = set()
    while len(cc) < NUM_CUSTOMER_COUPONS:
        cid = random.randint(1, NUM_CUSTOMERS)
        cpid = random.randint(1, NUM_COUPONS)
        if (cid, cpid) not in cc_pairs:
            cc_pairs.add((cid, cpid))
            dt = fake.date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
            used = random.choice([0, 1])
            cc.append((cid, cpid, escape_str(dt), used))
    batch_insert(f, "CustomerCoupons", ["CustomerID", "CouponID", "AssignedDate", "IsUsed"], cc)

    print("Generating Orders...")
    orders = []
    for i in range(1, NUM_ORDERS + 1):
        cid = random.randint(1, NUM_CUSTOMERS)
        dt = fake.date_time_between(start_date='-5y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
        tot = round(random.uniform(10.0, 2000.0), 2)
        status = random.choices(['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned'], weights=[5, 10, 20, 55, 5, 5])[0]
        aid = random.randint(1, NUM_ADDRESSES)
        cpid = random.choice(['NULL', random.randint(1, NUM_COUPONS)])
        orders.append((cid, escape_str(dt), tot, escape_str(status), aid, cpid))
    batch_insert(f, "Orders", ["CustomerID", "OrderDate", "TotalAmount", "OrderStatus", "ShippingAddressID", "CouponID"], orders)

    print("Generating OrderItems...")
    oitems = []
    for i in range(NUM_ORDER_ITEMS):
        oid = random.randint(1, NUM_ORDERS)
        pid = random.randint(1, NUM_PRODUCTS)
        qty = random.randint(1, 10)
        up = round(random.uniform(5.0, 500.0), 2)
        oitems.append((oid, pid, qty, up))
    batch_insert(f, "OrderItems", ["OrderID", "ProductID", "Quantity", "UnitPrice"], oitems)

    print("Generating Payments...")
    pays = []
    for i in range(NUM_PAYMENTS):
        oid = random.randint(1, NUM_ORDERS)
        dt = fake.date_time_between(start_date='-5y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
        amt = round(random.uniform(10.0, 2000.0), 2)
        meth = random.choice(['Cash', 'Card', 'UPI', 'Net Banking', 'Wallet'])
        status = random.choices(['Pending', 'Completed', 'Failed', 'Refunded'], weights=[5, 80, 10, 5])[0]
        pays.append((oid, escape_str(dt), amt, escape_str(meth), escape_str(status)))
    batch_insert(f, "Payments", ["OrderID", "PaymentDate", "Amount", "PaymentMethod", "PaymentStatus"], pays)

    print("Generating Shipments...")
    ships = []
    for i in range(NUM_SHIPMENTS):
        oid = random.randint(1, NUM_ORDERS)
        tn = fake.bothify('TRK-#########')
        car = random.choice(['FedEx', 'UPS', 'USPS', 'DHL'])
        sd = fake.date_time_between(start_date='-5y', end_date='now')
        ed = sd + timedelta(days=random.randint(2, 7))
        ad = ed + timedelta(days=random.randint(-1, 3)) if random.choice([True, False]) else 'NULL'
        sd_str = escape_str(sd.strftime('%Y-%m-%d %H:%M:%S'))
        ed_str = escape_str(ed.strftime('%Y-%m-%d %H:%M:%S'))
        ad_str = escape_str(ad.strftime('%Y-%m-%d %H:%M:%S')) if ad != 'NULL' else 'NULL'
        status = random.choice(['In Transit', 'Delivered', 'Delayed'])
        ships.append((oid, escape_str(tn), escape_str(car), sd_str, ed_str, ad_str, escape_str(status)))
    batch_insert(f, "Shipments", ["OrderID", "TrackingNumber", "Carrier", "ShipDate", "EstimatedDelivery", "ActualDelivery", "Status"], ships)

    print("Generating Reviews...")
    revs = []
    for i in range(NUM_REVIEWS):
        pid = random.randint(1, NUM_PRODUCTS)
        cid = random.randint(1, NUM_CUSTOMERS)
        rate = random.randint(1, 5)
        com = fake.sentence()
        dt = fake.date_time_between(start_date='-5y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
        revs.append((pid, cid, rate, escape_str(com), escape_str(dt)))
    batch_insert(f, "Reviews", ["ProductID", "CustomerID", "Rating", "Comment", "ReviewDate"], revs)

    print("Generating Returns...")
    rets = []
    for i in range(NUM_RETURNS):
        oid = random.randint(1, NUM_ORDERS)
        pid = random.randint(1, NUM_PRODUCTS)
        dt = fake.date_time_between(start_date='-5y', end_date='now').strftime('%Y-%m-%d %H:%M:%S')
        rea = random.choice(['Defective', 'Wrong Item', 'Changed Mind', 'Not as described'])
        ref = round(random.uniform(5.0, 500.0), 2)
        stat = random.choice(['Pending', 'Approved', 'Rejected'])
        rets.append((oid, pid, escape_str(dt), escape_str(rea), ref, escape_str(stat)))
    batch_insert(f, "Returns", ["OrderID", "ProductID", "ReturnDate", "Reason", "RefundAmount", "Status"], rets)

    print("Generating EmployeeAttendance...")
    att = []
    att_pairs = set()
    while len(att) < NUM_ATTENDANCE:
        eid = random.randint(1, NUM_EMPLOYEES)
        wd = fake.date_between(start_date='-1y', end_date='today')
        if (eid, wd) not in att_pairs:
            att_pairs.add((eid, wd))
            cin = '09:00:00'
            cout = '17:00:00'
            stat = random.choices(['Present', 'Absent', 'Half Day', 'Leave'], weights=[85, 5, 5, 5])[0]
            att.append((eid, escape_str(wd.strftime('%Y-%m-%d')), escape_str(cin), escape_str(cout), escape_str(stat)))
    batch_insert(f, "EmployeeAttendance", ["EmployeeID", "WorkDate", "CheckInTime", "CheckOutTime", "Status"], att)

    print("Generating Payroll...")
    payr = []
    for i in range(NUM_PAYROLL):
        eid = random.randint(1, NUM_EMPLOYEES)
        start_d = fake.date_between(start_date='-1y', end_date='today')
        end_d = start_d + timedelta(days=14)
        bs = round(random.uniform(1500.0, 5000.0), 2)
        bon = round(random.uniform(0.0, 500.0), 2)
        ded = round(random.uniform(50.0, 300.0), 2)
        pd = end_d + timedelta(days=2)
        payr.append((eid, escape_str(start_d.strftime('%Y-%m-%d')), escape_str(end_d.strftime('%Y-%m-%d')), bs, bon, ded, escape_str(pd.strftime('%Y-%m-%d %H:%M:%S'))))
    batch_insert(f, "Payroll", ["EmployeeID", "PayPeriodStart", "PayPeriodEnd", "BaseSalary", "Bonus", "Deductions", "PaymentDate"], payr)

    print("Generating AuditLogs...")
    alogs = []
    for i in range(NUM_AUDIT_LOGS):
        tn = random.choice(['Products', 'Orders', 'Employees', 'Customers'])
        op = random.choice(['INSERT', 'UPDATE', 'DELETE'])
        rid = random.randint(1, 1000)
        ov = escape_str(fake.word()) if op in ('UPDATE', 'DELETE') else 'NULL'
        nv = escape_str(fake.word()) if op in ('UPDATE', 'INSERT') else 'NULL'
        alogs.append((escape_str(tn), escape_str(op), rid, ov, nv))
    batch_insert(f, "AuditLogs", ["TableName", "Operation", "RecordID", "OldValue", "NewValue"], alogs)

def write_validation(f):
    f.write("-- =========================================\n")
    f.write("-- Validation and Analytical Queries\n")
    f.write("-- =========================================\n")
    f.write("SELECT 'Customers' AS TableName, COUNT(*) AS Row_Count FROM Customers;\n")
    f.write("SELECT 'Orders' AS TableName, COUNT(*) AS Row_Count FROM Orders;\n")
    f.write("SELECT 'OrderItems' AS TableName, COUNT(*) AS Row_Count FROM OrderItems;\n")
    f.write("SELECT 'Products' AS TableName, COUNT(*) AS Row_Count FROM Products;\n")
    f.write("SELECT 'Employees' AS TableName, COUNT(*) AS Row_Count FROM Employees;\n")
    f.write("GO\n\n")

    f.write("-- Top 5 Selling Products\n")
    f.write("SELECT TOP 5 * FROM vw_ProductSales ORDER BY TotalSold DESC;\nGO\n\n")
    
    f.write("-- Employee Hierarchy\n")
    f.write("WITH EmployeeCTE AS (\n")
    f.write("    SELECT EmployeeID, FirstName, LastName, ManagerID, 0 AS Level\n")
    f.write("    FROM Employees WHERE ManagerID IS NULL\n")
    f.write("    UNION ALL\n")
    f.write("    SELECT e.EmployeeID, e.FirstName, e.LastName, e.ManagerID, c.Level + 1\n")
    f.write("    FROM Employees e INNER JOIN EmployeeCTE c ON e.ManagerID = c.EmployeeID\n")
    f.write(")\nSELECT * FROM EmployeeCTE ORDER BY Level, ManagerID;\nGO\n\n")

if __name__ == "__main__":
    print(f"Generating {OUTPUT_FILE}...")
    with io.open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        write_ddl(f)
        write_indexes_and_advanced(f)
        generate_data(f)
        write_validation(f)
    print("Done!")
