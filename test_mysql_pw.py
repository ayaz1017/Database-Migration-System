import mysql.connector

passwords = ["", "root", "password", "admin", "mysql", "Ayaz@123", "Ayaz@1234", "123456", "1234", "qwerty"]
users = ["root", "migrator", "admin"]

success = False
for user in users:
    for pwd in passwords:
        try:
            conn = mysql.connector.connect(host="127.0.0.1", port=3306, user=user, password=pwd)
            print(f"SUCCESS: user '{user}' with password '{pwd}'")
            success = True
            conn.close()
            break
        except mysql.connector.Error as e:
            pass
    if success:
        break

if not success:
    print("ALL FAILED")
