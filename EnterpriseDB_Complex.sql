-- =========================================
-- EnterpriseDB_Complex Generation Script
-- =========================================

USE master;
GO
IF DB_ID('EnterpriseDB_Complex') IS NOT NULL
BEGIN
    ALTER DATABASE EnterpriseDB_Complex SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE EnterpriseDB_Complex;
END
GO
CREATE DATABASE EnterpriseDB_Complex;
GO
USE EnterpriseDB_Complex;
GO

-- 1. Departments
CREATE TABLE Departments (
    DepartmentID INT IDENTITY(1,1) PRIMARY KEY,
    DepartmentName NVARCHAR(100) NOT NULL UNIQUE,
    Budget DECIMAL(18,2) DEFAULT 0.00
);
GO

-- 2. Employees
CREATE TABLE Employees (
    EmployeeID INT IDENTITY(1,1) PRIMARY KEY,
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Email NVARCHAR(150) NOT NULL UNIQUE,
    DepartmentID INT NOT NULL FOREIGN KEY REFERENCES Departments(DepartmentID),
    ManagerID INT NULL FOREIGN KEY REFERENCES Employees(EmployeeID),
    HireDate DATE NOT NULL DEFAULT GETDATE(),
    Salary DECIMAL(18,2) NOT NULL CHECK (Salary > 0),
    Status NVARCHAR(20) DEFAULT 'Active' CHECK (Status IN ('Active', 'On Leave', 'Terminated'))
);
GO

-- 3. Customers
CREATE TABLE Customers (
    CustomerID INT IDENTITY(1,1) PRIMARY KEY,
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Email NVARCHAR(150) NOT NULL UNIQUE,
    Phone NVARCHAR(30),
    DOB DATE,
    Gender CHAR(1) CHECK (Gender IN ('M', 'F', 'O', 'U')),
    LoyaltyPoints INT DEFAULT 0,
    CustomerType NVARCHAR(20) DEFAULT 'Standard',
    RegistrationDate DATETIME DEFAULT GETDATE(),
    Status NVARCHAR(20) DEFAULT 'Active'
);
GO

-- 4. Addresses
CREATE TABLE Addresses (
    AddressID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID INT NOT NULL FOREIGN KEY REFERENCES Customers(CustomerID) ON DELETE CASCADE,
    AddressType NVARCHAR(20) CHECK (AddressType IN ('Billing', 'Shipping')),
    StreetAddress NVARCHAR(255) NOT NULL,
    City NVARCHAR(100) NOT NULL,
    State NVARCHAR(100),
    ZipCode NVARCHAR(20),
    Country NVARCHAR(100) NOT NULL
);
GO

-- 5. Suppliers
CREATE TABLE Suppliers (
    SupplierID INT IDENTITY(1,1) PRIMARY KEY,
    SupplierName NVARCHAR(150) NOT NULL,
    ContactName NVARCHAR(100),
    ContactEmail NVARCHAR(150),
    Phone NVARCHAR(30),
    City NVARCHAR(100),
    Country NVARCHAR(100)
);
GO

-- 6. Categories
CREATE TABLE Categories (
    CategoryID INT IDENTITY(1,1) PRIMARY KEY,
    CategoryName NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(MAX)
);
GO

-- 7. Products
CREATE TABLE Products (
    ProductID INT IDENTITY(1,1) PRIMARY KEY,
    SKU NVARCHAR(50) NOT NULL UNIQUE,
    Barcode NVARCHAR(100),
    ProductName NVARCHAR(200) NOT NULL,
    Brand NVARCHAR(100),
    CategoryID INT NOT NULL FOREIGN KEY REFERENCES Categories(CategoryID),
    SupplierID INT NOT NULL FOREIGN KEY REFERENCES Suppliers(SupplierID),
    CostPrice DECIMAL(18,2) NOT NULL CHECK (CostPrice >= 0),
    SellingPrice DECIMAL(18,2) NOT NULL CHECK (SellingPrice >= 0),
    Discount DECIMAL(5,2) DEFAULT 0.00 CHECK (Discount >= 0 AND Discount <= 100),
    Weight DECIMAL(10,2),
    WarrantyMonths INT DEFAULT 12,
    StockStatus NVARCHAR(20) DEFAULT 'In Stock',
    ProfitMargin AS ((SellingPrice - CostPrice) / NULLIF(CostPrice, 0)) PERSISTED
);
GO

