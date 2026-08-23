import re

file_path = r"backend\agents\validation_agent.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import_hashlib_code = """
from typing import Dict, Any, List
import hashlib
"""

content = content.replace("from typing import Dict, Any, List", import_hashlib_code)

checksum_code = """            elif engine == "mssql":
                cols_joined = ", ".join(columns)
                query = f"SELECT CHECKSUM_AGG(CHECKSUM({cols_joined})) FROM {table_name}"
                cursor.execute(query)
                checksum = str(cursor.fetchone()[0])
            elif engine == "oracle":
                hasher = hashlib.md5()
                cursor.arraysize = 1000
                if pk:
                    cursor.execute(f"SELECT * FROM {table_name} ORDER BY {pk}")
                else:
                    cursor.execute(f"SELECT * FROM {table_name}")
                while True:
                    rows = cursor.fetchmany(1000)
                    if not rows:
                        break
                    for row in rows:
                        row_str = "|".join(str(val) if val is not None else "" for val in row)
                        hasher.update(row_str.encode('utf-8'))
                checksum = hasher.hexdigest()"""

content = content.replace(
"""            elif engine == "mssql":
                cols_joined = ", ".join(columns)
                query = f"SELECT CHECKSUM_AGG(CHECKSUM({cols_joined})) FROM {table_name}"
                cursor.execute(query)
                checksum = str(cursor.fetchone()[0])""",
checksum_code)

# Fix checksum_method in tables_report
content = content.replace(
""""checksum_method": "MD5" if target_engine == "postgres" else ("CRC32" if target_engine == "mysql" else "CHECKSUM"),""",
""""checksum_method": "MD5" if target_engine in ("postgres", "oracle") else ("CRC32" if target_engine == "mysql" else "CHECKSUM"),"""
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("validation_agent.py patched successfully.")
