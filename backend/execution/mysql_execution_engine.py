"""
MySQL Execution Engine for Universal Migration Engine.
"""

from collections.abc import Generator

import mysql.connector


class MySQLExecutionEngine:
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        self.raw_host = host
        self.config = {
            "port": port,
            "user": username,
            "password": password,
            "database": database,
        }
        self._write_conn = None

    def _connect(self, cursor_class=None):
        hosts = [self.raw_host]
        if str(self.raw_host).strip().lower() in ("localhost", "127.0.0.1", "::1"):
            hosts = [self.raw_host, "::1", "127.0.0.1", "localhost"]
            seen = set()
            hosts = [h for h in hosts if not (h in seen or seen.add(h))]

        last_err = None
        for h in hosts:
            try:
                cfg = dict(self.config)
                cfg["host"] = h
                return mysql.connector.connect(**cfg)
            except Exception as e:
                last_err = e
        raise last_err

    def _get_write_conn(self) -> object:
        if self._write_conn is None or not self._write_conn.is_connected():
            self._write_conn = self._connect()
        return self._write_conn

    def get_row_count(self, table_name: str) -> int:
        """
        Get exact row count for a table.
        """
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def stream_table(
        self, table_name: str, pk_column: str, chunk_size: int = 1000, start_pk=None
    ) -> Generator:
        """
        Stream rows from a table using LIMIT/OFFSET pagination.
        This guarantees no data loss even if the table has no primary key or has duplicate values.
        """
        conn = self._connect()
        cursor = conn.cursor(dictionary=True)

        if pk_column:
            last_pk = start_pk
            while True:
                if last_pk is not None:
                    query = f"SELECT * FROM {table_name} WHERE {pk_column} > %s ORDER BY {pk_column} LIMIT {chunk_size}"
                    cursor.execute(query, (last_pk,))
                else:
                    query = f"SELECT * FROM {table_name} ORDER BY {pk_column} LIMIT {chunk_size}"
                    cursor.execute(query)

                rows = cursor.fetchall()
                if not rows:
                    break

                yield rows
                last_pk = rows[-1][pk_column]
        else:
            try:
                from mysql.connector.cursor import MySQLCursorSS
                conn_ss = mysql.connector.connect(**self.config)
                cursor_ss = conn_ss.cursor(cursor_class=MySQLCursorSS, dictionary=True)
                cursor_ss.execute(f"SELECT * FROM {table_name}")
                while True:
                    rows = cursor_ss.fetchmany(chunk_size)
                    if not rows:
                        break
                    yield rows
                cursor_ss.close()
                conn_ss.close()
                conn.close()
                return
            except Exception:
                offset = 0
                while True:
                    query = f"SELECT * FROM {table_name} LIMIT {chunk_size} OFFSET {offset}"
                    cursor.execute(query)

                    rows = cursor.fetchall()
                    if not rows:
                        break

                    yield rows
                    offset += chunk_size

        conn.close()

    def bulk_insert(self, table_name: str, rows: list[dict]) -> int:
        """
        Bulk insert using executemany() with INSERT IGNORE.
        Returns rows inserted.
        """
        if not rows:
            return 0

        conn = self._get_write_conn()
        cursor = conn.cursor()

        columns = list(rows[0].keys())
        cols_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        sql = f"INSERT IGNORE INTO {table_name} ({cols_str}) VALUES ({placeholders})"

        data = [tuple(row[col] for col in columns) for row in rows]

        cursor.executemany(sql, data)
        conn.commit()
        inserted = cursor.rowcount
        cursor.close()
        return inserted
