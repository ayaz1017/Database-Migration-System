import pyodbc
from structlog import get_logger

logger = get_logger()


class MSSQLConnector:
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def get_connection_string(self):
        # Using ODBC Driver 17 for SQL Server as a default modern driver
        return f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.host},{self.port};DATABASE={self.database};UID={self.user};PWD={self.password};TrustServerCertificate=yes;"

    def connect(self):
        try:
            self.connection = pyodbc.connect(self.get_connection_string())
            logger.info(f"Connected to MSSQL database: {self.database}")
            return True
        except Exception as e:
            logger.error("Failed to connect to MSSQL", error=str(e))
            return False

    def close(self):
        if self.connection:
            self.connection.close()

    def test_connection(self):
        success = self.connect()
        if success:
            self.close()
            return {"status": "success", "message": "Connection successful"}
        return {"status": "error", "message": "Connection failed"}

    def execute_query(self, query: str, params: tuple = None):
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute(query, params or ())
        if query.strip().upper().startswith("SELECT"):
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        self.connection.commit()
        return None
