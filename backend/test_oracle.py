import oracledb

conn = oracledb.connect(user="ayaz", password="Oracle123", dsn="localhost:1521/XEPDB1")
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM students")
print("Row count:", cursor.fetchone()[0])
conn.close()