-- 8. Warehouses
CREATE TABLE Warehouses (
    WarehouseID INT IDENTITY(1,1) PRIMARY KEY,
    WarehouseName NVARCHAR(100) NOT NULL,
    Location NVARCHAR(200)
);
GO

-- 9. Inventory
CREATE TABLE Inventory (
    WarehouseID INT NOT NULL FOREIGN KEY REFERENCES Warehouses(WarehouseID),
    ProductID INT NOT NULL FOREIGN KEY REFERENCES Products(ProductID),
    Quantity INT NOT NULL DEFAULT 0 CHECK (Quantity >= 0),
    LastUpdated DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (WarehouseID, ProductID)
);
GO

-- 10. Coupons
CREATE TABLE Coupons (
    CouponID INT IDENTITY(1,1) PRIMARY KEY,
    CouponCode NVARCHAR(50) NOT NULL UNIQUE,
    DiscountAmount DECIMAL(18,2) NOT NULL,
    IsActive BIT DEFAULT 1,
    ExpiryDate DATE
);
GO

-- 11. CustomerCoupons
CREATE TABLE CustomerCoupons (
    CustomerID INT NOT NULL FOREIGN KEY REFERENCES Customers(CustomerID),
    CouponID INT NOT NULL FOREIGN KEY REFERENCES Coupons(CouponID),
    AssignedDate DATETIME DEFAULT GETDATE(),
    IsUsed BIT DEFAULT 0,
    PRIMARY KEY (CustomerID, CouponID)
);
GO

-- 12. Orders
CREATE TABLE Orders (
    OrderID INT IDENTITY(1,1) PRIMARY KEY,
    CustomerID INT NOT NULL FOREIGN KEY REFERENCES Customers(CustomerID),
    OrderDate DATETIME DEFAULT GETDATE(),
    TotalAmount DECIMAL(18,2) DEFAULT 0.00,
    OrderStatus NVARCHAR(50) DEFAULT 'Pending' CHECK (OrderStatus IN ('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned')),
    ShippingAddressID INT FOREIGN KEY REFERENCES Addresses(AddressID),
    CouponID INT NULL FOREIGN KEY REFERENCES Coupons(CouponID)
);
GO

-- 13. OrderItems
CREATE TABLE OrderItems (
    OrderItemID INT IDENTITY(1,1) PRIMARY KEY,
    OrderID INT NOT NULL FOREIGN KEY REFERENCES Orders(OrderID) ON DELETE CASCADE,
    ProductID INT NOT NULL FOREIGN KEY REFERENCES Products(ProductID),
    Quantity INT NOT NULL CHECK (Quantity > 0),
    UnitPrice DECIMAL(18,2) NOT NULL,
    LineTotal AS (Quantity * UnitPrice) PERSISTED
);
GO

-- 14. Payments
CREATE TABLE Payments (
    PaymentID INT IDENTITY(1,1) PRIMARY KEY,
    OrderID INT NOT NULL FOREIGN KEY REFERENCES Orders(OrderID) ON DELETE CASCADE,
    PaymentDate DATETIME DEFAULT GETDATE(),
    Amount DECIMAL(18,2) NOT NULL CHECK (Amount >= 0),
    PaymentMethod NVARCHAR(50) CHECK (PaymentMethod IN ('Cash', 'Card', 'UPI', 'Net Banking', 'Wallet')),
    PaymentStatus NVARCHAR(50) DEFAULT 'Completed' CHECK (PaymentStatus IN ('Pending', 'Completed', 'Failed', 'Refunded'))
);
GO

-- 15. Shipments
CREATE TABLE Shipments (
    ShipmentID INT IDENTITY(1,1) PRIMARY KEY,
    OrderID INT NOT NULL FOREIGN KEY REFERENCES Orders(OrderID),
    TrackingNumber NVARCHAR(100),
    Carrier NVARCHAR(100),
    ShipDate DATETIME,
    EstimatedDelivery DATETIME,
    ActualDelivery DATETIME,
    Status NVARCHAR(50) DEFAULT 'In Transit'
);
GO

