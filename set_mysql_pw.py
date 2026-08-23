import mysql.connector
conn=mysql.connector.connect(host='127.0.0.1', port=3307, user='root', password='')
cursor = conn.cursor()
cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY 'Ayaz@123'")
cursor.execute("CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'Ayaz@123'")
cursor.execute("GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION")
cursor.execute("FLUSH PRIVILEGES")
conn.commit()
print('Password updated to Ayaz@123')
