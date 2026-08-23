"""
Discovery Service for Universal Migration Engine.
Connects and discovers schema strictly via system catalogs.
"""

from typing import Any

import mysql.connector
import oracledb
import psycopg2
import pyodbc


class DiscoveryService:
    def _connect_mysql(self, host: str, port: int, username: str, password: str, database: str = None) -> object:
        hosts = [host]
        if str(host).strip().lower() in ("localhost", "127.0.0.1", "::1"):
            hosts = [host, "::1", "127.0.0.1", "localhost"]
            seen = set()
            hosts = [h for h in hosts if not (h in seen or seen.add(h))]
        
        last_err = None
        for h in hosts:
            try:
                kwargs = {"host": h, "port": port, "user": username, "password": password}
                if database:
                    kwargs["database"] = database
                return mysql.connector.connect(**kwargs)
            except mysql.connector.Error as db_err:
                if getattr(db_err, 'errno', None) == 1049 and database is not None:
                    try:
                        return mysql.connector.connect(host=h, port=port, user=username, password=password)
                    except Exception as fallback_err:
                        last_err = fallback_err
                else:
                    last_err = db_err
            except Exception as e:
                last_err = e
        raise last_err

    def _make_connection(self, host: str, port: int, username: str, password: str, db_type: str, database: str = None) -> object:
        if db_type.lower() == "mssql":
            h = "127.0.0.1" if str(host).strip().lower() in ("localhost", "::1") else host
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={h},{port};UID={username};PWD={password};TrustServerCertificate=yes;"
            return pyodbc.connect(conn_str)
        elif db_type.lower() == "mysql":
            return self._connect_mysql(host, port, username, password, database)
        elif db_type.lower() in ["postgres", "postgresql"]:
            h = "127.0.0.1" if str(host).strip().lower() in ("localhost", "::1") else host
            return self._connect_postgres(h, port, username, password, database)
        elif db_type.lower() == "oracle":
            h = "127.0.0.1" if str(host).strip().lower() in ("localhost", "::1") else host
            return oracledb.connect(
                user=username, password=password, dsn=f"{h}:{port}/{database}"
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def connect_and_discover(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        db_type: str,
        database: str = None,
        table_filter: list = None,
    ) -> dict[str, Any]:
        """
        Connects to the database and discovers the schema using system catalogs.
        Raises ConnectionError if the connection fails.
        """
        db_key = db_type.lower()
        try:
            if db_key == "mssql":
                h = "127.0.0.1" if str(host).strip().lower() in ("localhost", "::1") else host
                return self._discover_mssql(h, port, username, password, database, table_filter)
            elif db_key == "mysql":
                return self._discover_mysql(host, port, username, password, database, table_filter)
            elif db_key in ["postgres", "postgresql"]:
                h = "127.0.0.1" if str(host).strip().lower() in ("localhost", "::1") else host
                return self._discover_postgres(h, port, username, password, database, table_filter)
            elif db_key == "oracle":
                h = "127.0.0.1" if str(host).strip().lower() in ("localhost", "::1") else host
                return self._discover_oracle(h, port, username, password, database, table_filter)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
        except ValueError:
            raise
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {db_type} at {host}:{port} — {e}") from e

    def list_tables_only(
        self, host: str, port: int, username: str, password: str, db_type: str, database: str = None
    ) -> dict[str, Any]:
        """
        Lightweight metadata extraction for table picker UI.
        Only returns table names, row counts, estimated size, and FK relationships.
        """
        db_key = db_type.lower()
        try:
            if db_key == "mssql":
                h = "127.0.0.1" if str(host).strip().lower() in ("localhost", "::1") else host
                return self._list_tables_mssql(h, port, username, password, database)
            elif db_key == "mysql":
                return self._list_tables_mysql(host, port, username, password, database)
            elif db_key in ["postgres", "postgresql"]:
                h = "127.0.0.1" if str(host).strip().lower() in ("localhost", "::1") else host
                return self._list_tables_postgres(h, port, username, password, database)
            elif db_key == "oracle":
                return self._list_tables_oracle(host, port, username, password, database)
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
        except ValueError:
            raise
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {db_type} at {host}:{port} — {e}") from e

    def _list_tables_mssql(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> dict[str, Any]:
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};UID={username};PWD={password};TrustServerCertificate=yes;"
        if database:
            conn_str += f";DATABASE={database}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Get tables and approximate row counts
        cursor.execute("""
            SELECT t.name, SUM(p.rows)
            FROM sys.tables t
            JOIN sys.partitions p ON t.object_id = p.object_id
            WHERE p.index_id IN (0, 1)
            GROUP BY t.name
        """)
        tables = {}
        for row in cursor.fetchall():
            tables[row[0]] = {
                "name": row[0],
                "row_count": row[1] or 0,
                "estimated_size_mb": 0.0,  # approximation can be added if needed
                "has_foreign_keys_to": [],
                "referenced_by": [],
            }

        # Get all foreign keys
        cursor.execute("""
            SELECT OBJECT_NAME(fk.parent_object_id) AS from_table,
                   OBJECT_NAME(fk.referenced_object_id) AS to_table
            FROM sys.foreign_keys fk
        """)
        for row in cursor.fetchall():
            from_t = row[0]
            to_t = row[1]
            if from_t in tables and to_t in tables:
                if to_t not in tables[from_t]["has_foreign_keys_to"]:
                    tables[from_t]["has_foreign_keys_to"].append(to_t)
                if from_t not in tables[to_t]["referenced_by"]:
                    tables[to_t]["referenced_by"].append(from_t)

        conn.close()
        return {"tables": list(tables.values())}

    def _list_tables_mysql(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> dict[str, Any]:
        conn = self._connect_mysql(host, port, username, password, database)
        cursor = conn.cursor(dictionary=True)

        cursor.execute(f"""
            SELECT TABLE_NAME, TABLE_ROWS, (DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024 AS size_mb
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = '{database}' AND TABLE_TYPE = 'BASE TABLE'
        """)
        tables = {}
        for row in cursor.fetchall():
            tables[row["TABLE_NAME"]] = {
                "name": row["TABLE_NAME"],
                "row_count": row["TABLE_ROWS"] or 0,
                "estimated_size_mb": float(row["size_mb"] or 0.0),
                "has_foreign_keys_to": [],
                "referenced_by": [],
            }

        cursor.execute(f"""
            SELECT TABLE_NAME, REFERENCED_TABLE_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{database}' AND REFERENCED_TABLE_NAME IS NOT NULL
        """)
        for row in cursor.fetchall():
            from_t = row["TABLE_NAME"]
            to_t = row["REFERENCED_TABLE_NAME"]
            if from_t in tables and to_t in tables:
                if to_t not in tables[from_t]["has_foreign_keys_to"]:
                    tables[from_t]["has_foreign_keys_to"].append(to_t)
                if from_t not in tables[to_t]["referenced_by"]:
                    tables[to_t]["referenced_by"].append(from_t)

        conn.close()
        return {"tables": list(tables.values())}

    def _connect_postgres(self, host: str, port: int, username: str, password: str, database: str = None) -> object:
        host = "127.0.0.1" if str(host).strip().lower() in ("localhost", "::1") else host
        target_db = database or "postgres"
        try:
            return psycopg2.connect(host=host, port=port, user=username, password=password, dbname=target_db)
        except psycopg2.OperationalError as err:
            if target_db != target_db.lower():
                try:
                    return psycopg2.connect(host=host, port=port, user=username, password=password, dbname=target_db.lower())
                except psycopg2.OperationalError:
                    pass
            try:
                return psycopg2.connect(host=host, port=port, user=username, password=password, dbname="postgres")
            except psycopg2.OperationalError:
                raise err

    def _list_tables_postgres(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> dict[str, Any]:
        conn = self._connect_postgres(host, port, username, password, database)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT relname, reltuples::bigint, pg_total_relation_size(c.oid) / 1048576.0 AS size_mb
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
        """)
        tables = {}
        for row in cursor.fetchall():
            tables[row[0]] = {
                "name": row[0],
                "row_count": max(0, int(row[1] or 0)),
                "estimated_size_mb": float(row[2] or 0.0),
                "has_foreign_keys_to": [],
                "referenced_by": [],
            }

        cursor.execute("""
            SELECT tc.table_name AS from_table, ccu.table_name AS to_table
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
        """)
        for row in cursor.fetchall():
            from_t = row[0]
            to_t = row[1]
            if from_t in tables and to_t in tables:
                if to_t not in tables[from_t]["has_foreign_keys_to"]:
                    tables[from_t]["has_foreign_keys_to"].append(to_t)
                if from_t not in tables[to_t]["referenced_by"]:
                    tables[to_t]["referenced_by"].append(from_t)

        conn.close()
        return {"tables": list(tables.values())}

    def _list_tables_oracle(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> dict[str, Any]:
        conn = oracledb.connect(user=username, password=password, dsn=f"{host}:{port}/{database}")
        cursor = conn.cursor()
        schema = username.upper()

        cursor.execute("""
            SELECT table_name, num_rows 
            FROM ALL_TABLES 
            WHERE owner = :schema
            AND table_name NOT LIKE 'BIN$%'
        """, schema=schema)
        
        tables = {}
        for row in cursor.fetchall():
            tables[row[0]] = {
                "name": row[0],
                "row_count": row[1] or 0,
                "estimated_size_mb": 0.0,
                "has_foreign_keys_to": [],
                "referenced_by": [],
            }

        cursor.execute("""
            SELECT cons.table_name AS from_table, r_cons.table_name AS to_table
            FROM ALL_CONSTRAINTS cons
            JOIN ALL_CONSTRAINTS r_cons ON cons.r_constraint_name = r_cons.constraint_name
            WHERE cons.constraint_type = 'R'
            AND cons.owner = :schema
        """, schema=schema)
        
        for row in cursor.fetchall():
            from_t = row[0]
            to_t = row[1]
            if from_t in tables and to_t in tables:
                if to_t not in tables[from_t]["has_foreign_keys_to"]:
                    tables[from_t]["has_foreign_keys_to"].append(to_t)
                if from_t not in tables[to_t]["referenced_by"]:
                    tables[to_t]["referenced_by"].append(from_t)

        conn.close()
        return {"tables": list(tables.values())}

    def _discover_mssql(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        table_filter: list = None,
    ) -> dict[str, Any]:
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};UID={username};PWD={password};TrustServerCertificate=yes;"
        if database:
            conn_str += f";DATABASE={database}"

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        result = {"databases": [], "schemas": [], "tables": [], "row_counts": {}}

        # Get databases
        cursor.execute("SELECT name FROM sys.databases")
        result["databases"] = [row[0] for row in cursor.fetchall()]

        if not database:
            return result

        # Get schemas
        cursor.execute("SELECT name FROM sys.schemas")
        result["schemas"] = [row[0] for row in cursor.fetchall()]

        # Get tables
        cursor.execute("SELECT name FROM sys.tables")
        tables = [row[0] for row in cursor.fetchall()]

        if table_filter:
            tables = [t for t in tables if t in table_filter]

        for table in tables:
            table_info = {
                "name": table,
                "columns": [],
                "primary_keys": [],
                "foreign_keys": [],
                "indexes": [],
                "check_constraints": [],
                "row_count": 0,
            }

            # Row count
            cursor.execute(
                f"SELECT SUM(row_count) FROM sys.dm_db_partition_stats WHERE object_id=OBJECT_ID('{table}') AND (index_id=0 or index_id=1)"
            )
            count_row = cursor.fetchone()
            table_info["row_count"] = count_row[0] if count_row and count_row[0] else 0

            # Columns
            cursor.execute(f"""
                SELECT c.name, t.name AS type, c.is_nullable, 
                       OBJECT_DEFINITION(c.default_object_id) AS default_val
                FROM sys.columns c
                JOIN sys.types t ON c.user_type_id = t.user_type_id
                WHERE c.object_id = OBJECT_ID('{table}')
            """)
            for row in cursor.fetchall():
                table_info["columns"].append(
                    {"name": row[0], "type": row[1], "nullable": bool(row[2]), "default": row[3]}
                )

            # Primary keys
            cursor.execute(f"""
                SELECT c.name 
                FROM sys.indexes i
                JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
                JOIN sys.columns c ON ic.object_id = c.object_id AND c.column_id = ic.column_id
                WHERE i.is_primary_key = 1 AND i.object_id = OBJECT_ID('{table}')
            """)
            table_info["primary_keys"] = [row[0] for row in cursor.fetchall()]

            # Foreign keys
            cursor.execute(f"""
                SELECT c.name AS column_name, 
                       OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
                       rc.name AS referenced_column,
                       fk.delete_referential_action_desc AS on_delete,
                       fk.update_referential_action_desc AS on_update
                FROM sys.foreign_keys fk
                JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
                JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
                JOIN sys.columns rc ON fkc.referenced_object_id = rc.object_id AND fkc.referenced_column_id = rc.column_id
                WHERE fk.parent_object_id = OBJECT_ID('{table}')
            """)
            for row in cursor.fetchall():
                table_info["foreign_keys"].append(
                    {
                        "column": row[0],
                        "references_table": row[1],
                        "references_column": row[2],
                        "on_delete": row[3],
                        "on_update": row[4],
                    }
                )

            # Indexes
            cursor.execute(f"""
                SELECT i.name, i.is_unique, i.type_desc, c.name AS column_name
                FROM sys.indexes i
                JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
                JOIN sys.columns c ON ic.object_id = c.object_id AND c.column_id = ic.column_id
                WHERE i.object_id = OBJECT_ID('{table}') AND i.type > 0
            """)
            indexes_dict = {}
            for row in cursor.fetchall():
                idx_name, is_unique, type_desc, col_name = row
                if idx_name not in indexes_dict:
                    indexes_dict[idx_name] = {
                        "name": idx_name,
                        "unique": bool(is_unique),
                        "type": type_desc,
                        "columns": [],
                    }
                indexes_dict[idx_name]["columns"].append(col_name)
            table_info["indexes"] = list(indexes_dict.values())

            # Check constraints
            cursor.execute(f"""
                SELECT definition 
                FROM sys.check_constraints 
                WHERE parent_object_id = OBJECT_ID('{table}')
            """)
            table_info["check_constraints"] = [row[0] for row in cursor.fetchall()]

            result["tables"].append(table_info)

        conn.close()
        return result

    def _discover_mysql(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        table_filter: list = None,
    ) -> dict[str, Any]:
        try:
            conn = self._connect_mysql(host, port, username, password, database)
        except mysql.connector.Error as err:
            if getattr(err, 'errno', None) == 1049:
                conn = self._connect_mysql(host, port, username, password, None)
            else:
                raise
        cursor = conn.cursor(dictionary=True)

        result = {"databases": [], "schemas": [], "tables": [], "row_counts": {}}

        cursor.execute("SHOW DATABASES")
        result["databases"] = [row["Database"] for row in cursor.fetchall()]

        if not database:
            return result

        cursor.execute(
            f"SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{database}' AND TABLE_TYPE = 'BASE TABLE'"
        )
        tables = [row["TABLE_NAME"] for row in cursor.fetchall()]

        if table_filter:
            tables = [t for t in tables if t in table_filter]

        for table in tables:
            table_info = {
                "name": table,
                "columns": [],
                "primary_keys": [],
                "foreign_keys": [],
                "indexes": [],
                "check_constraints": [],
                "row_count": 0,
            }

            cursor.execute(
                f"SELECT TABLE_ROWS FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}'"
            )
            row = cursor.fetchone()
            table_info["row_count"] = row["TABLE_ROWS"] if row and row["TABLE_ROWS"] else 0

            cursor.execute(
                f"SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}'"
            )
            for row in cursor.fetchall():
                table_info["columns"].append(
                    {
                        "name": row["COLUMN_NAME"],
                        "type": row["COLUMN_TYPE"],
                        "nullable": row["IS_NULLABLE"] == "YES",
                        "default": row["COLUMN_DEFAULT"],
                    }
                )

            cursor.execute(f"SHOW KEYS FROM {table} WHERE Key_name = 'PRIMARY'")
            table_info["primary_keys"] = [row["Column_name"] for row in cursor.fetchall()]

            cursor.execute(f"""
                SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}' AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            for row in cursor.fetchall():
                table_info["foreign_keys"].append(
                    {
                        "column": row["COLUMN_NAME"],
                        "references_table": row["REFERENCED_TABLE_NAME"],
                        "references_column": row["REFERENCED_COLUMN_NAME"],
                        "on_delete": "UNKNOWN",  # Requires more complex parsing or SHOW CREATE TABLE
                        "on_update": "UNKNOWN",
                    }
                )

            cursor.execute(f"SHOW INDEX FROM {table} WHERE Key_name != 'PRIMARY'")
            indexes_dict = {}
            for row in cursor.fetchall():
                idx_name = row["Key_name"]
                if idx_name not in indexes_dict:
                    indexes_dict[idx_name] = {
                        "name": idx_name,
                        "unique": row["Non_unique"] == 0,
                        "type": row["Index_type"],
                        "columns": [],
                    }
                indexes_dict[idx_name]["columns"].append(row["Column_name"])
            table_info["indexes"] = list(indexes_dict.values())

            # Check constraints (MySQL 8.0.16+)
            cursor.execute(
                f"SELECT CHECK_CLAUSE FROM information_schema.CHECK_CONSTRAINTS WHERE CONSTRAINT_SCHEMA = '{database}'"
            )
            try:
                table_info["check_constraints"] = [row["CHECK_CLAUSE"] for row in cursor.fetchall()]
            except Exception:
                pass  # Older MySQL version or permission issue

            result["tables"].append(table_info)

        conn.close()
        return result

    def _discover_postgres(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        table_filter: list = None,
    ) -> dict[str, Any]:
        conn = self._connect_postgres(host, port, username, password, database)
        cursor = conn.cursor()

        result = {"databases": [], "schemas": [], "tables": [], "row_counts": {}}

        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false")
        result["databases"] = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT schema_name FROM information_schema.schemata")
        result["schemas"] = [row[0] for row in cursor.fetchall()]

        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        if table_filter:
            tables = [t for t in tables if t in table_filter]

        for table in tables:
            table_info = {
                "name": table,
                "columns": [],
                "primary_keys": [],
                "foreign_keys": [],
                "indexes": [],
                "check_constraints": [],
                "row_count": 0,
            }

            # Row count (approximate for speed, or exact if needed. Instructions imply accurate, using count(*))
            # However, exact count(*) can be slow. Using exact here per standard practice in migrations unless large.
            cursor.execute(f"SELECT reltuples::bigint FROM pg_class WHERE relname = '{table}'")
            row = cursor.fetchone()
            table_info["row_count"] = row[0] if row else 0

            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND table_schema = 'public'
            """)
            for row in cursor.fetchall():
                table_info["columns"].append(
                    {"name": row[0], "type": row[1], "nullable": row[2] == "YES", "default": row[3]}
                )

            cursor.execute(f"""
                SELECT a.attname
                FROM   pg_index i
                JOIN   pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE  i.indrelid = '{table}'::regclass AND i.indisprimary
            """)
            table_info["primary_keys"] = [row[0] for row in cursor.fetchall()]

            cursor.execute(f"""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule,
                    rc.update_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
                JOIN information_schema.referential_constraints AS rc
                  ON rc.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = '{table}'
            """)
            for row in cursor.fetchall():
                table_info["foreign_keys"].append(
                    {
                        "column": row[0],
                        "references_table": row[1],
                        "references_column": row[2],
                        "on_delete": row[3],
                        "on_update": row[4],
                    }
                )

            cursor.execute(f"""
                SELECT
                    i.relname AS index_name,
                    ix.indisunique AS is_unique,
                    am.amname AS index_type,
                    a.attname AS column_name
                FROM pg_class t
                JOIN pg_index ix ON t.oid = ix.indrelid
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                JOIN pg_am am ON i.relam = am.oid
                WHERE t.relkind = 'r' AND t.relname = '{table}' AND ix.indisprimary = false
            """)
            indexes_dict = {}
            for row in cursor.fetchall():
                idx_name, is_unique, idx_type, col_name = row
                if idx_name not in indexes_dict:
                    indexes_dict[idx_name] = {
                        "name": idx_name,
                        "unique": is_unique,
                        "type": idx_type,
                        "columns": [],
                    }
                indexes_dict[idx_name]["columns"].append(col_name)
            table_info["indexes"] = list(indexes_dict.values())

            cursor.execute(f"""
                SELECT pg_get_constraintdef(c.oid)
                FROM pg_constraint c
                JOIN pg_namespace n ON n.oid = c.connamespace
                WHERE contype = 'c' AND conrelid = '{table}'::regclass
            """)
            table_info["check_constraints"] = [row[0] for row in cursor.fetchall()]

            result["tables"].append(table_info)

        conn.close()
        return result

    def _discover_oracle(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        database: str,
        table_filter: list = None,
    ) -> dict[str, Any]:
        conn = oracledb.connect(user=username, password=password, dsn=f"{host}:{port}/{database}")
        cursor = conn.cursor()
        schema = username.upper()

        result = {
            "databases": [database] if database else [],
            "schemas": [schema],
            "tables": [],
            "row_counts": {},
        }

        cursor.execute("""
            SELECT table_name, num_rows 
            FROM ALL_TABLES 
            WHERE owner = :schema
            AND table_name NOT LIKE 'BIN$%'
        """, schema=schema)
        
        tables_data = cursor.fetchall()
        
        if table_filter:
            tables_data = [t for t in tables_data if t[0] in table_filter]

        for table_row in tables_data:
            table_name = table_row[0]
            row_count = table_row[1] or 0
            
            table_info = {
                "name": table_name,
                "schema": schema,
                "columns": [],
                "primary_keys": [],
                "foreign_keys": [],
                "indexes": [],
            }
            
            result["row_counts"][f"{schema}.{table_name}"] = row_count

            cursor.execute("""
                SELECT column_name, data_type, 
                       data_length, data_precision, 
                       data_scale, nullable, 
                       data_default
                FROM ALL_TAB_COLUMNS
                WHERE owner = :schema
                AND table_name = :table_name
                ORDER BY column_id
            """, schema=schema, table_name=table_name)
            
            for col in cursor.fetchall():
                table_info["columns"].append({
                    "name": col[0],
                    "type": col[1],
                    "length": col[2],
                    "precision": col[3],
                    "scale": col[4],
                    "is_nullable": col[5] == 'Y',
                    "default": col[6].strip() if col[6] and isinstance(col[6], str) else None,
                    "is_auto_increment": False
                })
                
            cursor.execute("""
                SELECT cols.column_name
                FROM ALL_CONSTRAINTS cons
                JOIN ALL_CONS_COLUMNS cols 
                  ON cons.constraint_name = cols.constraint_name
                  AND cons.owner = cols.owner
                WHERE cons.constraint_type = 'P'
                AND cons.owner = :schema
                AND cons.table_name = :table_name
            """, schema=schema, table_name=table_name)
            
            table_info["primary_keys"] = [row[0] for row in cursor.fetchall()]

            cursor.execute("""
                SELECT cols.column_name,
                       r_cons.table_name AS ref_table,
                       r_cols.column_name AS ref_column
                FROM ALL_CONSTRAINTS cons
                JOIN ALL_CONS_COLUMNS cols 
                  ON cons.constraint_name = cols.constraint_name
                JOIN ALL_CONSTRAINTS r_cons 
                  ON cons.r_constraint_name = r_cons.constraint_name
                JOIN ALL_CONS_COLUMNS r_cols 
                  ON r_cons.constraint_name = r_cols.constraint_name
                  AND cols.position = r_cols.position
                WHERE cons.constraint_type = 'R'
                AND cons.owner = :schema
                AND cons.table_name = :table_name
            """, schema=schema, table_name=table_name)
            
            for fk in cursor.fetchall():
                table_info["foreign_keys"].append({
                    "column": fk[0],
                    "referenced_table": fk[1],
                    "referenced_column": fk[2],
                })
                
            result["tables"].append(table_info)

        conn.close()
        return result

    def _estimate_complexity(self, definition: str, object_type: str) -> str:
        if not definition:
            return "low"
        def_lower = definition.lower()
        # High complexity indicators
        high_indicators = [
            "cursor",
            "declare cursor",
            "open ",
            "fetch ",
            "exception",
            "handler",
            "sqlexception",
            "pragma exception_init",
            "execute immediate",
            "sp_executesql",
            "exec(",
            "execute(",
        ]
        if any(ind in def_lower for ind in high_indicators):
            return "high"

        if object_type == "view":
            return "low"

        # Count semicolons or check for BEGIN/END
        if object_type == "trigger":
            # Check if it has multiple statements
            semicolon_count = def_lower.count(";")
            if semicolon_count <= 2:
                return "low"
            return "medium"

        # Default for procedures/functions is medium
        return "medium"

    def _resolve_object_dependencies(
        self,
        definition: str,
        all_table_names: list[str],
        all_object_names: list[str],
        current_name: str,
    ) -> tuple[list[str], list[str]]:
        import re

        if not definition:
            return [], []

        # Strip comments
        clean_def = re.sub(r"--.*", "", definition)
        clean_def = re.sub(r"/\*.*?\*/", "", clean_def, flags=re.DOTALL)
        clean_def_lower = clean_def.lower()

        depends_on_tables = []
        depends_on_objects = []

        for table in all_table_names:
            # Word boundary search
            if re.search(rf"\b{re.escape(table.lower())}\b", clean_def_lower):
                depends_on_tables.append(table)

        for obj in all_object_names:
            if obj.lower() == current_name.lower():
                continue
            if re.search(rf"\b{re.escape(obj.lower())}\b", clean_def_lower):
                depends_on_objects.append(obj)

        return depends_on_tables, depends_on_objects

    def list_migratable_objects(
        self, host: str, port: int, username: str, password: str, db_type: str, database: str = None
    ) -> dict[str, list[dict[str, Any]]]:
        # Connect and list tables first to have a list of table names for dependency parsing
        tables_res = self.list_tables_only(host, port, username, password, db_type, database)
        table_names = [t["name"] for t in tables_res.get("tables", [])]

        if db_type.lower() == "mssql":
            raw_objects = self._list_objects_mssql(host, port, username, password, database)
        elif db_type.lower() == "mysql":
            raw_objects = self._list_objects_mysql(host, port, username, password, database)
        elif db_type.lower() in ["postgres", "postgresql"]:
            raw_objects = self._list_objects_postgres(host, port, username, password, database)
        elif db_type.lower() == "oracle":
            raw_objects = self._list_objects_oracle(host, port, username, password, database)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        print(f"Discovery query for {db_type} views returned {len(raw_objects.get('views', []))} results", flush=True)
        print(f"Discovery query for {db_type} procedures returned {len(raw_objects.get('procedures', []))} results", flush=True)
        print(f"Discovery query for {db_type} triggers returned {len(raw_objects.get('triggers', []))} results", flush=True)

        # Post-process to parse dependencies and estimate complexity
        all_object_names = []
        for category in ["views", "procedures", "triggers"]:
            for obj in raw_objects.get(category, []):
                all_object_names.append(obj["name"])

        processed = {"views": [], "procedures": [], "triggers": []}

        for category in ["views", "procedures", "triggers"]:
            for obj in raw_objects.get(category, []):
                definition = obj.get("source_definition", "")
                name = obj.get("name", "")

                depends_tbls, depends_objs = self._resolve_object_dependencies(
                    definition, table_names, all_object_names, name
                )
                complexity = self._estimate_complexity(definition, obj["object_type"])

                processed[category].append(
                    {
                        "object_type": obj["object_type"],
                        "name": name,
                        "schema_name": obj.get("schema_name"),
                        "source_definition": definition,
                        "depends_on_tables": depends_tbls,
                        "depends_on_objects": depends_objs,
                        "complexity_estimate": complexity,
                    }
                )

        return processed

    def _list_objects_mssql(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> dict[str, list[dict[str, Any]]]:
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port};UID={username};PWD={password};TrustServerCertificate=yes;"
        if database:
            conn_str += f";DATABASE={database}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        result = {"views": [], "procedures": [], "triggers": []}

        # 1. Fetch Views
        cursor.execute("""
            SELECT v.name, SCHEMA_NAME(v.schema_id), sm.definition
            FROM sys.views v
            JOIN sys.sql_modules sm ON v.object_id = sm.object_id
        """)
        for row in cursor.fetchall():
            result["views"].append(
                {
                    "object_type": "view",
                    "name": row[0],
                    "schema_name": row[1],
                    "source_definition": row[2] or "",
                }
            )

        # 2. Fetch Procedures & Functions
        cursor.execute("""
            SELECT p.name, SCHEMA_NAME(p.schema_id), sm.definition
            FROM sys.procedures p
            JOIN sys.sql_modules sm ON p.object_id = sm.object_id
        """)
        for row in cursor.fetchall():
            result["procedures"].append(
                {
                    "object_type": "procedure",
                    "name": row[0],
                    "schema_name": row[1],
                    "source_definition": row[2] or "",
                }
            )

        cursor.execute("""
            SELECT o.name, SCHEMA_NAME(o.schema_id), sm.definition, o.type
            FROM sys.objects o
            JOIN sys.sql_modules sm ON o.object_id = sm.object_id
            WHERE o.type IN ('FN', 'IF', 'TF')
        """)
        for row in cursor.fetchall():
            result["procedures"].append(
                {
                    "object_type": "function",
                    "name": row[0],
                    "schema_name": row[1],
                    "source_definition": row[2] or "",
                }
            )

        # 3. Fetch Triggers (sys.triggers has no schema_id; join sys.objects for it)
        cursor.execute("""
            SELECT t.name, SCHEMA_NAME(o.schema_id), sm.definition
            FROM sys.triggers t
            JOIN sys.objects o ON t.object_id = o.object_id
            JOIN sys.sql_modules sm ON t.object_id = sm.object_id
        """)
        for row in cursor.fetchall():
            result["triggers"].append(
                {
                    "object_type": "trigger",
                    "name": row[0],
                    "schema_name": row[1],
                    "source_definition": row[2] or "",
                }
            )

        conn.close()
        return result

    def _list_objects_mysql(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> dict[str, list[dict[str, Any]]]:
        conn = self._connect_mysql(host, port, username, password, database)
        cursor = conn.cursor(dictionary=True)

        result = {"views": [], "procedures": [], "triggers": []}

        # 1. Fetch Views — use SHOW CREATE VIEW to get the original SQL
        # (information_schema.VIEWS.VIEW_DEFINITION returns MySQL's internally
        # rewritten SQL which strips table aliases and makes JOINs ambiguous)
        cursor.execute(f"""
            SELECT TABLE_NAME
            FROM information_schema.VIEWS
            WHERE TABLE_SCHEMA = '{database}'
        """)
        view_names = [row["TABLE_NAME"] for row in cursor.fetchall()]
        for view_name in view_names:
            definition = ""
            try:
                show_cur = conn.cursor(dictionary=True)
                show_cur.execute(f"SHOW CREATE VIEW `{database}`.`{view_name}`")
                show_row = show_cur.fetchone()
                if show_row:
                    definition = (
                        show_row.get("Create View")
                        or show_row.get("create_view")
                        or ""
                    )
                    if not definition:
                        for k, val in show_row.items():
                            if isinstance(val, str) and "SELECT" in val.upper() and ("CREATE" in val.upper() or "VIEW" in val.upper()):
                                definition = val
                                break
                show_cur.close()
            except Exception:
                definition = ""

            # Fallback: use information_schema if SHOW CREATE VIEW failed
            if not definition:
                try:
                    fallback_cur = conn.cursor(dictionary=True)
                    fallback_cur.execute(f"""
                        SELECT VIEW_DEFINITION
                        FROM information_schema.VIEWS
                        WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{view_name}'
                    """)
                    fb_row = fallback_cur.fetchone()
                    if fb_row:
                        definition = fb_row["VIEW_DEFINITION"] or ""
                    fallback_cur.close()
                except Exception:
                    pass

            result["views"].append(
                {
                    "object_type": "view",
                    "name": view_name,
                    "schema_name": database,
                    "source_definition": definition,
                }
            )

        # 2. Fetch Procedures / Functions
        cursor.execute(f"""
            SELECT ROUTINE_NAME, ROUTINE_TYPE, ROUTINE_DEFINITION, DATA_TYPE
            FROM information_schema.ROUTINES
            WHERE ROUTINE_SCHEMA = '{database}'
        """)
        routines = cursor.fetchall()
        for r in routines:
            name = r["ROUTINE_NAME"]
            rtype = r["ROUTINE_TYPE"]
            definition = ""
            try:
                show_cur = conn.cursor(dictionary=True)
                show_cur.execute(f"SHOW CREATE {rtype} `{database}`.`{name}`")
                show_row = show_cur.fetchone()
                if show_row:
                    definition = (
                        show_row.get(f"Create {rtype.capitalize()}")
                        or show_row.get(f"Create {rtype.upper()}")
                        or show_row.get("Create Procedure")
                        or show_row.get("Create Function")
                        or ""
                    )
                    if not definition:
                        for k, val in show_row.items():
                            if isinstance(val, str) and ("CREATE" in val.upper() or "BEGIN" in val.upper()):
                                definition = val
                                break
                show_cur.close()
            except Exception:
                definition = ""

            if not definition and r.get("ROUTINE_DEFINITION"):
                body = r["ROUTINE_DEFINITION"]
                if rtype.upper() == "FUNCTION":
                    ret = r.get("DATA_TYPE") or "VARCHAR(255)"
                    definition = f"CREATE FUNCTION `{name}`()\nRETURNS {ret}\nDETERMINISTIC\nBEGIN\n{body}\nEND"
                else:
                    definition = f"CREATE PROCEDURE `{name}`()\nBEGIN\n{body}\nEND"

            result["procedures"].append(
                {
                    "object_type": "procedure" if rtype.upper() == "PROCEDURE" else "function",
                    "name": name,
                    "schema_name": database,
                    "source_definition": definition,
                }
            )

        # 3. Fetch Triggers
        cursor.execute(f"""
            SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE, ACTION_TIMING, ACTION_STATEMENT
            FROM information_schema.TRIGGERS
            WHERE TRIGGER_SCHEMA = '{database}'
        """)
        triggers = cursor.fetchall()
        for t in triggers:
            name = t["TRIGGER_NAME"]
            definition = ""
            try:
                show_cur = conn.cursor(dictionary=True)
                show_cur.execute(f"SHOW CREATE TRIGGER `{database}`.`{name}`")
                show_row = show_cur.fetchone()
                if show_row:
                    # In MySQL, SHOW CREATE TRIGGER returns 'SQL Original Statement'
                    definition = (
                        show_row.get("SQL Original Statement")
                        or show_row.get("sql_original_statement")
                        or show_row.get("Create Trigger")
                        or ""
                    )
                    if not definition:
                        for k, val in show_row.items():
                            if isinstance(val, str) and re.search(r'\bCREATE\s+(?:DEFINER\s*=\s*\S+\s+)?TRIGGER\b', val, re.IGNORECASE):
                                definition = val
                                break
                show_cur.close()
            except Exception:
                definition = ""

            if not definition and t.get("ACTION_STATEMENT"):
                timing = t.get("ACTION_TIMING", "AFTER")
                event = t.get("EVENT_MANIPULATION", "INSERT")
                table = t.get("EVENT_OBJECT_TABLE", "")
                stmt = t.get("ACTION_STATEMENT")
                definition = f"CREATE TRIGGER `{name}` {timing} {event} ON `{table}` FOR EACH ROW\n{stmt}"

            result["triggers"].append(
                {
                    "object_type": "trigger",
                    "name": name,
                    "schema_name": database,
                    "source_definition": definition,
                    "trigger_table": t.get("EVENT_OBJECT_TABLE", ""),
                    "trigger_timing": t.get("ACTION_TIMING", "AFTER"),
                    "trigger_event": t.get("EVENT_MANIPULATION", "INSERT"),
                }
            )

        conn.close()
        return result

    def _list_objects_postgres(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> dict[str, list[dict[str, Any]]]:
        conn = self._connect_postgres(host, port, username, password, database)
        cursor = conn.cursor()

        result = {"views": [], "procedures": [], "triggers": []}

        # 1. Fetch Views
        cursor.execute("""
            SELECT viewname, definition
            FROM pg_views
            WHERE schemaname = 'public'
        """)
        for row in cursor.fetchall():
            view_def = (row[1] or "").strip()
            if not view_def.lower().startswith("create"):
                view_def = f"CREATE VIEW {row[0]} AS {view_def}"
            result["views"].append(
                {
                    "object_type": "view",
                    "name": row[0],
                    "schema_name": "public",
                    "source_definition": view_def,
                }
            )

        # 2. Fetch Procedures & Functions
        cursor.execute("""
            SELECT p.proname, p.prokind, pg_get_functiondef(p.oid), t.typname
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            JOIN pg_type t ON p.prorettype = t.oid
            WHERE n.nspname = 'public' AND p.prokind IN ('p', 'f')
        """)
        for row in cursor.fetchall():
            p_name, prokind, func_def, ret_type = row
            is_trigger_func = ret_type == "trigger"

            result["procedures"].append(
                {
                    "object_type": "procedure"
                    if prokind == "p"
                    else ("trigger_function" if is_trigger_func else "function"),
                    "name": p_name,
                    "schema_name": "public",
                    "source_definition": func_def or "",
                }
            )

        # 3. Fetch Triggers
        cursor.execute("""
            SELECT trg.tgname, pg_get_triggerdef(trg.oid), tbl.relname
            FROM pg_trigger trg
            JOIN pg_class tbl ON trg.tgrelid = tbl.oid
            JOIN pg_namespace ns ON tbl.relnamespace = ns.oid
            WHERE ns.nspname = 'public' AND NOT trg.tgisinternal
        """)
        for row in cursor.fetchall():
            result["triggers"].append(
                {
                    "object_type": "trigger",
                    "name": row[0],
                    "schema_name": "public",
                    "source_definition": row[1] or "",
                }
            )

        conn.close()
        return result

    def _list_objects_oracle(
        self, host: str, port: int, username: str, password: str, database: str
    ) -> dict[str, list[dict[str, Any]]]:
        conn = oracledb.connect(user=username, password=password, dsn=f"{host}:{port}/{database}")
        cursor = conn.cursor()
        schema = username.upper()
        
        result = {"views": [], "procedures": [], "triggers": []}
        
        cursor.execute("""
            SELECT view_name, text
            FROM ALL_VIEWS
            WHERE owner = :schema
        """, schema=schema)
        for row in cursor.fetchall():
            text = row[1].read() if hasattr(row[1], 'read') else (row[1] or "")
            if not text.strip().lower().startswith("create"):
                text = f"CREATE VIEW {row[0]} AS {text}"
            result["views"].append({
                "object_type": "view",
                "name": row[0],
                "schema_name": schema,
                "source_definition": text,
            })
            
        cursor.execute("""
            SELECT object_name, object_type, status
            FROM ALL_OBJECTS
            WHERE owner = :schema
            AND object_type IN ('PROCEDURE', 'FUNCTION', 'PACKAGE', 'PACKAGE BODY')
        """, schema=schema)
        
        routines = cursor.fetchall()
        for r in routines:
            obj_name = r[0]
            obj_type = r[1]
            
            cursor.execute("""
                SELECT text FROM ALL_SOURCE
                WHERE owner = :schema
                AND name = :obj_name
                AND type = :obj_type
                ORDER BY line
            """, schema=schema, obj_name=obj_name, obj_type=obj_type)
            
            definition = "".join([line[0] for line in cursor.fetchall()])
            
            result["procedures"].append({
                "object_type": "procedure" if obj_type == "PROCEDURE" else "function",
                "name": obj_name,
                "schema_name": schema,
                "source_definition": definition,
            })
            
        cursor.execute("""
            SELECT trigger_name, trigger_type,
                   triggering_event, table_name,
                   trigger_body
            FROM ALL_TRIGGERS
            WHERE owner = :schema
            AND base_object_type = 'TABLE'
        """, schema=schema)
        
        for row in cursor.fetchall():
            result["triggers"].append({
                "object_type": "trigger",
                "name": row[0],
                "schema_name": schema,
                "source_definition": f"CREATE OR REPLACE TRIGGER {row[0]} {row[1]} {row[2]} ON {row[3]}\n{row[4]}",
            })
            
        conn.close()
        return result
