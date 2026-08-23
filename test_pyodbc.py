import pyodbc
import binascii

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;UID=sa;PWD=Ayaz@123;DATABASE=migrated_sql"
conn = pyodbc.connect(conn_str)

cursor = conn.cursor()
try:
    cursor.execute("CREATE TABLE #temp_test (id INT, dto DATETIMEOFFSET)")
    cursor.execute("INSERT INTO #temp_test VALUES (1, '2026-06-21 21:35:53.5600226 +05:30')")

    def dto_handler(value):
        print("Received value:", binascii.hexlify(value))
        # Usually it's unpacked like: struct.unpack("<hBBBBBiihh", ...)
        return str(value)

    conn.add_output_converter(-155, dto_handler)

    cursor.execute("SELECT dto FROM #temp_test")
    row = cursor.fetchone()
    print("Handled row:", row)
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