-- 16. Reviews
CREATE TABLE Reviews (
    ReviewID INT IDENTITY(1,1) PRIMARY KEY,
    ProductID INT NOT NULL FOREIGN KEY REFERENCES Products(ProductID) ON DELETE CASCADE,
    CustomerID INT NOT NULL FOREIGN KEY REFERENCES Customers(CustomerID) ON DELETE CASCADE,
    Rating INT CHECK (Rating BETWEEN 1 AND 5),
    Comment NVARCHAR(MAX),
    ReviewDate DATETIME DEFAULT GETDATE()
);
GO

-- 17. Returns
CREATE TABLE Returns (
    ReturnID INT IDENTITY(1,1) PRIMARY KEY,
    OrderID INT NOT NULL FOREIGN KEY REFERENCES Orders(OrderID),
    ProductID INT NOT NULL FOREIGN KEY REFERENCES Products(ProductID),
    ReturnDate DATETIME DEFAULT GETDATE(),
    Reason NVARCHAR(255),
    RefundAmount DECIMAL(18,2),
    Status NVARCHAR(50) DEFAULT 'Pending'
);
GO

-- 18. EmployeeAttendance
CREATE TABLE EmployeeAttendance (
    AttendanceID INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID INT NOT NULL FOREIGN KEY REFERENCES Employees(EmployeeID) ON DELETE CASCADE,
    WorkDate DATE NOT NULL,
    CheckInTime TIME,
    CheckOutTime TIME,
    Status NVARCHAR(20) DEFAULT 'Present' CHECK (Status IN ('Present', 'Absent', 'Half Day', 'Leave')),
    UNIQUE (EmployeeID, WorkDate)
);
GO

-- 19. Payroll
CREATE TABLE Payroll (
    PayrollID INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID INT NOT NULL FOREIGN KEY REFERENCES Employees(EmployeeID) ON DELETE CASCADE,
    PayPeriodStart DATE NOT NULL,
    PayPeriodEnd DATE NOT NULL,
    BaseSalary DECIMAL(18,2) NOT NULL,
    Bonus DECIMAL(18,2) DEFAULT 0.00,
    Deductions DECIMAL(18,2) DEFAULT 0.00,
    NetPay AS (BaseSalary + Bonus - Deductions) PERSISTED,
    PaymentDate DATETIME
);
GO

-- 20. AuditLogs
CREATE TABLE AuditLogs (
    LogID INT IDENTITY(1,1) PRIMARY KEY,
    TableName NVARCHAR(100) NOT NULL,
    Operation NVARCHAR(50) NOT NULL,
    RecordID INT NOT NULL,
    OldValue NVARCHAR(MAX),
    NewValue NVARCHAR(MAX),
    ChangedBy NVARCHAR(100) DEFAULT SYSTEM_USER,
    ChangedDate DATETIME DEFAULT GETDATE()
);
GO

-- =========================================
-- Indexes
-- =========================================
CREATE NONCLUSTERED INDEX IX_Customers_Email ON Customers(Email);
GO
CREATE NONCLUSTERED INDEX IX_Products_Category ON Products(CategoryID);
GO
CREATE NONCLUSTERED INDEX IX_Orders_Customer ON Orders(CustomerID);
GO
CREATE NONCLUSTERED INDEX IX_OrderItems_Order ON OrderItems(OrderID);
GO
CREATE UNIQUE NONCLUSTERED INDEX UQ_Inventory_Warehouse_Product ON Inventory(WarehouseID, ProductID);
GO
CREATE NONCLUSTERED INDEX IX_Payments_Order ON Payments(OrderID);
GO
CREATE FILTERED INDEX FIX_Orders_Pending ON Orders(OrderStatus) WHERE OrderStatus = 'Pending';
GO

