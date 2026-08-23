import pyodbc

servers_to_test = [
    "localhost",
    "127.0.0.1",
    ".",
    ".\\SQLEXPRESS",
    "localhost\\SQLEXPRESS",
    "127.0.0.1,1433",
    "(localdb)\\MSSQLLocalDB"
]

drivers_to_test = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server"
]

password = "Ayaz@123"
user = "sa"

working_conn_str = None

for server in servers_to_test:
    if working_conn_str:
        break
    for driver in drivers_to_test:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};UID={user};PWD={password};DATABASE=master;TrustServerCertificate=yes;"
        try:
            print(f"Testing: SERVER={server}, DRIVER={driver}...", end=" ")
            conn = pyodbc.connect(conn_str, timeout=3)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            row = cursor.fetchone()
            print("SUCCESS!")
            print(f"Connected to: {row[0][:50]}")
            working_conn_str = (server, driver)
            conn.close()
            break
        except Exception as e:
            print(f"FAILED: {str(e)[:60]}")

if working_conn_str:
    print(f"\nWORKING CONFIG: Server='{working_conn_str[0]}', Driver='{working_conn_str[1]}'")
else:
    print("\nCould not find a working connection string. Checking ODBC drivers installed...")
    print("Installed ODBC drivers:", pyodbc.drivers())
