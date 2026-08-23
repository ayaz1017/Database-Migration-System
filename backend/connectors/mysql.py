import mysql.connector
from structlog import get_logger

logger = get_logger()


class MySQLConnector:
    def __init__(self, host, port, database, user, password):
        self.raw_host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        hosts_to_try = [self.raw_host]
        if str(self.raw_host).strip().lower() in ("localhost", "127.0.0.1", "::1"):
            hosts_to_try = [self.raw_host, "::1", "127.0.0.1", "localhost"]
            seen = set()
            hosts_to_try = [h for h in hosts_to_try if not (h in seen or seen.add(h))]

        last_error = None
        for h in hosts_to_try:
            try:
                self.connection = mysql.connector.connect(
                    host=h,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                )
                logger.info(f"Connected to MySQL database: {self.database} via {h}")
                return True
            except Exception as e:
                last_error = e
        logger.error("Failed to connect to MySQL", error=str(last_error))
        return False

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def test_connection(self):
        success = self.connect()
        if success:
            self.close()
            return {"status": "success", "message": "Connection successful"}
        return {"status": "error", "message": "Connection failed"}

    def execute_query(self, query: str, params: tuple = None):
        if not self.connection or not self.connection.is_connected():
            self.connect()
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            cursor.close()
            return results
        self.connection.commit()
        cursor.close()
        return None