-- =========================================
-- Views
-- =========================================
CREATE VIEW vw_OrderSummary AS
SELECT o.OrderID, o.OrderDate, c.FirstName + ' ' + c.LastName AS CustomerName, o.TotalAmount, o.OrderStatus
FROM Orders o JOIN Customers c ON o.CustomerID = c.CustomerID;
GO

CREATE VIEW vw_ProductSales AS
SELECT p.ProductID, p.ProductName, SUM(oi.Quantity) AS TotalSold, SUM(oi.LineTotal) AS Revenue
FROM Products p JOIN OrderItems oi ON p.ProductID = oi.ProductID
GROUP BY p.ProductID, p.ProductName;
GO

CREATE VIEW vw_EmployeePayroll AS
SELECT e.EmployeeID, e.FirstName + ' ' + e.LastName AS EmployeeName, d.DepartmentName, p.PayPeriodStart, p.NetPay
FROM Employees e JOIN Departments d ON e.DepartmentID = d.DepartmentID
JOIN Payroll p ON e.EmployeeID = p.EmployeeID;
GO

CREATE VIEW vw_LowInventory AS
SELECT w.WarehouseName, p.ProductName, i.Quantity
FROM Inventory i JOIN Warehouses w ON i.WarehouseID = w.WarehouseID
JOIN Products p ON i.ProductID = p.ProductID
WHERE i.Quantity < 10;
GO

-- =========================================
-- Functions
-- =========================================
CREATE FUNCTION fn_TotalOrderValue(@OrderID INT)
RETURNS DECIMAL(18,2)
AS
BEGIN
    DECLARE @Total DECIMAL(18,2);
    SELECT @Total = SUM(LineTotal) FROM OrderItems WHERE OrderID = @OrderID;
    RETURN ISNULL(@Total, 0);
END;
GO

CREATE FUNCTION fn_CustomerLifetimeValue(@CustomerID INT)
RETURNS DECIMAL(18,2)
AS
BEGIN
    DECLARE @LTV DECIMAL(18,2);
    SELECT @LTV = SUM(TotalAmount) FROM Orders WHERE CustomerID = @CustomerID AND OrderStatus = 'Delivered';
    RETURN ISNULL(@LTV, 0);
END;
GO

-- =========================================
-- Triggers
-- =========================================
CREATE TRIGGER trg_AuditProductPrice
ON Products
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF UPDATE(SellingPrice)
    BEGIN
        INSERT INTO AuditLogs (TableName, Operation, RecordID, OldValue, NewValue)
        SELECT 'Products', 'UPDATE', i.ProductID, CAST(d.SellingPrice AS NVARCHAR), CAST(i.SellingPrice AS NVARCHAR)
        FROM inserted i JOIN deleted d ON i.ProductID = d.ProductID
        WHERE i.SellingPrice <> d.SellingPrice;
    END
END;
GO

CREATE TRIGGER trg_PreventNegativeStock
ON Inventory
INSTEAD OF UPDATE
AS
BEGIN
    IF EXISTS (SELECT 1 FROM inserted WHERE Quantity < 0)
    BEGIN
        RAISERROR('Cannot update inventory to a negative quantity.', 16, 1);
        ROLLBACK TRANSACTION;
    END
    ELSE
    BEGIN
        UPDATE Inventory SET Quantity = i.Quantity, LastUpdated = GETDATE()
        FROM Inventory inv JOIN inserted i ON inv.ProductID = i.ProductID AND inv.WarehouseID = i.WarehouseID;
    END
END;
GO

-- =========================================
-- Stored Procedures
-- =========================================
CREATE PROCEDURE sp_CreateOrder
    @CustomerID INT, @ShippingAddressID INT, @CouponID INT = NULL, @NewOrderID INT OUTPUT
AS
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;
        INSERT INTO Orders (CustomerID, OrderDate, OrderStatus, ShippingAddressID, CouponID)
        VALUES (@CustomerID, GETDATE(), 'Pending', @ShippingAddressID, @CouponID);
        SET @NewOrderID = SCOPE_IDENTITY();
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
        RAISERROR(@ErrMsg, 16, 1);
    END CATCH
END;
GO

-- =========================================
-- Data Generation
-- =========================================
