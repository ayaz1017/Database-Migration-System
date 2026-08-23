import re

file_path = r"backend\services\discovery_service.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add import
content = content.replace("import psycopg2\n", "import psycopg2\nimport oracledb\n")

# 2. Update _make_connection signature and body
content = content.replace("def _make_connection(self, host, port, username, password, db_type):", "def _make_connection(self, host, port, username, password, db_type, database=None):")
content = content.replace(
"""        elif db_type.lower() in ["postgres", "postgresql"]:
            return psycopg2.connect(host=host, port=port, user=username, password=password, dbname="postgres")
        else:""",
"""        elif db_type.lower() in ["postgres", "postgresql"]:
            return psycopg2.connect(host=host, port=port, user=username, password=password, dbname="postgres")
        elif db_type.lower() == "oracle":
            return oracledb.connect(user=username, password=password, dsn=f"{host}:{port}/{database}")
        else:"""
)

# 3. Update connect_and_discover
content = content.replace(
"connection = self._make_connection(host, port, username, password, db_type)",
"connection = self._make_connection(host, port, username, password, db_type, database)"
)

content = content.replace(
"""        elif db_type.lower() in ["postgres", "postgresql"]:
            return self._discover_postgres(host, port, username, password, database)
        else:""",
"""        elif db_type.lower() in ["postgres", "postgresql"]:
            return self._discover_postgres(host, port, username, password, database)
        elif db_type.lower() == "oracle":
            return self._discover_oracle(host, port, username, password, database)
        else:"""
)

# 4. Add _discover_oracle
oracle_method = """

    def _discover_oracle(self, host: str, port: int, username: str, password: str, database: str) -> Dict[str, Any]:
        conn = oracledb.connect(
            user=username,
            password=password,
            dsn=f"{host}:{port}/{database}"
        )
        cursor = conn.cursor()
        
        result = {
            "databases": [database] if database else [],
            "schemas": [username.upper()],
            "tables": [],
            "row_counts": {}
        }
        
        cursor.execute("SELECT table_name FROM user_tables")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            table_info = {
                "name": table,
                "columns": [],
                "primary_keys": [],
                "foreign_keys": [],
                "indexes": [],
                "check_constraints": [],
                "row_count": 0
            }
            
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row = cursor.fetchone()
            table_info["row_count"] = row[0] if row else 0
            
            cursor.execute('''
                SELECT column_name, data_type, data_length, data_precision, data_scale, nullable, data_default 
                FROM user_tab_columns WHERE table_name = :table_name
            ''', table_name=table)
            for row in cursor.fetchall():
                table_info["columns"].append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[5] == 'Y',
                    "default": row[6]
                })
                
            cursor.execute('''
                SELECT cols.column_name 
                FROM user_constraints cons
                JOIN user_cons_columns cols ON cons.constraint_name = cols.constraint_name 
                WHERE cons.constraint_type = 'P' AND cons.table_name = :table_name
            ''', table_name=table)
            table_info["primary_keys"] = [row[0] for row in cursor.fetchall()]
            
            cursor.execute('''
                SELECT cols.column_name,
                       r_cons.table_name as referenced_table,
                       r_cols.column_name as referenced_column
                FROM user_constraints cons
                JOIN user_cons_columns cols ON cons.constraint_name = cols.constraint_name
                JOIN user_constraints r_cons ON cons.r_constraint_name = r_cons.constraint_name
                JOIN user_cons_columns r_cols ON r_cons.constraint_name = r_cols.constraint_name AND cols.position = r_cols.position
                WHERE cons.constraint_type = 'R' AND cons.table_name = :table_name
            ''', table_name=table)
            for row in cursor.fetchall():
                table_info["foreign_keys"].append({
                    "column": row[0],
                    "references_table": row[1],
                    "references_column": row[2],
                    "on_delete": "UNKNOWN",
                    "on_update": "UNKNOWN"
                })
                
            cursor.execute('''
                SELECT index_name, column_name 
                FROM user_ind_columns 
                WHERE table_name = :table_name
            ''', table_name=table)
            indexes_dict = {}
            for row in cursor.fetchall():
                idx_name, col_name = row
                if idx_name not in indexes_dict:
                    indexes_dict[idx_name] = {
                        "name": idx_name,
                        "unique": False, # Basic discovery doesn't fetch uniqueness here easily without joining user_indexes
                        "type": "NORMAL",
                        "columns": []
                    }
                indexes_dict[idx_name]["columns"].append(col_name)
            table_info["indexes"] = list(indexes_dict.values())
            
            cursor.execute('''
                SELECT search_condition 
                FROM user_constraints 
                WHERE constraint_type = 'C' AND table_name = :table_name
            ''', table_name=table)
            table_info["check_constraints"] = [str(row[0]) for row in cursor.fetchall() if row[0]]
            
            result["tables"].append(table_info)
            
        conn.close()
        return result
"""

content += oracle_method

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Discovery service patched successfully.")
