"""
PostgreSQL Execution Engine for Universal Migration Engine.
"""

import platform
import shutil
import subprocess
from collections.abc import Generator

import psycopg2


class PostgresExecutionEngine:
    def __init__(self, host: str, port: int, username: str, password: str, database: str):
        self.config = {
            "host": host,
            "port": port,
            "user": username,
            "password": password,
            "dbname": database,
        }
        self._write_conn = None

    def _get_write_conn(self) -> object:
        if self._write_conn is None or self._write_conn.closed:
            self._write_conn = psycopg2.connect(**self.config)
        return self._write_conn

        # Auto-detect pgloader
        os_name = platform.system().lower()
        pgloader_path = shutil.which("pgloader")

        if os_name == "windows":
            # Check if pgloader is available in WSL
            try:
                import subprocess

                res = subprocess.run(["wsl", "which", "pgloader"], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    self.mode = "wsl_pgloader"
                else:
                    self.mode = "streaming_fallback"
            except Exception:
                self.mode = "streaming_fallback"
        elif os_name in ["linux", "ubuntu"] and pgloader_path:
            self.mode = "native_pgloader"
        else:
            self.mode = "streaming_fallback"

    def get_row_count(self, table_name: str) -> int:
        """
        Get exact row count for a table.
        """
        conn = psycopg2.connect(**self.config)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def stream_table(self, table_name: str, chunk_size: int = 1000) -> Generator:
        """
        Stream rows from a table (fallback mode).
        """
        conn = psycopg2.connect(**self.config)

        # Get columns first with normal cursor
        normal_cursor = conn.cursor()
        normal_cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
        columns = [desc[0] for desc in normal_cursor.description]
        normal_cursor.close()

        # Using server-side cursor by naming it
        cursor = conn.cursor(name=f"cursor_stream_{table_name}")
        cursor.itersize = chunk_size

        cursor.execute(f"SELECT * FROM {table_name}")

        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break

            chunk = [dict(zip(columns, row)) for row in rows]
            yield chunk

        cursor.close()
        conn.close()

    def convert_to_wsl_path(self, windows_path: str) -> str:
        """
        Helper to convert Windows path to WSL path.
        """
        try:
            result = subprocess.run(
                ["wsl", "wslpath", "-a", windows_path], capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except Exception:
            return windows_path  # Return as is if conversion fails

    def generate_pgloader_config(self, source_conn: str, target_conn: str, table_name: str) -> str:
        """
        Generate a valid .load file content string.
        """
        config = f"""
LOAD DATABASE
     FROM      {source_conn}
     INTO      {target_conn}

 INCLUDING ONLY TABLE NAMES MATCHING ~/{table_name}/

 WITH include drop, create tables, create indexes, reset sequences

  SET work_mem to '16MB', maintenance_work_mem to '512 MB';
"""
        return config

    def run_pgloader(self, config_path: str) -> dict:
        """
        Execute pgloader.
        """
        cmd = ["pgloader", config_path]
        if self.mode == "wsl_pgloader":
            cmd = ["wsl"] + cmd

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0
            return {
                "success": success,
                "rows": -1,  # We could parse stdout to get actual rows
                "errors": [result.stderr] if result.stderr else [],
            }
        except Exception as e:
            return {"success": False, "rows": 0, "errors": [str(e)]}

    def migrate_table(self, source_conn: str, target_conn: str, table_name: str) -> dict:
        """
        Auto-selects pgloader or streaming_fallback based on self.mode.
        """
        if self.mode in ["native_pgloader", "wsl_pgloader"]:
            import os
            import tempfile

            config_content = self.generate_pgloader_config(source_conn, target_conn, table_name)

            with tempfile.NamedTemporaryFile(mode="w", suffix=".load", delete=False) as f:
                f.write(config_content)
                config_path = f.name

            if self.mode == "wsl_pgloader":
                config_path = self.convert_to_wsl_path(config_path)

            result = self.run_pgloader(config_path)
            os.remove(f.name)
            return result
        else:
            # Fallback to streaming - requires external orchestrator to pull and push
            return {"success": True, "mode": "streaming_fallback_required", "errors": []}

    def _convert_value(self, val: object) -> object:
        """
        Convert Python values to strings suitable for PostgreSQL COPY CSV format.
        """
        if val is None:
            return None
        if isinstance(val, bool):
            # PostgreSQL COPY expects 't'/'f' for booleans, not 'True'/'False'
            return "t" if val else "f"
        if isinstance(val, (int, float)):
            return str(val)
        import datetime
        import decimal

        if isinstance(val, decimal.Decimal):
            return str(val)
        if isinstance(val, datetime.datetime):
            # Handles both timezone-aware (datetimeoffset) and naive (datetime/datetime2)
            return val.isoformat()
        if isinstance(val, datetime.date):
            return val.isoformat()
        if isinstance(val, datetime.time):
            return val.isoformat()
        if isinstance(val, datetime.timedelta):
            total_seconds = int(val.total_seconds())
            hours, remainder = divmod(abs(total_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            sign = "-" if total_seconds < 0 else ""
            return f"{sign}{hours:02}:{minutes:02}:{seconds:02}"
        if isinstance(val, bytes):
            # PostgreSQL BYTEA hex format
            return "\\x" + val.hex()
        # Fallback: convert to string
        return str(val)

    def bulk_insert(self, table_name: str, rows: list[dict]) -> int:
        """
        Bulk insert using PostgreSQL COPY command for massive speedup.
        """
        if not rows:
            return 0

        import csv
        import io

        conn = self._get_write_conn()
        cursor = conn.cursor()

        columns = list(rows[0].keys())
        cols_str = ", ".join(columns)

        # Convert all values to COPY-compatible strings
        converted_rows = []
        for row in rows:
            converted = {}
            for col in columns:
                converted[col] = self._convert_value(row[col])
            converted_rows.append(converted)

        f = io.StringIO()
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writerows(converted_rows)
        f.seek(0)

        try:
            cursor.copy_expert(f"COPY {table_name} ({cols_str}) FROM STDIN WITH CSV NULL ''", f)
            conn.commit()
            inserted = len(
                rows
            )  # copy_expert doesn't return rowcount reliably in all psycopg2 versions
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            import uuid

            temp_table = f"{table_name}_temp_{uuid.uuid4().hex[:8]}"

            try:
                # Create a temporary table with the same schema
                cursor.execute(
                    f"CREATE TEMP TABLE {temp_table} (LIKE {table_name} INCLUDING ALL) ON COMMIT DROP"
                )
                f.seek(0)
                # Load data into the temp table
                cursor.copy_expert(f"COPY {temp_table} ({cols_str}) FROM STDIN WITH CSV", f)
                # Insert from temp table to actual table ignoring conflicts
                cursor.execute(
                    f"INSERT INTO {table_name} SELECT * FROM {temp_table} ON CONFLICT DO NOTHING"
                )
                inserted = cursor.rowcount
                conn.commit()
            except Exception as inner_e:
                conn.rollback()
                raise inner_e
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

        return inserted
