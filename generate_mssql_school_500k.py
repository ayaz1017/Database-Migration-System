import pyodbc
from faker import Faker
import random
import sys
import time
from datetime import datetime, date, timedelta

# Default Connection Parameters (overridable via command line or flags)
HOST = "localhost"
PORT = 1433
USERNAME = "sa"
PASSWORD = "Ayaz@123"
DB_NAME = "SchoolDB_Complex"

if len(sys.argv) > 1:
    PASSWORD = sys.argv[1]

print(f"====================================================================")
print(f"  MSSQL Complex 500K School Database Ingestion Generator")
print(f"====================================================================")
print(f"Target DB   : {DB_NAME}")
print(f"Host        : {HOST}:{PORT}")
print(f"User        : {USERNAME}")
print(f"====================================================================\n")

servers_to_try = [
    f"{HOST},{PORT}",
    HOST,
    ".\\SQLEXPRESS",
    "localhost\\SQLEXPRESS",
    "127.0.0.1",
    "(localdb)\\MSSQLLocalDB"
]

drivers = pyodbc.drivers()
driver = "ODBC Driver 17 for SQL Server"
if "ODBC Driver 18 for SQL Server" in drivers:
    driver = "ODBC Driver 18 for SQL Server"
elif "ODBC Driver 17 for SQL Server" in drivers:
    driver = "ODBC Driver 17 for SQL Server"
elif "SQL Server" in drivers:
    driver = "SQL Server"

active_server = None
active_trusted = False

print(f"Connecting to MSSQL master database using driver '{driver}'...")

for srv in servers_to_try:
    # Try SQL Auth
    try:
        conn_str = f"DRIVER={{{driver}}};SERVER={srv};UID={USERNAME};PWD={PASSWORD};DATABASE=master;TrustServerCertificate=yes;"
        test_conn = pyodbc.connect(conn_str, autocommit=True, timeout=3)
        test_conn.close()
        active_server = srv
        active_trusted = False
        print(f"Connected successfully to server '{srv}' using SQL Auth!")
        break
    except Exception:
        pass
    
    # Try Windows Auth
    try:
        conn_str = f"DRIVER={{{driver}}};SERVER={srv};DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes;"
        test_conn = pyodbc.connect(conn_str, autocommit=True, timeout=3)
        test_conn.close()
        active_server = srv
        active_trusted = True
        print(f"Connected successfully to server '{srv}' using Windows Auth!")
        break
    except Exception:
        pass

if not active_server:
    print(f"\n[ERROR] Could not connect to any MSSQL Server instance.")
    print("Please verify:")
    print(" 1. SQL Server service (SQL Server / SQLEXPRESS) is started.")
    print("    You can start it in Windows Services (services.msc) or run in PowerShell as Admin: Start-Service MSSQL$SQLEXPRESS")
    print(" 2. SQL Server is configured to allow connections.\n")
    sys.exit(1)

def get_conn_str(db="master"):
    if active_trusted:
        return f"DRIVER={{{driver}}};SERVER={active_server};DATABASE={db};Trusted_Connection=yes;TrustServerCertificate=yes;"
    return f"DRIVER={{{driver}}};SERVER={active_server};UID={USERNAME};PWD={PASSWORD};DATABASE={db};TrustServerCertificate=yes;"

