import psycopg2
from psycopg2.extras import DictCursor
from structlog import get_logger

logger = get_logger()


class PostgresConnector:
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        host = "127.0.0.1" if str(self.host).strip().lower() in ("localhost", "::1") else self.host
        target_db = self.database or "postgres"
        try:
            self.connection = psycopg2.connect(
                host=host,
                port=self.port,
                dbname=target_db,
                user=self.user,
                password=self.password,
            )
            logger.info(f"Connected to PostgreSQL database: {target_db}")
            return True
        except Exception as err:
            if target_db != target_db.lower():
                try:
                    self.connection = psycopg2.connect(
                        host=host,
                        port=self.port,
                        dbname=target_db.lower(),
                        user=self.user,
                        password=self.password,
                    )
                    logger.info(f"Connected to PostgreSQL database: {target_db.lower()}")
                    return True
                except Exception:
                    pass
            logger.error("Failed to connect to PostgreSQL", error=str(err))
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
        with self.connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                return [dict(row) for row in cursor.fetchall()]
            self.connection.commit()
            return None
