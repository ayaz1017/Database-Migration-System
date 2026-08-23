-- ============================================================================
-- Complex MSSQL Database Creation Script for Migration Testing
-- Database: ComplexDB
-- Includes: Tables, FKs, Views, Stored Procedures, Triggers, and Sample Data
-- ============================================================================

USE master;
GO

IF EXISTS (SELECT name FROM sys.databases WHERE name = N'ComplexDB')
BEGIN
    ALTER DATABASE [ComplexDB] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE [ComplexDB];
END;
GO

CREATE DATABASE [ComplexDB];
GO

USE [ComplexDB];
GO

-- ============================================================================
-- 1. TABLES & CONSTRAINTS
-- ============================================================================

CREATE TABLE Departments (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Budget DECIMAL(18,2) NOT NULL
);
GO

CREATE TABLE Employees (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    DeptId INT NOT NULL,
    FirstName VARCHAR(100) NOT NULL,
    LastName VARCHAR(100) NOT NULL,
    Salary DECIMAL(18,2) NOT NULL,
    HireDate DATETIME NOT NULL DEFAULT GETDATE(),
    IsActive BIT NOT NULL DEFAULT 1,
    CONSTRAINT FK_Employees_Departments FOREIGN KEY (DeptId) REFERENCES Departments(Id)
);
GO

CREATE TABLE Customers (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name VARCHAR(200) NOT NULL,
    Email VARCHAR(200) NOT NULL,
    Region VARCHAR(50) NOT NULL
);
GO

CREATE TABLE Orders (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    CustomerId INT NOT NULL,
    OrderDate DATETIME NOT NULL DEFAULT GETDATE(),
    TotalAmount DECIMAL(18,2) NOT NULL,
    CONSTRAINT FK_Orders_Customers FOREIGN KEY (CustomerId) REFERENCES Customers(Id)
);
GO

CREATE TABLE AuditLogs (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    TableName VARCHAR(100) NOT NULL,
    Action VARCHAR(100) NOT NULL,
    Timestamp DATETIME DEFAULT GETDATE()
);
GO

-- ============================================================================
-- 2. TRIGGERS
-- ============================================================================

CREATE TRIGGER trg_Employees_Insert
ON Employees
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO AuditLogs (TableName, Action) VALUES ('Employees', 'INSERT');
END;
GO

CREATE TRIGGER trg_Orders_Insert
ON Orders
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO AuditLogs (TableName, Action) VALUES ('Orders', 'INSERT');
END;
GO

-- ============================================================================
-- 3. VIEWS
-- ============================================================================

CREATE VIEW vw_ActiveEmployees AS
SELECT 
    e.Id, 
    e.FirstName, 
    e.LastName, 
    d.Name AS DepartmentName, 
    e.Salary
FROM Employees e
JOIN Departments d ON e.DeptId = d.Id
WHERE e.IsActive = 1;
GO

CREATE VIEW vw_DepartmentSummary AS
SELECT 
    d.Name AS DepartmentName, 
    COUNT(e.Id) AS EmployeeCount, 
    ISNULL(SUM(e.Salary), 0) AS TotalSalary
FROM Departments d
LEFT JOIN Employees e ON d.Id = e.DeptId
GROUP BY d.Name;
GO

-- ============================================================================
-- 4. STORED PROCEDURES
-- ============================================================================

CREATE PROCEDURE sp_GiveRaise
    @DeptId INT,
    @Percentage DECIMAL(5,2)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Employees
    SET Salary = Salary + (Salary * @Percentage / 100)
    WHERE DeptId = @DeptId;
END;
GO

CREATE PROCEDURE sp_GetCustomerOrders
    @CustomerId INT
AS
BEGIN
    SET NOCOUNT ON;
    SELECT Id, OrderDate, TotalAmount
    FROM Orders
    WHERE CustomerId = @CustomerId;
END;
GO

-- ============================================================================
-- 5. SAMPLE DATA INGESTION
-- ============================================================================

INSERT INTO Departments (Name, Budget) VALUES 
('Engineering', 5000000.00),
('Marketing', 1500000.00),
('Sales', 3000000.00),
('Human Resources', 800000.00),
('Finance', 2000000.00);
GO

INSERT INTO Employees (DeptId, FirstName, LastName, Salary, HireDate, IsActive) VALUES 
(1, 'Alice', 'Smith', 120000.00, '2021-03-15', 1),
(1, 'Bob', 'Johnson', 110000.00, '2022-01-10', 1),
(2, 'Carol', 'Williams', 85000.00, '2020-07-22', 1),
(3, 'David', 'Brown', 95000.00, '2019-11-05', 1),
(4, 'Eve', 'Davis', 75000.00, '2023-02-01', 0);
GO

INSERT INTO Customers (Name, Email, Region) VALUES 
('Acme Corp', 'contact@acme.com', 'North'),
('Globex Inc', 'info@globex.com', 'East'),
('Stark Industries', 'sales@stark.com', 'West'),
('Wayne Enterprises', 'support@wayne.com', 'South');
GO

INSERT INTO Orders (CustomerId, OrderDate, TotalAmount) VALUES 
(1, '2024-01-15', 4999.99),
(2, '2024-02-20', 1250.00),
(3, '2024-03-10', 8900.50),
(1, '2024-04-05', 350.00);
GO
