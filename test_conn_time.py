import time
import pyodbc

print("Testing without port:")
start = time.time()
try:
    conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1;DATABASE=ComplexDB;UID=sa;PWD=Ayaz@123;TrustServerCertificate=yes;", timeout=5)
    print("Success in", time.time() - start)
    conn.close()
except Exception as e:
    print("Failed in", time.time() - start, e)

print("Testing with port ,1433:")
start = time.time()
try:
    conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};SERVER=127.0.0.1,1433;DATABASE=ComplexDB;UID=sa;PWD=Ayaz@123;TrustServerCertificate=yes;", timeout=5)
    print("Success in", time.time() - start)
    conn.close()
except Exception as e:
    print("Failed in", time.time() - start, e)
