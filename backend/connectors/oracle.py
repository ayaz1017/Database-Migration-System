import oracledb
from structlog import get_logger

logger = get_logger()

class OracleConnector:
    def __init__(self, host, port, service_name, user, password):
        self.host = host
        self.port = port
        self.service_name = service_name
        self.user = user
        self.password = password
        self.dsn = f"{host}:{port}/{service_name}"
        self.connection = None

    def connect(self):
        try:
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            logger.info(f"Connected to Oracle database service: {self.service_name}")
            return True
        except Exception as e:
            logger.error("Failed to connect to Oracle", error=str(e))
            return False

    def close(self):
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection = None

    def test_connection(self):
        try:
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            cursor = self.connection.cursor()
            
            # Check server version
            server_version = self.connection.version
            
            # Check SELECT ANY TABLE privilege
            cursor.execute("""
                SELECT privilege 
                FROM session_privs 
                WHERE privilege = 'SELECT ANY TABLE'
            """)
            has_privilege = cursor.fetchone() is not None
            
            self.close()
            
            if not has_privilege:
                return {
                    "status": "error",
                    "message": f"Connection successful (Oracle {server_version}), but missing required 'SELECT ANY TABLE' privilege."
                }
                
            return {
                "status": "success", 
                "message": f"Connection successful (Oracle {server_version})"
            }
        except Exception as e:
            logger.error("Failed to connect to Oracle during test", error=str(e))
            return {"status": "error", "message": f"Connection failed: {str(e)}"}

    def execute_query(self, query: str, params: tuple = None):
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        
        # In oracledb, we can get dict-like results by setting rowfactory
        cursor.execute(query, params or ())
        
        if query.strip().upper().startswith("SELECT"):
            columns = [col[0].lower() for col in cursor.description]
            cursor.rowfactory = lambda *args: dict(zip(columns, args))
            results = cursor.fetchall()
            cursor.close()
            return results
            
        self.connection.commit()
        cursor.close()
        return None
