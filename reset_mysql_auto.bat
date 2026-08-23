@echo off
echo =========================================
echo MySQL Root Password Reset Script
echo =========================================
echo.
echo Stopping MySQL Service...
net stop MYSQL80

echo.
echo ALTER USER 'root'@'localhost' IDENTIFIED BY 'Ayaz@123'; > C:\mysql-init.txt
echo CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY 'Ayaz@123'; >> C:\mysql-init.txt
echo ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY 'Ayaz@123'; >> C:\mysql-init.txt
echo CREATE USER IF NOT EXISTS 'root'@'%%' IDENTIFIED BY 'Ayaz@123'; >> C:\mysql-init.txt
echo ALTER USER 'root'@'%%' IDENTIFIED BY 'Ayaz@123'; >> C:\mysql-init.txt
echo GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION; >> C:\mysql-init.txt
echo GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION; >> C:\mysql-init.txt
echo GRANT ALL PRIVILEGES ON *.* TO 'root'@'%%' WITH GRANT OPTION; >> C:\mysql-init.txt
echo FLUSH PRIVILEGES; >> C:\mysql-init.txt

echo.
echo Starting MySQL to apply reset (this takes ~10 seconds)...
start "MySQL Reset" "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe" --defaults-file="C:\ProgramData\MySQL\MySQL Server 8.0\my.ini" --init-file="C:\mysql-init.txt" --console

timeout /t 12 /nobreak

echo.
echo Killing the temporary MySQL process...
taskkill /F /IM mysqld.exe

echo.
echo Restarting MySQL Service normally...
net start MYSQL80

echo.
echo Cleaning up...
del C:\mysql-init.txt

echo.
echo =========================================
echo Done! The password for 'root' is now Ayaz@123.
echo You can now click RETRY on the UI!
echo =========================================
