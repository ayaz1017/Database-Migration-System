"""
MSSQL Execution Engine for Universal Migration Engine.
"""

from collections.abc import Generator

import pyodbc


class MSSQLExecutionEngine:
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        self.conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};UID={username};PWD={password};DATABASE={database};TrustServerCertificate=yes;"
        self._write_conn = None

    def _get_write_conn(self) -> object:
        import pyodbc

        try:
            if self._write_conn is None:
                self._write_conn = pyodbc.connect(self.conn_str)
            else:
                self._write_conn.execute("SELECT 1").fetchone()
        except:
            self._write_conn = pyodbc.connect(self.conn_str)
        return self._write_conn

    def get_row_count(self, table_name: str) -> int:
        """
        Get exact row count for a table.
        """
        conn = pyodbc.connect(self.conn_str)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def stream_table(
        self, table_name: str, chunk_size: int = 1000, table_schema: dict = None
    ) -> Generator:
        """
        Stream rows from a table using server-side cursor.
        NEVER call fetchall().
        """
        conn = pyodbc.connect(self.conn_str)
        cursor = conn.cursor()
        try:
            cursor.execute("SET NOCOUNT ON")
        except Exception:
            pass

        # In pyodbc, setting arraysize affects fetchmany efficiency
        cursor.arraysize = chunk_size

        select_clause = "*"
        if table_schema and "columns" in table_schema:
            col_exprs = []
            for col in table_schema["columns"]:
                col_name = col["name"]
                col_type = col.get("type", "").lower()

                if col_type == "bit":
                    col_exprs.append(
                        f"CASE WHEN [{col_name}] = 1 THEN 'true' WHEN [{col_name}] = 0 THEN 'false' ELSE NULL END AS [{col_name}]"
                    )
                elif "datetimeoffset" in col_type:
                    # 127 is ISO8601 with timezone Z
                    col_exprs.append(f"CONVERT(varchar(50), [{col_name}], 127) AS [{col_name}]")
                elif "datetime" in col_type:  # handles datetime and datetime2
                    # 121 is yyyy-mm-dd hh:mi:ss.mmm
                    col_exprs.append(f"CONVERT(varchar(50), [{col_name}], 121) AS [{col_name}]")
                else:
                    col_exprs.append(f"[{col_name}]")
            select_clause = ", ".join(col_exprs)

        cursor.execute(f"SELECT {select_clause} FROM [{table_name}]")

        # Get column names
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
        Bulk insert using highly optimized multi-row INSERT statements.
        This bypasses buggy pyodbc fast_executemany silent failures and respects the 2100 parameter limit.
        """
        if not rows:
            return 0

        conn = self._get_write_conn()
        cursor = conn.cursor()

        columns = list(rows[0].keys())
        cols_str = ", ".join(f"[{col}]" for col in columns)

        # MSSQL allows max 2100 parameters per query. Leave a small buffer.
        max_params = 2000
        batch_size = max(1, max_params // len(columns))

        total_inserted = 0
        import decimal

        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            placeholders = []
            data = []

            for row in batch:
                row_placeholders = []
                for col in columns:
                    val = row[col]
                    if isinstance(val, decimal.Decimal):
                        val = float(val)
                    # Convert empty strings to None for numeric/date columns to prevent silent PyODBC crashes
                    elif val == "":
                        val = None
                    elif hasattr(val, "isoformat"):
                        val = str(val)
                    data.append(val)
                    row_placeholders.append("?")
                placeholders.append("(" + ", ".join(row_placeholders) + ")")

            sql = f"INSERT INTO [{table_name}] ({cols_str}) VALUES " + ", ".join(placeholders)

            try:
                cursor.execute(sql, data)
                total_inserted += cursor.rowcount if cursor.rowcount > 0 else len(batch)
            except Exception:
                # Fallback to row-by-row for this specific batch if it contains dirty data
                for row in batch:
                    try:
                        row_data = [
                            float(row[col])
                            if isinstance(row[col], decimal.Decimal)
                            else (str(row[col]) if hasattr(row[col], "isoformat") else (None if row[col] == "" else row[col]))
                            for col in columns
                        ]
                        row_sql = f"INSERT INTO [{table_name}] ({cols_str}) VALUES ({', '.join(['?'] * len(columns))})"
                        cursor.execute(row_sql, row_data)
                        total_inserted += 1
                    except Exception as inner_e:
                        msg = f"Warning: Dropped dirty row in {table_name}: {inner_e}"
                        print(msg.encode('ascii', 'backslashreplace').decode('ascii'))

        conn.commit()
        cursor.close()
        return total_inserted
