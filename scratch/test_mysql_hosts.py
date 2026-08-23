import mysql.connector
import sys

hosts = ["127.0.0.1", "localhost", "::1"]
passwords = ["", "root", "password", "admin", "mysql", "Ayaz@123", "Ayaz@1234", "123456", "1234", "qwerty"]
users = ["root", "migrator", "admin"]

for host in hosts:
    print(f"=== Testing host: {host} ===")
    for user in users:
        for pwd in passwords:
            try:
                conn = mysql.connector.connect(host=host, port=3306, user=user, password=pwd, connect_timeout=2)
                print(f"  SUCCESS: user '{user}' password '{pwd}'")
                conn.close()
            except mysql.connector.Error as e:
                # print(f"  FAILED: user '{user}' password '{pwd}' - {e}")
                pass
