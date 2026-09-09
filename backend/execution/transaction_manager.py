from structlog import get_logger

logger = get_logger()


class TransactionManager:
    def __init__(self, target_conn, db_type: str, group_tables: list[str], job_id: str = None):
        self.job_id = job_id
        self.conn = target_conn
        self.db_type = db_type.lower()
        self.group_tables = group_tables
        self.cursor = self.conn.cursor()

    def check_privileges(self) -> bool:
        if self.db_type in ["postgres", "postgresql"]:
            try:
                self.cursor.execute("SELECT current_setting('is_superuser')")
                res = self.cursor.fetchone()
                if res and res[0] == "on":
                    return True
                # If not superuser, try setting role to test if they have replication privileges
                self.cursor.execute("SET session_replication_role = 'replica'")
                self.cursor.execute("SET session_replication_role = 'origin'")
                return True
            except Exception:
                self.conn.rollback()
                return False

        elif self.db_type == "mysql":
            self.cursor.execute("SHOW GRANTS FOR CURRENT_USER")
            grants = self.cursor.fetchall()
            for grant in grants:
                grant_str = grant[0].upper()
                if (
                    "ALL PRIVILEGES" in grant_str
                    or "SUPER" in grant_str
                    or "SESSION_VARIABLES_ADMIN" in grant_str
                ):
                    return True
            return False

        elif self.db_type == "mssql":
            for table in self.group_tables:
                self.cursor.execute(f"SELECT HAS_PERMS_BY_NAME('{table}', 'OBJECT', 'ALTER')")
                res = self.cursor.fetchone()
                if not res or res[0] == 0:
                    return False
            return True

        return True

    def get_missing_privilege_error(self, current_user: str) -> str:
        group_str = ", ".join(self.group_tables)
        if self.db_type in ["postgres", "postgresql"]:
            req = "superuser or REPLICATION role privileges"
        elif self.db_type == "mysql":
            req = "SUPER or SESSION_VARIABLES_ADMIN privilege"
        elif self.db_type == "mssql":
            req = "ALTER permission on the affected tables"
        else:
            req = "appropriate privileges"

        return (
            f"circular dependency group: [{group_str}] requires {req}. "
            f"Current user: {current_user}. "
            "Grant the required privilege to this user, or provide credentials for a user that has it, then retry the migration."
        )

    def begin_transaction(self) -> None:
        if hasattr(self.conn, "autocommit"):
            self.conn.autocommit = False
        elif hasattr(self.conn, "start_transaction"):
            self.conn.start_transaction()

    def disable_constraints(self):
        if self.db_type in ["postgres", "postgresql"]:
            self.cursor.execute("SET session_replication_role = 'replica'")
        elif self.db_type == "mysql":
            self.cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        elif self.db_type == "mssql":
            for table in self.group_tables:
                self.cursor.execute(f"ALTER TABLE {table} NOCHECK CONSTRAINT ALL")
        elif self.db_type == "oracle":
            for table in self.group_tables:
                try:
                    self.cursor.execute(f"SELECT constraint_name FROM user_constraints WHERE table_name = UPPER('{table}') AND constraint_type = 'R'")
                    for (cname,) in self.cursor.fetchall():
                        self.cursor.execute(f"ALTER TABLE {table} DISABLE CONSTRAINT {cname}")
                except Exception:
                    pass

    def enable_constraints(self) -> None:
        if self.db_type in ["postgres", "postgresql"]:
            self.cursor.execute("SET session_replication_role = 'origin'")
        elif self.db_type == "mysql":
            self.cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        elif self.db_type == "mssql":
            for table in self.group_tables:
                self.cursor.execute(f"ALTER TABLE {table} CHECK CONSTRAINT ALL")
        elif self.db_type == "oracle":
            for table in self.group_tables:
                try:
                    self.cursor.execute(f"SELECT constraint_name FROM user_constraints WHERE table_name = UPPER('{table}') AND constraint_type = 'R'")
                    for (cname,) in self.cursor.fetchall():
                        self.cursor.execute(f"ALTER TABLE {table} ENABLE CONSTRAINT {cname}")
                except Exception:
                    pass

    def validate_constraints(self) -> list[dict]:
        violations = []
        if self.db_type == "mssql":
            for table in self.group_tables:
                try:
                    self.cursor.execute(f"DBCC CHECKCONSTRAINTS ('{table}')")
                    res = self.cursor.fetchall()
                    if res:
                        violations.append({"table": table, "violations": len(res)})
                except Exception:
                    pass
        return violations

    def _save_dropped_indexes(self, table: str, indexes: list[str]):
        if not self.job_id:
            return
        import json
        import os

        from backend.database import get_db

        with get_db() as (conn, c):
            c.execute("SELECT full_payload FROM migration_jobs WHERE id = ?", (self.job_id,))
            row = c.fetchone()
            if row and row[0]:
                payload = json.loads(row[0])
                if "dropped_indexes" not in payload:
                    payload["dropped_indexes"] = {}
                if table not in payload["dropped_indexes"]:
                    payload["dropped_indexes"][table] = []
                payload["dropped_indexes"][table].extend(indexes)
                c.execute(
                    "UPDATE migration_jobs SET full_payload = ? WHERE id = ?",
                    (json.dumps(payload), self.job_id),
                )

    def _get_dropped_indexes(self, table: str) -> list[str]:
        if not self.job_id:
            return []
        import json

        from backend.database import get_db

        with get_db() as (conn, c):
            c.execute("SELECT full_payload FROM migration_jobs WHERE id = ?", (self.job_id,))
            row = c.fetchone()
            if row and row[0]:
                payload = json.loads(row[0])
                return payload.get("dropped_indexes", {}).get(table, [])
        return []

    def _clear_dropped_indexes(self, table: str):
        if not self.job_id:
            return
        import json

        from backend.database import get_db

        with get_db() as (conn, c):
            c.execute("SELECT full_payload FROM migration_jobs WHERE id = ?", (self.job_id,))
            row = c.fetchone()
            if row and row[0]:
                payload = json.loads(row[0])
                if "dropped_indexes" in payload and table in payload["dropped_indexes"]:
                    del payload["dropped_indexes"][table]
                    c.execute(
                        "UPDATE migration_jobs SET full_payload = ? WHERE id = ?",
                        (json.dumps(payload), self.job_id),
                    )

    def disable_indexes_for_table(self, table: str, row_count: int):
        import os

        threshold = int(os.environ.get("INDEX_DISABLE_THRESHOLD", 100000))
        if row_count < threshold:
            return

        if self.db_type in ["postgres", "postgresql"]:
            try:
                self.cursor.execute(
                    f"SELECT indexname, indexdef FROM pg_indexes WHERE tablename = '{table}' AND indexname NOT IN (SELECT conname FROM pg_constraint WHERE contype = 'p')"
                )
                indexes = self.cursor.fetchall()
                if indexes:
                    defs = [idx[1] for idx in indexes]
                    self._save_dropped_indexes(table, defs)
                    for idx in indexes:
                        self.cursor.execute(f"DROP INDEX IF EXISTS {idx[0]}")
                    logger.info(f"Disabled indexes for {table} ({len(indexes)} dropped)")
            except Exception as e:
                logger.warning(f"Failed to drop indexes for {table}: {e}")
        elif self.db_type == "mysql":
            try:
                self.cursor.execute(f"ALTER TABLE {table} DISABLE KEYS")
                logger.info(f"Disabled keys for {table}")
            except Exception:
                pass
        elif self.db_type == "mssql":
            if not hasattr(self, "_use_tablock_cache"):
                self._use_tablock_cache = {}
            self._use_tablock_cache[table] = True
            logger.info(f"Enabled TABLOCK hint for {table}")
        elif self.db_type == "oracle":
            try:
                self.cursor.execute(f"SELECT index_name FROM user_indexes WHERE table_name = UPPER('{table}') AND index_type = 'NORMAL'")
                indexes = self.cursor.fetchall()
                if indexes:
                    self._save_dropped_indexes(table, [idx[0] for idx in indexes])
                    for (idx_name,) in indexes:
                        self.cursor.execute(f"ALTER INDEX {idx_name} UNUSABLE")
                    # Session must skip unusable indexes to allow inserts
                    self.cursor.execute("ALTER SESSION SET SKIP_UNUSABLE_INDEXES = TRUE")
                    logger.info(f"Marked indexes UNUSABLE for {table}")
            except Exception as e:
                logger.warning(f"Failed to mark indexes unusable for {table}: {e}")

    def enable_indexes_for_table(self, table: str):
        if self.db_type in ["postgres", "postgresql"]:
            defs = self._get_dropped_indexes(table)
            if defs:
                for ddl in defs:
                    try:
                        self.cursor.execute(ddl)
                    except Exception as e:
                        logger.warning(f"Failed to recreate index {ddl}: {e}")
                self._clear_dropped_indexes(table)
                logger.info(f"Re-enabled indexes for {table}")
        elif self.db_type == "mysql":
            try:
                self.cursor.execute(f"ALTER TABLE {table} ENABLE KEYS")
                logger.info(f"Re-enabled keys for {table}")
            except Exception:
                pass
        elif self.db_type == "oracle":
            indexes = self._get_dropped_indexes(table)
            if indexes:
                for idx_name in indexes:
                    try:
                        self.cursor.execute(f"ALTER INDEX {idx_name} REBUILD")
                    except Exception as e:
                        logger.warning(f"Failed to rebuild index {idx_name}: {e}")
                self._clear_dropped_indexes(table)
                logger.info(f"Rebuilt indexes for {table}")

    def commit(self) -> None:
        self.conn.commit()

    def rollback(self) -> None:
        self.conn.rollback()
        # Explicitly re-enable constraints on rollback for MySQL and MSSQL
        if self.db_type == "mysql":
            try:
                self.cursor.execute("SET FOREIGN_KEY_CHECKS=1")
            except Exception:
                pass
        elif self.db_type == "mssql":
            for table in self.group_tables:
                try:
                    self.cursor.execute(f"ALTER TABLE {table} CHECK CONSTRAINT ALL")
                except Exception:
                    pass

    def close(self) -> None:
        self.cursor.close()

    def bulk_insert_chunk(self, table_name: str, rows: list[dict], chunk_offset: int = 0) -> int:
        """Insert a chunk of rows into the target table.

        Args:
            table_name: Target table to insert into.
            rows: List of row dicts to insert.
            chunk_offset: Zero-based index of this chunk in the stream,
                          used for structured error reporting.

        Returns:
            Number of rows successfully inserted.

        Raises:
            MigrationChunkError: If the insertion fails, after rolling back
                                 partial writes and persisting FAILED status.
        """
        if not rows:
            return 0

        from backend.execution.exceptions import MigrationChunkError

        columns = list(rows[0].keys())
        cols_str = ", ".join(columns)

        import json
        for row in rows:
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    row[k] = json.dumps(v)
                elif isinstance(v, (bytearray, memoryview)):
                    row[k] = bytes(v)

        try:
            if self.db_type in ["postgres", "postgresql"]:
                import io

                buffer = io.StringIO()
                for row in rows:
                    row_vals = []
                    for col in columns:
                        val = row[col]
                        if val is None:
                            row_vals.append("\\N")
                        elif isinstance(val, bool):
                            row_vals.append("t" if val else "f")
                        elif isinstance(val, bytes):
                            row_vals.append("\\x" + val.hex())
                        else:
                            s_val = str(val).replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")
                            row_vals.append(s_val)
                    buffer.write("\t".join(row_vals) + "\n")

                buffer.seek(0)
                logger.info(f"Using COPY for {table_name} — {len(rows)} rows")

                try:
                    if hasattr(self.connection, "set_client_encoding"):
                        try:
                            self.connection.set_client_encoding("UTF8")
                        except Exception:
                            pass
                    self.cursor.copy_from(
                        buffer,
                        table_name,
                        columns=columns,
                        null="\\N",
                    )
                    return len(rows)
                except Exception as copy_err:
                    logger.warning(f"COPY failed for {table_name}: {copy_err}. Falling back to executemany.")
                    placeholders = ", ".join(["%s"] * len(columns))
                    sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                    data = [tuple(row[col] for col in columns) for row in rows]
                    self.cursor.executemany(sql, data)
                    return len(rows)

            elif self.db_type == "mysql":
                placeholders = ", ".join(["%s"] * len(columns))
                sql = f"INSERT IGNORE INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                data = [tuple(row[col] for col in columns) for row in rows]
                self.cursor.executemany(sql, data)
                return self.cursor.rowcount if self.cursor.rowcount > 0 else len(rows)

            elif self.db_type == "mssql":
                import decimal as _decimal

                cols_mssql = ", ".join(f"[{col}]" for col in columns)
                placeholders = ", ".join(["?"] * len(columns))
                use_tablock = (
                    " WITH (TABLOCK)" if getattr(self, "_use_tablock_cache", {}).get(table_name) else ""
                )
                sql = f"INSERT INTO {table_name}{use_tablock} ({cols_mssql}) VALUES ({placeholders})"

                # Coerce Python values into types the MSSQL ODBC driver can bind.
                # Without this, pyodbc raises 22018 "Invalid character value for
                # cast specification" for bool → BIT, timedelta → TIME, etc.
                import datetime as _dt
                import uuid as _uuid

                def _sanitize(val):
                    if val is None:
                        return None
                    if isinstance(val, _uuid.UUID):
                        return str(val)
                    if isinstance(val, _decimal.Decimal):
                        return float(val)
                    if val == "":
                        return None
                    # Python bool → MSSQL BIT expects int 0/1
                    if isinstance(val, bool):
                        return 1 if val else 0
                    # String booleans (e.g. from MySQL TINYINT(1) read as 'true'/'false')
                    if isinstance(val, str) and val.lower() in ("true", "false"):
                        return 1 if val.lower() == "true" else 0
                    # MySQL TIME columns return timedelta; MSSQL TIME needs 'HH:MM:SS'
                    if isinstance(val, _dt.timedelta):
                        total = int(val.total_seconds())
                        h, rem = divmod(abs(total), 3600)
                        m, s = divmod(rem, 60)
                        return f"{'-' if total < 0 else ''}{h:02}:{m:02}:{s:02}"
                    # bytes pass through directly for VARBINARY
                    if isinstance(val, bytes):
                        return val
                    # Fallback for other objects like IPv4Address etc.
                    if not isinstance(val, (int, float, str, bytes, _dt.datetime, _dt.date, _dt.time)):
                        return str(val)
                    return val

                data = [tuple(_sanitize(row[col]) for col in columns) for row in rows]
                try:
                    self.cursor.fast_executemany = True
                except Exception:
                    pass
                self.cursor.executemany(sql, data)
                return len(rows)
            elif self.db_type == "oracle":
                placeholders = ", ".join([f":{i+1}" for i in range(len(columns))])
                sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
                
                import datetime as _dt
                import decimal as _decimal
                import uuid as _uuid
                
                def _sanitize_oracle(val):
                    if val is None:
                        return None
                    if isinstance(val, bool):
                        return 1 if val else 0
                    if isinstance(val, _uuid.UUID):
                        return str(val)
                    if isinstance(val, _decimal.Decimal):
                        return float(val)
                    if isinstance(val, _dt.timedelta):
                        total = int(val.total_seconds())
                        h, rem = divmod(abs(total), 3600)
                        m, s = divmod(rem, 60)
                        return f"{'-' if total < 0 else ''}{h:02}:{m:02}:{s:02}"
                    if not isinstance(val, (int, float, str, bytes, _dt.datetime, _dt.date, _dt.time)):
                        return str(val)
                    return val
                
                data = [tuple(_sanitize_oracle(row[col]) for col in columns) for row in rows]
                self.cursor.executemany(sql, data)
                return len(rows)

            return 0
        except Exception as e:
            # ── Step A: Rollback partial writes immediately ────────────────
            try:
                self.conn.rollback()
            except Exception as rb_err:
                logger.warning(
                    "Rollback after chunk failure also failed",
                    table=table_name,
                    chunk_offset=chunk_offset,
                    rollback_error=str(rb_err),
                )

            # ── Step B: Structured logging ────────────────────────────────
            safe_error = str(e).encode('ascii', 'replace').decode('ascii')
            logger.error(
                "Chunk insertion failed",
                table=table_name,
                chunk_offset=chunk_offset,
                rows_in_chunk=len(rows),
                db_type=self.db_type,
                error=safe_error,
                job_id=self.job_id,
                exc_info=True,
            )

            # ── Step C: Persist FAILED status to metadata DB ──────────────
            if self.job_id:
                try:
                    import json
                    from backend.database import get_db
                    with get_db() as (conn, cursor):
                        cursor.execute(
                            "SELECT full_payload FROM migration_jobs WHERE id = ?",
                            (self.job_id,),
                        )
                        row = cursor.fetchone()
                        if row and row[0]:
                            payload = json.loads(row[0])
                            # Record exactly which table/chunk failed
                            payload["failed_chunk"] = {
                                "table": table_name,
                                "chunk_offset": chunk_offset,
                                "rows_in_chunk": len(rows),
                                "error": str(e),
                            }
                            payload["status"] = "failed"
                            cursor.execute(
                                "UPDATE migration_jobs SET status = ?, full_payload = ? WHERE id = ?",
                                ("FAILED", json.dumps(payload), self.job_id),
                            )
                        else:
                            cursor.execute(
                                "UPDATE migration_jobs SET status = ? WHERE id = ?",
                                ("FAILED", self.job_id),
                            )
                except Exception as db_err:
                    logger.warning(
                        "Failed to persist chunk failure status to metadata DB",
                        job_id=self.job_id,
                        error=str(db_err),
                    )

            # ── Step D: Raise typed exception to halt the stream ──────────
            raise MigrationChunkError(
                table_name=table_name,
                chunk_offset=chunk_offset,
                rows_in_chunk=len(rows),
                original_error=e,
            ) from e

