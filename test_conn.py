import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.connectors.mssql import MSSQLConnector

connector = MSSQLConnector(host="127.0.0.1", port=1433, database="ComplexDB", user="sa", password="Ayaz@123")
print("Connecting with:", connector.get_connection_string())
success = connector.connect()
if success:
    print("SUCCESS")
else:
    print("FAILED")
