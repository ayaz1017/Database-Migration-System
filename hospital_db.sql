DROP DATABASE IF EXISTS HospitalDB;
CREATE DATABASE HospitalDB;
USE HospitalDB;

-- 1. SCHEMA DEFINITION
CREATE TABLE Departments (
    DeptID INT AUTO_INCREMENT PRIMARY KEY,
    DeptName VARCHAR(100) NOT NULL,
    Location VARCHAR(100)
);

CREATE TABLE Doctors (
    DoctorID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    Specialization VARCHAR(100),
    DeptID INT,
    ContactNumber VARCHAR(20),
    FOREIGN KEY (DeptID) REFERENCES Departments(DeptID) ON DELETE SET NULL
);

CREATE TABLE Patients (
    PatientID INT AUTO_INCREMENT PRIMARY KEY,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50) NOT NULL,
    DOB DATE,
    Gender ENUM('Male', 'Female', 'Other'),
    ContactNumber VARCHAR(20),
    Address VARCHAR(255),
    RegistrationDate DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Appointments (
    AppointmentID INT AUTO_INCREMENT PRIMARY KEY,
    PatientID INT,
    DoctorID INT,
    AppointmentDateTime DATETIME NOT NULL,
    Status ENUM('Scheduled', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    Notes TEXT,
    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID) ON DELETE CASCADE,
    FOREIGN KEY (DoctorID) REFERENCES Doctors(DoctorID) ON DELETE CASCADE
);

CREATE TABLE MedicalRecords (
    RecordID INT AUTO_INCREMENT PRIMARY KEY,
    PatientID INT,
    DoctorID INT,
    RecordDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Diagnosis VARCHAR(255),
    Prescription TEXT,
    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID) ON DELETE CASCADE,
    FOREIGN KEY (DoctorID) REFERENCES Doctors(DoctorID) ON DELETE SET NULL
);

CREATE TABLE Billing (
    BillID INT AUTO_INCREMENT PRIMARY KEY,
    PatientID INT,
    AppointmentID INT,
    Amount DECIMAL(10, 2) NOT NULL,
    Status ENUM('Pending', 'Paid', 'Cancelled') DEFAULT 'Pending',
    PaymentDate DATETIME,
    FOREIGN KEY (PatientID) REFERENCES Patients(PatientID) ON DELETE CASCADE,
    FOREIGN KEY (AppointmentID) REFERENCES Appointments(AppointmentID) ON DELETE CASCADE
);

-- 2. VIEWS
CREATE VIEW vw_DoctorWorkload AS
SELECT 
    d.DoctorID, 
    CONCAT(d.FirstName, ' ', d.LastName) AS DoctorName, 
    dept.DeptName,
    COUNT(a.AppointmentID) AS TotalAppointments
FROM Doctors d
LEFT JOIN Appointments a ON d.DoctorID = a.DoctorID
LEFT JOIN Departments dept ON d.DeptID = dept.DeptID
GROUP BY d.DoctorID;

CREATE VIEW vw_PendingBills AS
SELECT 
    b.BillID, 
    CONCAT(p.FirstName, ' ', p.LastName) AS PatientName,
    b.Amount, 
    a.AppointmentDateTime,
    b.Status
FROM Billing b
JOIN Patients p ON b.PatientID = p.PatientID
JOIN Appointments a ON b.AppointmentID = a.AppointmentID
WHERE b.Status = 'Pending';

CREATE VIEW vw_PatientHistory AS
SELECT 
    p.PatientID, 
    CONCAT(p.FirstName, ' ', p.LastName) AS PatientName,
    a.AppointmentDateTime, 
    CONCAT(d.FirstName, ' ', d.LastName) AS DoctorName,
    m.Diagnosis, 
    m.Prescription
FROM Patients p
LEFT JOIN Appointments a ON p.PatientID = a.PatientID
LEFT JOIN Doctors d ON a.DoctorID = d.DoctorID
LEFT JOIN MedicalRecords m ON p.PatientID = m.PatientID AND d.DoctorID = m.DoctorID;

-- 3. TRIGGERS
DELIMITER //

-- Trigger to auto-generate a pending bill when an appointment is completed
CREATE TRIGGER trg_AfterAppointmentUpdate
AFTER UPDATE ON Appointments
FOR EACH ROW
BEGIN
    IF NEW.Status = 'Completed' AND OLD.Status != 'Completed' THEN
        INSERT INTO Billing (PatientID, AppointmentID, Amount, Status)
        VALUES (NEW.PatientID, NEW.AppointmentID, 150.00, 'Pending'); -- Base fee
    END IF;
END //

-- Trigger to prevent double booking for doctors
CREATE TRIGGER trg_BeforeAppointmentInsert
BEFORE INSERT ON Appointments
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT;
    SELECT COUNT(*) INTO conflict_count 
    FROM Appointments 
    WHERE DoctorID = NEW.DoctorID 
      AND AppointmentDateTime = NEW.AppointmentDateTime
      AND Status != 'Cancelled';
      
    IF conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Doctor is already booked at this time.';
    END IF;
END //

