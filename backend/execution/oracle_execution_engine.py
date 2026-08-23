"""
Oracle Execution Engine for Universal Migration Engine.
"""

from collections.abc import Generator

import oracledb


class OracleExecutionEngine:
    def __init__(self, host: str, port: int, username: str, password: str, service_name: str):
        self.username = username
        self.password = password
        self.dsn = f"{host}:{port}/{service_name}"

        # Oracle requires explicit handling for LOBs if you don't want LOB locators returned
        oracledb.defaults.fetch_lobs = False
        self._write_conn = None

    def _get_write_conn(self) -> object:
        if self._write_conn is None:
            self._write_conn = oracledb.connect(
                user=self.username, password=self.password, dsn=self.dsn
            )
        else:
            try:
                self._write_conn.ping()
            except:
                self._write_conn = oracledb.connect(
                    user=self.username, password=self.password, dsn=self.dsn
                )
        return self._write_conn

    def _get_connection(self) -> object:
        return oracledb.connect(user=self.username, password=self.password, dsn=self.dsn)

    def check_privileges(self) -> dict:
        """
        Check for necessary schema privileges (CREATE TABLE, INSERT, CREATE SEQUENCE, etc.)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT privilege FROM session_privs")
        privs = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        required = ["CREATE TABLE", "CREATE SEQUENCE", "CREATE TRIGGER"]
        missing = [p for p in required if p not in privs]
        
        # Also need INSERT ANY TABLE if target schema is different, but assuming we migrate to our own schema.
        
        if missing:
            return {"status": "error", "message": f"Missing required privileges: {', '.join(missing)}"}
        return {"status": "success", "message": "All required privileges present."}

    def sync_sequences(self, table_name: str, pk_column: str = None) -> None:
        """
        Sync sequence with max value after bulk insert.
        """
        if not pk_column:
            return
            
        conn = self._get_write_conn()
        cursor = conn.cursor()
        
        seq_name = f"{table_name[:30]}_{pk_column}_seq"[:30]
        
        try:
            # Get current max value
            cursor.execute(f"SELECT MAX({pk_column}) FROM {table_name}")
            max_val = cursor.fetchone()[0]
            if not max_val:
                return
                
            # Get current sequence value
            cursor.execute(f"SELECT {seq_name}.NEXTVAL FROM sys.dual")
            curr_seq = cursor.fetchone()[0]
            
            diff = max_val - curr_seq
            if diff > 0:
                cursor.execute(f"ALTER SEQUENCE {seq_name} INCREMENT BY {diff}")
                cursor.execute(f"SELECT {seq_name}.NEXTVAL FROM sys.dual")
                cursor.execute(f"ALTER SEQUENCE {seq_name} INCREMENT BY 1")
                conn.commit()
        except Exception as e:
            # Just ignore if sequence doesn't exist
            pass
        finally:
            cursor.close()

    def get_row_count(self, table_name: str) -> int:
        """
        Get exact row count for a table.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def stream_table(self, table_name: str, chunk_size: int = 1000) -> Generator:
        """
        Stream rows from a table using server-side cursor.
        NEVER call fetchall().
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.arraysize = chunk_size

        cursor.execute(f"SELECT * FROM {table_name}")

        # Get column names (Oracle returns them uppercase by default)
        columns = [column[0] for column in cursor.description]

        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break

            chunk = [dict(zip(columns, row)) for row in rows]
            yield chunk

        conn.close()

    def bulk_insert(self, table_name: str, rows: list[dict]) -> int:
        """
        Bulk insert using executemany() with batcherrors=True.
        Handles LOB > 32KB via setinputsizes() or explicit writes if needed.
        Detects empty string -> NULL Oracle behavior.
        """
        if not rows:
            return 0

        conn = self._get_write_conn()
        cursor = conn.cursor()

        columns = list(rows[0].keys())
        cols_str = ", ".join(columns)
        placeholders = ", ".join([f":{i + 1}" for i in range(len(columns))])
        sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"

        has_empty_string = False
        data = []
        for row in rows:
            t_row = []
            for col in columns:
                val = row[col]
                if isinstance(val, str):
                    if val == "":
                        has_empty_string = True
                    # Check for large strings (LOB) > 32KB
                    # oracledb thick mode can handle up to 1GB if we just pass strings,
                    # but if we need explicit LOB mapping we would setinputsizes.
                    # Recent oracledb versions handle strings > 32KB natively without setinputsizes.
                t_row.append(val)
            data.append(tuple(t_row))

        if has_empty_string:
            msg = f"WARNING: Empty strings detected during insert into {table_name}. Oracle treats '' as NULL."
            print(msg.encode('ascii', 'backslashreplace').decode('ascii'))

        try:
            # Enable batch errors
            cursor.executemany(sql, data, batcherrors=True)
            
            for error in cursor.getbatcherrors():
                msg = f"Error at row offset {error.offset}: {error.message}"
                print(msg.encode('ascii', 'backslashreplace').decode('ascii'))
                
            conn.commit()
            inserted = cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            
        return inserted

    def apply_ddl(self, ddl_statements: list[str]) -> dict:
        """
        Execute each DDL statement individually.
        Returns {"applied": [str], "failed": [{"ddl": str, "error": str}]}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        applied = []
        failed = []

        for ddl in ddl_statements:
            if not ddl.strip():
                continue
            try:
                cursor.execute(ddl)
                applied.append(ddl)
            except Exception as e:
                failed.append({"ddl": ddl, "error": str(e)})

        conn.close()
        return {"applied": applied, "failed": failed}
