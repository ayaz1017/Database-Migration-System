import oracledb

conn = oracledb.connect(user="pdbadmin", password="Oracle123", dsn="localhost:1521/ORACLEDB")
cursor = conn.cursor()
try:
    cursor.execute("SELECT * FROM session_privs WHERE privilege LIKE '%TABLE%'")
    privs = cursor.fetchall()
    print("Privileges:", privs)

    cursor.execute("SELECT * FROM user_sys_privs")
    print("Sys privs:", cursor.fetchall())
except Exception as e:
    print("ERROR:", e)
conn.close()