-- 4. PROCEDURES
-- Safely schedule appointment
CREATE PROCEDURE sp_ScheduleAppointment(
    IN p_PatientID INT,
    IN p_DoctorID INT,
    IN p_AppointmentDateTime DATETIME,
    IN p_Notes TEXT
)
BEGIN
    -- The trigger trg_BeforeAppointmentInsert will handle the validation
    INSERT INTO Appointments (PatientID, DoctorID, AppointmentDateTime, Status, Notes)
    VALUES (p_PatientID, p_DoctorID, p_AppointmentDateTime, 'Scheduled', p_Notes);
END //

-- Generate Dummy Data (50,000 rows approx)
CREATE PROCEDURE sp_GenerateDummyData()
BEGIN
    DECLARE i INT DEFAULT 0;
    DECLARE dept_count INT DEFAULT 10;
    DECLARE doc_count INT DEFAULT 100;
    DECLARE pat_count INT DEFAULT 10000;
    DECLARE appt_count INT DEFAULT 20000;
    DECLARE rec_count INT DEFAULT 10000;
    
    DECLARE rand_dept INT;
    DECLARE rand_doc INT;
    DECLARE rand_pat INT;
    
    -- Optimize insertion speed for the duration of this procedure
    SET autocommit = 0;
    SET unique_checks = 0;
    SET foreign_key_checks = 0;
    
    -- Insert Departments (10 rows)
    WHILE i < dept_count DO
        INSERT INTO Departments (DeptName, Location) 
        VALUES (CONCAT('Department_', i), CONCAT('Floor_', (i MOD 5) + 1));
        SET i = i + 1;
    END WHILE;
    COMMIT;
    
    -- Insert Doctors (100 rows)
    SET i = 0;
    WHILE i < doc_count DO
        SET rand_dept = FLOOR(1 + (RAND() * dept_count));
        INSERT INTO Doctors (FirstName, LastName, Specialization, DeptID, ContactNumber)
        VALUES (CONCAT('DocFirstName_', i), CONCAT('DocLastName_', i), 'General', rand_dept, CONCAT('555-01', LPAD(i, 2, '0')));
        SET i = i + 1;
    END WHILE;
    COMMIT;
    
    -- Insert Patients (10000 rows)
    SET i = 0;
    WHILE i < pat_count DO
        INSERT INTO Patients (FirstName, LastName, DOB, Gender, ContactNumber, Address)
        VALUES (
            CONCAT('PatFirst_', i), 
            CONCAT('PatLast_', i), 
            DATE_SUB(CURDATE(), INTERVAL FLOOR(5 + (RAND() * 80)) YEAR),
            IF(RAND() > 0.5, 'Male', 'Female'),
            CONCAT('555-99', LPAD(i MOD 100, 2, '0')),
            CONCAT(FLOOR(RAND() * 9999), ' Main St, City')
        );
        SET i = i + 1;
        IF i MOD 1000 = 0 THEN
            COMMIT;
        END IF;
    END WHILE;
    COMMIT;
    
    -- Insert Appointments (20000 rows)
    SET i = 0;
    WHILE i < appt_count DO
        SET rand_pat = FLOOR(1 + (RAND() * pat_count));
        SET rand_doc = FLOOR(1 + (RAND() * doc_count));
        
        -- To avoid the trigger blocking us, we will just ensure datetime is unique by using i
        INSERT INTO Appointments (PatientID, DoctorID, AppointmentDateTime, Status, Notes)
        VALUES (
            rand_pat, 
            rand_doc, 
            DATE_ADD(CURDATE(), INTERVAL (i - 10000) HOUR), -- spread over past and future
            'Scheduled',
            'Routine checkup'
        );
        SET i = i + 1;
        IF i MOD 1000 = 0 THEN
            COMMIT;
        END IF;
    END WHILE;
    COMMIT;

    -- Update some appointments to Completed to trigger billing (10000 rows -> creates 10000 Bills)
    -- Temporarily re-enable checks so the trigger works correctly
    SET foreign_key_checks = 1;
    SET unique_checks = 1;
    
    UPDATE Appointments SET Status = 'Completed' WHERE AppointmentID <= 10000;
    COMMIT;
    
    -- Re-disable for MedicalRecords
    SET unique_checks = 0;
    SET foreign_key_checks = 0;
    
    -- Insert Medical Records (10000 rows)
    SET i = 0;
    WHILE i < rec_count DO
        SET rand_pat = FLOOR(1 + (RAND() * pat_count));
        SET rand_doc = FLOOR(1 + (RAND() * doc_count));
        INSERT INTO MedicalRecords (PatientID, DoctorID, Diagnosis, Prescription)
        VALUES (
            rand_pat,
            rand_doc,
            CONCAT('Diagnosis for symptom ', FLOOR(RAND() * 100)),
            CONCAT('Medication A ', FLOOR(RAND() * 500), 'mg')
        );
        SET i = i + 1;
        IF i MOD 1000 = 0 THEN
            COMMIT;
        END IF;
    END WHILE;
    COMMIT;
    
    -- Restore defaults
    SET autocommit = 1;
    SET unique_checks = 1;
    SET foreign_key_checks = 1;
    
END //
DELIMITER ;