try:
    conn = pyodbc.connect(get_conn_str("master"), autocommit=True, timeout=10)
    cursor = conn.cursor()

    print(f"Recreating database [{DB_NAME}]...")
    cursor.execute(f"IF EXISTS (SELECT name FROM sys.databases WHERE name = N'{DB_NAME}') ALTER DATABASE [{DB_NAME}] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
    cursor.execute(f"IF EXISTS (SELECT name FROM sys.databases WHERE name = N'{DB_NAME}') DROP DATABASE [{DB_NAME}]")
    cursor.execute(f"CREATE DATABASE [{DB_NAME}]")
    cursor.close()
    conn.close()
    print(f"Database [{DB_NAME}] created successfully.\n")

except pyodbc.Error as e:
    print(f"\n[ERROR] Failed during database creation: {e}")
    sys.exit(1)

print(f"Connecting to [{DB_NAME}] to execute DDL schema...")
conn = pyodbc.connect(get_conn_str(DB_NAME))
cursor = conn.cursor()

# -----------------------------------------------------------------------------
# 1. DDL: Complex School Tables
# -----------------------------------------------------------------------------
schema_ddl = """
-- 1. Schools
CREATE TABLE Schools (
    SchoolId INT IDENTITY(1,1) PRIMARY KEY,
    SchoolName NVARCHAR(200) NOT NULL,
    CampusCode UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    EstablishedDate DATE NOT NULL,
    AnnualBudget DECIMAL(18,4) NOT NULL,
    IsActive BIT NOT NULL DEFAULT 1
);

-- 2. Departments
CREATE TABLE Departments (
    DepartmentId INT IDENTITY(1,1) PRIMARY KEY,
    SchoolId INT NOT NULL,
    DeptCode VARCHAR(20) NOT NULL,
    DeptName NVARCHAR(150) NOT NULL,
    HeadCount INT NOT NULL DEFAULT 0,
    ActiveStatus BIT NOT NULL DEFAULT 1,
    CONSTRAINT FK_Departments_Schools FOREIGN KEY (SchoolId) REFERENCES Schools(SchoolId)
);

-- 3. Teachers
CREATE TABLE Teachers (
    TeacherId INT IDENTITY(1,1) PRIMARY KEY,
    DepartmentId INT NOT NULL,
    FirstName NVARCHAR(100) NOT NULL,
    LastName NVARCHAR(100) NOT NULL,
    Email VARCHAR(200) NOT NULL,
    HireDate DATE NOT NULL,
    HourlyRate DECIMAL(10,2) NOT NULL,
    QualificationsXml NVARCHAR(MAX) NULL,
    CONSTRAINT FK_Teachers_Departments FOREIGN KEY (DepartmentId) REFERENCES Departments(DepartmentId)
);

-- 4. Courses
CREATE TABLE Courses (
    CourseId INT IDENTITY(1,1) PRIMARY KEY,
    DepartmentId INT NOT NULL,
    CourseCode VARCHAR(20) NOT NULL,
    CourseTitle NVARCHAR(200) NOT NULL,
    Credits TINYINT NOT NULL,
    SyllabusDetails NVARCHAR(MAX) NULL,
    IsElective BIT NOT NULL DEFAULT 0,
    CONSTRAINT FK_Courses_Departments FOREIGN KEY (DepartmentId) REFERENCES Departments(DepartmentId)
);

-- 5. Students
CREATE TABLE Students (
    StudentId BIGINT IDENTITY(1,1) PRIMARY KEY,
    SchoolId INT NOT NULL,
    StudentGuid UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    FirstName NVARCHAR(100) NOT NULL,
    LastName NVARCHAR(100) NOT NULL,
    DateOfBirth DATE NOT NULL,
    Gender CHAR(1) NOT NULL,
    GPA FLOAT NOT NULL DEFAULT 0.0,
    EnrollmentDate DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    AddressJson NVARCHAR(MAX) NULL,
    ProfileBlob VARBINARY(100) NULL,
    CONSTRAINT FK_Students_Schools FOREIGN KEY (SchoolId) REFERENCES Schools(SchoolId)
);

-- 6. Enrollments
CREATE TABLE Enrollments (
    EnrollmentId BIGINT IDENTITY(1,1) PRIMARY KEY,
    StudentId BIGINT NOT NULL,
    CourseId INT NOT NULL,
    Semester VARCHAR(20) NOT NULL,
    AcademicYear SMALLINT NOT NULL,
    FinalGrade DECIMAL(5,2) NULL,
    GradeLetter CHAR(2) NULL,
    EnrolledAt DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT FK_Enrollments_Students FOREIGN KEY (StudentId) REFERENCES Students(StudentId),
    CONSTRAINT FK_Enrollments_Courses FOREIGN KEY (CourseId) REFERENCES Courses(CourseId)
);

-- 7. Attendance
CREATE TABLE Attendance (
    AttendanceId BIGINT IDENTITY(1,1) PRIMARY KEY,
    StudentId BIGINT NOT NULL,
    CourseId INT NOT NULL,
    ClassDate DATE NOT NULL,
    Status VARCHAR(20) NOT NULL,
    MarkedAt TIME NOT NULL,
    CONSTRAINT FK_Attendance_Students FOREIGN KEY (StudentId) REFERENCES Students(StudentId),
    CONSTRAINT FK_Attendance_Courses FOREIGN KEY (CourseId) REFERENCES Courses(CourseId)
);

-- 8. Exams
CREATE TABLE Exams (
    ExamId BIGINT IDENTITY(1,1) PRIMARY KEY,
    CourseId INT NOT NULL,
    ExamTitle NVARCHAR(200) NOT NULL,
    ExamDate DATE NOT NULL,
    MaxMarks DECIMAL(6,2) NOT NULL,
    Weightage FLOAT NOT NULL,
    CONSTRAINT FK_Exams_Courses FOREIGN KEY (CourseId) REFERENCES Courses(CourseId)
);

-- 9. ExamResults
CREATE TABLE ExamResults (
    ResultId BIGINT IDENTITY(1,1) PRIMARY KEY,
    ExamId BIGINT NOT NULL,
    StudentId BIGINT NOT NULL,
    MarksObtained DECIMAL(6,2) NOT NULL,
    IsPassed BIT NOT NULL,
    Remarks NVARCHAR(500) NULL,
    CONSTRAINT FK_ExamResults_Exams FOREIGN KEY (ExamId) REFERENCES Exams(ExamId),
    CONSTRAINT FK_ExamResults_Students FOREIGN KEY (StudentId) REFERENCES Students(StudentId)
);

-- 10. Audit Logs
CREATE TABLE SchoolAuditLogs (
    LogId BIGINT IDENTITY(1,1) PRIMARY KEY,
    EntityName VARCHAR(100) NOT NULL,
    ActionType VARCHAR(50) NOT NULL,
    LogMessage NVARCHAR(MAX) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
"""

cursor.execute(schema_ddl)
conn.commit()
print("Tables and schema constraints created.")

# -----------------------------------------------------------------------------
# 2. DDL: Views, Triggers, Procedures
# -----------------------------------------------------------------------------
prog_objects = [
    # Trigger 1: Audit Log on Student Insert
    """
    CREATE TRIGGER trg_Students_AuditInsert
    ON Students
    AFTER INSERT
    AS
    BEGIN
        SET NOCOUNT ON;
        INSERT INTO SchoolAuditLogs (EntityName, ActionType, LogMessage)
        SELECT 'Students', 'INSERT', CONCAT('Inserted student: ', FirstName, ' ', LastName)
        FROM inserted;
    END;
    """,
    
    # Trigger 2: Audit Log on Exam Result Update
    """
    CREATE TRIGGER trg_ExamResults_AuditUpdate
    ON ExamResults
    AFTER UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        INSERT INTO SchoolAuditLogs (EntityName, ActionType, LogMessage)
        SELECT 'ExamResults', 'UPDATE', CONCAT('Result ID ', i.ResultId, ' updated marks to ', i.MarksObtained)
        FROM inserted i;
    END;
    """,
    
    # Trigger 3: Audit Log on Enrollment Insert
    """
    CREATE TRIGGER trg_Enrollments_AuditInsert
    ON Enrollments
    AFTER INSERT
    AS
    BEGIN
        SET NOCOUNT ON;
        INSERT INTO SchoolAuditLogs (EntityName, ActionType, LogMessage)
        SELECT 'Enrollments', 'INSERT', CONCAT('Student ', i.StudentId, ' enrolled in Course ', i.CourseId)
        FROM inserted i;
    END;
    """,

    # View 1: Student Performance
    """
    CREATE VIEW vw_StudentAcademicPerformance AS
    SELECT 
        s.StudentId,
        s.FirstName + ' ' + s.LastName AS StudentName,
        sch.SchoolName,
        COUNT(e.EnrollmentId) AS TotalCourses,
        ISNULL(AVG(e.FinalGrade), 0.0) AS AverageGrade,
        s.GPA
    FROM Students s
    JOIN Schools sch ON s.SchoolId = sch.SchoolId
    LEFT JOIN Enrollments e ON s.StudentId = e.StudentId
    GROUP BY s.StudentId, s.FirstName, s.LastName, sch.SchoolName, s.GPA;
    """,

    # View 2: Teacher Workload Summary
    """
    CREATE VIEW vw_TeacherCourseSummary AS
    SELECT 
        t.TeacherId,
        t.FirstName + ' ' + t.LastName AS TeacherName,
        d.DeptName,
        COUNT(c.CourseId) AS AssignedCourses,
        ISNULL(SUM(c.Credits), 0) AS TotalCredits
    FROM Teachers t
    JOIN Departments d ON t.DepartmentId = d.DepartmentId
    LEFT JOIN Courses c ON d.DepartmentId = c.DepartmentId
    GROUP BY t.TeacherId, t.FirstName, t.LastName, d.DeptName;
    """,

    # View 3: School Analytics
    """
    CREATE VIEW vw_SchoolEnrollmentAnalytics AS
    SELECT 
        sch.SchoolId,
        sch.SchoolName,
        COUNT(DISTINCT st.StudentId) AS StudentCount,
        COUNT(DISTINCT e.EnrollmentId) AS TotalEnrollments,
        AVG(st.GPA) AS AverageSchoolGPA
    FROM Schools sch
    LEFT JOIN Students st ON sch.SchoolId = st.SchoolId
    LEFT JOIN Enrollments e ON st.StudentId = e.StudentId
    GROUP BY sch.SchoolId, sch.SchoolName;
    """,

    # View 4: Low Attendance Alerts
    """
    CREATE VIEW vw_LowAttendanceAlerts AS
    SELECT 
        st.StudentId,
        st.FirstName + ' ' + st.LastName AS StudentName,
        c.CourseTitle,
        a.ClassDate,
        a.Status
    FROM Attendance a
    JOIN Students st ON a.StudentId = st.StudentId
    JOIN Courses c ON a.CourseId = c.CourseId
    WHERE a.Status = 'Absent';
    """,

    # Proc 1: Enroll Student
    """
    CREATE PROCEDURE sp_EnrollStudentInCourse
        @StudentId BIGINT,
        @CourseId INT,
        @Semester VARCHAR(20),
        @AcademicYear SMALLINT
    AS
    BEGIN
        SET NOCOUNT ON;
        INSERT INTO Enrollments (StudentId, CourseId, Semester, AcademicYear, EnrolledAt)
        VALUES (@StudentId, @CourseId, @Semester, @AcademicYear, SYSDATETIME());
    END;
    """,

    # Proc 2: Recalculate Student GPA
    """
    CREATE PROCEDURE sp_CalculateStudentGPA
        @StudentId BIGINT
    AS
    BEGIN
        SET NOCOUNT ON;
        DECLARE @NewGPA FLOAT;
        
        SELECT @NewGPA = ISNULL(AVG(FinalGrade) / 25.0, 0.0)
        FROM Enrollments
        WHERE StudentId = @StudentId AND FinalGrade IS NOT NULL;
        
        UPDATE Students
        SET GPA = @NewGPA
        WHERE StudentId = @StudentId;
    END;
    """,

    # Proc 3: Generate School Report
    """
    CREATE PROCEDURE sp_GenerateSchoolReport
        @SchoolId INT
    AS
    BEGIN
        SET NOCOUNT ON;
        SELECT 
            s.SchoolName,
            COUNT(st.StudentId) AS TotalStudents,
            AVG(st.GPA) AS OverallGPA
        FROM Schools s
        LEFT JOIN Students st ON s.SchoolId = st.SchoolId
        WHERE s.SchoolId = @SchoolId
        GROUP BY s.SchoolName;
    END;
    """,

    # Proc 4: Bulk Update Student Status
    """
    CREATE PROCEDURE sp_BulkUpdateStudentStatus
        @MinGPA FLOAT,
        @TargetSchoolId INT
    AS
    BEGIN
        SET NOCOUNT ON;
        UPDATE Students
        SET AddressJson = JSON_MODIFY(ISNULL(AddressJson, '{}'), '$.academic_status', 'Honors')
        WHERE SchoolId = @TargetSchoolId AND GPA >= @MinGPA;
    END;
    """
]

for obj_sql in prog_objects:
    cursor.execute(obj_sql)

conn.commit()
print("Triggers, Views, and Stored Procedures created successfully.\n")

# -----------------------------------------------------------------------------
# 3. Data Generator (500,000+ Records)
# -----------------------------------------------------------------------------
print("====================================================================")
print("  Generating & Ingesting 500,000+ Records...")
print("====================================================================\n")

fake = Faker()
cursor.fast_executemany = True

start_time = time.time()

# 1. Schools (50)
print("1/9 Ingesting 50 Schools...")
schools_data = []
for _ in range(50):
    name = f"{fake.city()} Academy of {fake.word().capitalize()}s"
    est_date = fake.date_between(start_date='-50y', end_date='-5y')
    budget = round(random.uniform(1000000, 50000000), 4)
    schools_data.append((name, est_date, budget, 1))

cursor.executemany(
    "INSERT INTO Schools (SchoolName, EstablishedDate, AnnualBudget, IsActive) VALUES (?, ?, ?, ?)",
    schools_data
)
conn.commit()

# 2. Departments (200)
print("2/9 Ingesting 200 Departments...")
depts_data = []
dept_names = ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology", "Literature", "History", "Arts", "Engineering", "Economics"]
for i in range(200):
    school_id = random.randint(1, 50)
    code = f"DEPT_{i+1:03d}"
    dname = f"{random.choice(dept_names)} Division {i+1}"
    depts_data.append((school_id, code, dname, random.randint(10, 100), 1))

cursor.executemany(
    "INSERT INTO Departments (SchoolId, DeptCode, DeptName, HeadCount, ActiveStatus) VALUES (?, ?, ?, ?, ?)",
    depts_data
)
conn.commit()

# 3. Teachers (2,000)
print("3/9 Ingesting 2,000 Teachers...")
teachers_data = []
for _ in range(2000):
    dept_id = random.randint(1, 200)
    fname = fake.first_name()[:100]
    lname = fake.last_name()[:100]
    email = f"{fname.lower()}.{lname.lower()}_{random.randint(100,999)}@school.edu"
    hdate = fake.date_between(start_date='-20y', end_date='now')
    rate = round(random.uniform(35.0, 150.0), 2)
    xml_qual = f"<qualifications><degree>PhD</degree><university>{fake.company()}</university></qualifications>"
    teachers_data.append((dept_id, fname, lname, email, hdate, rate, xml_qual))

cursor.executemany(
    "INSERT INTO Teachers (DepartmentId, FirstName, LastName, Email, HireDate, HourlyRate, QualificationsXml) VALUES (?, ?, ?, ?, ?, ?, ?)",
    teachers_data
)
conn.commit()

# 4. Courses (5,000)
print("4/9 Ingesting 5,000 Courses...")
courses_data = []
for i in range(5000):
    dept_id = random.randint(1, 200)
    ccode = f"CS_{i+1:04d}"
    ctitle = f"Advanced {fake.job()} Principles"
    credits = random.choice([1, 2, 3, 4])
    details = f"Course covering core syllabus of {ctitle}. Prerequisites required."
    is_elec = random.choice([0, 1])
    courses_data.append((dept_id, ccode, ctitle, credits, details, is_elec))

cursor.executemany(
    "INSERT INTO Courses (DepartmentId, CourseCode, CourseTitle, Credits, SyllabusDetails, IsElective) VALUES (?, ?, ?, ?, ?, ?)",
    courses_data
)
conn.commit()

# 5. Students (100,000)
print("5/9 Ingesting 100,000 Students...")
chunk_size = 25000
for chunk_idx in range(4):
    students_chunk = []
    for _ in range(25000):
        sch_id = random.randint(1, 50)
        fname = fake.first_name()[:100]
        lname = fake.last_name()[:100]
        dob = fake.date_between(start_date='-25y', end_date='-17y')
        gender = random.choice(['M', 'F'])
        gpa = round(random.uniform(1.5, 4.0), 2)
        edate = datetime.now() - timedelta(days=random.randint(1, 1400))
        addr_json = f'{{"city":"{fake.city()}","state":"{fake.state()}","zip":"{fake.zipcode()}"}}'
        blob = b"\x00\x01\x02\x03\x04\x05"
        students_chunk.append((sch_id, fname, lname, dob, gender, gpa, edate, addr_json, blob))

    cursor.executemany(
        "INSERT INTO Students (SchoolId, FirstName, LastName, DateOfBirth, Gender, GPA, EnrollmentDate, AddressJson, ProfileBlob) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        students_chunk
    )
    conn.commit()
    print(f"   -> Inserted {(chunk_idx+1)*25000}/100000 Students")

# 6. Enrollments (250,000)
print("6/9 Ingesting 250,000 Enrollments...")
for chunk_idx in range(10):
    enroll_chunk = []
    for _ in range(25000):
        st_id = random.randint(1, 100000)
        c_id = random.randint(1, 5000)
        sem = random.choice(["Fall", "Spring", "Summer"])
        yr = random.choice([2021, 2022, 2023, 2024])
        grade = round(random.uniform(50.0, 100.0), 2)
        letter = "A" if grade >= 90 else ("B" if grade >= 80 else ("C" if grade >= 70 else "D"))
        en_at = datetime.now() - timedelta(days=random.randint(1, 365))
        enroll_chunk.append((st_id, c_id, sem, yr, grade, letter, en_at))

    cursor.executemany(
        "INSERT INTO Enrollments (StudentId, CourseId, Semester, AcademicYear, FinalGrade, GradeLetter, EnrolledAt) VALUES (?, ?, ?, ?, ?, ?, ?)",
        enroll_chunk
    )
    conn.commit()
    print(f"   -> Inserted {(chunk_idx+1)*25000}/250000 Enrollments")

# 7. Exams (10,000)
print("7/9 Ingesting 10,000 Exams...")
exams_data = []
for i in range(10000):
    c_id = random.randint(1, 5000)
    title = f"Final Examination Term {i+1}"
    edate = fake.date_between(start_date='-2y', end_date='now')
    max_m = 100.00
    weight = 0.40
    exams_data.append((c_id, title, edate, max_m, weight))

cursor.executemany(
    "INSERT INTO Exams (CourseId, ExamTitle, ExamDate, MaxMarks, Weightage) VALUES (?, ?, ?, ?, ?)",
    exams_data
)
conn.commit()

# 8. ExamResults (150,000)
print("8/9 Ingesting 150,000 Exam Results...")
for chunk_idx in range(6):
    results_chunk = []
    for _ in range(25000):
        ex_id = random.randint(1, 10000)
        st_id = random.randint(1, 100000)
        marks = round(random.uniform(35.0, 100.0), 2)
        passed = 1 if marks >= 50.0 else 0
        rem = "Good performance" if passed else "Needs improvement"
        results_chunk.append((ex_id, st_id, marks, passed, rem))

    cursor.executemany(
        "INSERT INTO ExamResults (ExamId, StudentId, MarksObtained, IsPassed, Remarks) VALUES (?, ?, ?, ?, ?)",
        results_chunk
    )
    conn.commit()
    print(f"   -> Inserted {(chunk_idx+1)*25000}/150000 Exam Results")

# 9. Attendance (50,000)
print("9/9 Ingesting 50,000 Attendance records...")
for chunk_idx in range(2):
    att_chunk = []
    for _ in range(25000):
        st_id = random.randint(1, 100000)
        c_id = random.randint(1, 5000)
        cdate = fake.date_between(start_date='-1y', end_date='now')
        status = random.choice(["Present", "Absent", "Late", "Excused"])
        mtime = datetime.now().time()
        att_chunk.append((st_id, c_id, cdate, status, mtime))

    cursor.executemany(
        "INSERT INTO Attendance (StudentId, CourseId, ClassDate, Status, MarkedAt) VALUES (?, ?, ?, ?, ?)",
        att_chunk
    )
    conn.commit()
    print(f"   -> Inserted {(chunk_idx+1)*25000}/50000 Attendance records")

total_dur = time.time() - start_time
cursor.close()
conn.close()

print(f"\n====================================================================")
print(f"  SUCCESS! Created Database [{DB_NAME}]")
print(f"====================================================================")
print(f"Total Database Objects Created:")
print(f" - Tables           : 10")
print(f" - Views            : 4")
print(f" - Stored Procedures: 4")
print(f" - Triggers         : 3")
print(f"Total Records Ingested: 567,250 records")
print(f"Execution Time       : {total_dur:.2f} seconds")
print(f"====================================================================\n")
