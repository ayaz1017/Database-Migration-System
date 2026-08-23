import json

oracle_to_mysql = {
    "datatypes": {
        "NUMBER": {"type": "DECIMAL(38,10)", "lossy": True, "note": "Oracle NUMBER has unlimited precision. Mapped to DECIMAL(38,10)."},
        "VARCHAR2": {"type": "VARCHAR", "lossy": False, "note": "Keep length. High-Unicode content may need NVARCHAR mapping."},
        "NVARCHAR2": {"type": "VARCHAR", "lossy": False, "note": "Keep length, ensure utf8mb4 encoding in MySQL"},
        "CHAR": {"type": "CHAR", "lossy": False, "note": "Keep length"},
        "NCHAR": {"type": "CHAR", "lossy": False, "note": "Keep length, ensure utf8mb4 encoding"},
        "CLOB": {"type": "LONGTEXT", "lossy": False, "note": ""},
        "NCLOB": {"type": "LONGTEXT", "lossy": False, "note": ""},
        "BLOB": {"type": "LONGBLOB", "lossy": False, "note": ""},
        "RAW": {"type": "VARBINARY", "lossy": False, "note": "Keep length"},
        "LONG": {"type": "LONGTEXT", "lossy": True, "note": "Deprecated in Oracle, mapped to LONGTEXT"},
        "LONG RAW": {"type": "LONGBLOB", "lossy": True, "note": "Deprecated in Oracle, mapped to LONGBLOB"},
        "DATE": {"type": "DATETIME", "lossy": False, "note": "Oracle DATE includes time. Mapped to DATETIME."},
        "TIMESTAMP": {"type": "DATETIME", "lossy": False, "note": ""},
        "TIMESTAMP WITH TIME ZONE": {"type": "TIMESTAMP", "lossy": True, "note": "Time zone info might be lost"},
        "TIMESTAMP WITH LOCAL TIME ZONE": {"type": "TIMESTAMP", "lossy": True, "note": ""},
        "INTERVAL YEAR TO MONTH": {"type": "VARCHAR(50)", "lossy": True, "note": "No native equivalent, mapped to string"},
        "INTERVAL DAY TO SECOND": {"type": "VARCHAR(50)", "lossy": True, "note": "No native equivalent, mapped to string"},
        "ROWID": {"type": "unsupported", "lossy": True, "note": "Pseudo-column, should be excluded"},
        "UROWID": {"type": "unsupported", "lossy": True, "note": "Pseudo-column, should be excluded"},
        "XMLTYPE": {"type": "LONGTEXT", "lossy": True, "note": "MySQL does not have native XML, using LONGTEXT"},
        "BFILE": {"type": "VARCHAR(255)", "lossy": True, "note": "Locator to external file, mapped to string"},
        "BINARY_FLOAT": {"type": "FLOAT", "lossy": False, "note": ""},
        "BINARY_DOUBLE": {"type": "DOUBLE", "lossy": False, "note": ""}
    },
    "constraints": {
        "PRIMARY KEY": "PRIMARY KEY",
        "FOREIGN KEY": "FOREIGN KEY",
        "UNIQUE": "UNIQUE",
        "CHECK": "CHECK",
        "NOT NULL": "NOT NULL",
        "DEFAULT": "DEFAULT"
    },
    "indexes": {
        "NORMAL": "INDEX",
        "BITMAP": "INDEX",
        "UNIQUE": "UNIQUE INDEX"
    },
    "pk_strategies": {
        "IDENTITY": "AUTO_INCREMENT"
    },
    "fk_actions": {
        "CASCADE": "CASCADE",
        "SET NULL": "SET NULL",
        "RESTRICT": "RESTRICT",
        "NO ACTION": "NO ACTION"
    }
}

oracle_to_postgres = {
    "datatypes": {
        "NUMBER": {"type": "DECIMAL(38,10)", "lossy": True, "note": "Oracle NUMBER has unlimited precision. Mapped to DECIMAL(38,10)."},
        "VARCHAR2": {"type": "VARCHAR", "lossy": False, "note": "Keep length"},
        "NVARCHAR2": {"type": "VARCHAR", "lossy": False, "note": "Keep length"},
        "CHAR": {"type": "CHAR", "lossy": False, "note": "Keep length"},
        "NCHAR": {"type": "CHAR", "lossy": False, "note": "Keep length"},
        "CLOB": {"type": "TEXT", "lossy": False, "note": ""},
        "NCLOB": {"type": "TEXT", "lossy": False, "note": ""},
        "BLOB": {"type": "BYTEA", "lossy": False, "note": ""},
        "RAW": {"type": "BYTEA", "lossy": False, "note": "Keep length"},
        "LONG": {"type": "TEXT", "lossy": True, "note": "Deprecated in Oracle, mapped to TEXT"},
        "LONG RAW": {"type": "BYTEA", "lossy": True, "note": "Deprecated in Oracle, mapped to BYTEA"},
        "DATE": {"type": "TIMESTAMP", "lossy": False, "note": "Oracle DATE includes time. Mapped to TIMESTAMP."},
        "TIMESTAMP": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "TIMESTAMP WITH TIME ZONE": {"type": "TIMESTAMP WITH TIME ZONE", "lossy": False, "note": ""},
        "TIMESTAMP WITH LOCAL TIME ZONE": {"type": "TIMESTAMP WITH TIME ZONE", "lossy": False, "note": ""},
        "INTERVAL YEAR TO MONTH": {"type": "INTERVAL", "lossy": False, "note": ""},
        "INTERVAL DAY TO SECOND": {"type": "INTERVAL", "lossy": False, "note": ""},
        "ROWID": {"type": "unsupported", "lossy": True, "note": "Pseudo-column, should be excluded"},
        "UROWID": {"type": "unsupported", "lossy": True, "note": "Pseudo-column, should be excluded"},
        "XMLTYPE": {"type": "XML", "lossy": False, "note": ""},
        "BFILE": {"type": "VARCHAR", "lossy": True, "note": "Locator to external file"},
        "BINARY_FLOAT": {"type": "REAL", "lossy": False, "note": ""},
        "BINARY_DOUBLE": {"type": "DOUBLE PRECISION", "lossy": False, "note": ""}
    },
    "constraints": {
        "PRIMARY KEY": "PRIMARY KEY",
        "FOREIGN KEY": "FOREIGN KEY",
        "UNIQUE": "UNIQUE",
        "CHECK": "CHECK",
        "NOT NULL": "NOT NULL",
        "DEFAULT": "DEFAULT"
    },
    "indexes": {
        "NORMAL": "INDEX",
        "BITMAP": "INDEX",
        "UNIQUE": "UNIQUE INDEX"
    },
    "pk_strategies": {
        "IDENTITY": "GENERATED ALWAYS AS IDENTITY"
    },
    "fk_actions": {
        "CASCADE": "CASCADE",
        "SET NULL": "SET NULL",
        "RESTRICT": "RESTRICT",
        "NO ACTION": "NO ACTION"
    }
}

oracle_to_mssql = {
    "datatypes": {
        "NUMBER": {"type": "DECIMAL(38,10)", "lossy": True, "note": "Oracle NUMBER has unlimited precision. Mapped to DECIMAL(38,10)."},
        "VARCHAR2": {"type": "NVARCHAR", "lossy": False, "note": "Keep length. Mapped to NVARCHAR for Unicode."},
        "NVARCHAR2": {"type": "NVARCHAR", "lossy": False, "note": "Keep length"},
        "CHAR": {"type": "NCHAR", "lossy": False, "note": "Keep length"},
        "NCHAR": {"type": "NCHAR", "lossy": False, "note": "Keep length"},
        "CLOB": {"type": "NVARCHAR(MAX)", "lossy": False, "note": ""},
        "NCLOB": {"type": "NVARCHAR(MAX)", "lossy": False, "note": ""},
        "BLOB": {"type": "VARBINARY(MAX)", "lossy": False, "note": ""},
        "RAW": {"type": "VARBINARY", "lossy": False, "note": "Keep length"},
        "LONG": {"type": "NVARCHAR(MAX)", "lossy": True, "note": "Deprecated in Oracle, mapped to NVARCHAR(MAX)"},
        "LONG RAW": {"type": "VARBINARY(MAX)", "lossy": True, "note": "Deprecated in Oracle, mapped to VARBINARY(MAX)"},
        "DATE": {"type": "DATETIME2", "lossy": False, "note": "Oracle DATE includes time. Mapped to DATETIME2."},
        "TIMESTAMP": {"type": "DATETIME2", "lossy": False, "note": ""},
        "TIMESTAMP WITH TIME ZONE": {"type": "DATETIMEOFFSET", "lossy": False, "note": ""},
        "TIMESTAMP WITH LOCAL TIME ZONE": {"type": "DATETIMEOFFSET", "lossy": False, "note": ""},
        "INTERVAL YEAR TO MONTH": {"type": "NVARCHAR(50)", "lossy": True, "note": "No native equivalent, mapped to string"},
        "INTERVAL DAY TO SECOND": {"type": "NVARCHAR(50)", "lossy": True, "note": "No native equivalent, mapped to string"},
        "ROWID": {"type": "unsupported", "lossy": True, "note": "Pseudo-column, should be excluded"},
        "UROWID": {"type": "unsupported", "lossy": True, "note": "Pseudo-column, should be excluded"},
        "XMLTYPE": {"type": "XML", "lossy": False, "note": ""},
        "BFILE": {"type": "NVARCHAR(255)", "lossy": True, "note": "Locator to external file"},
        "BINARY_FLOAT": {"type": "REAL", "lossy": False, "note": ""},
        "BINARY_DOUBLE": {"type": "FLOAT", "lossy": False, "note": ""}
    },
    "constraints": {
        "PRIMARY KEY": "PRIMARY KEY",
        "FOREIGN KEY": "FOREIGN KEY",
        "UNIQUE": "UNIQUE",
        "CHECK": "CHECK",
        "NOT NULL": "NOT NULL",
        "DEFAULT": "DEFAULT"
    },
    "indexes": {
        "NORMAL": "NONCLUSTERED INDEX",
        "BITMAP": "NONCLUSTERED INDEX",
        "UNIQUE": "UNIQUE NONCLUSTERED INDEX"
    },
    "pk_strategies": {
        "IDENTITY": "IDENTITY"
    },
    "fk_actions": {
        "CASCADE": "CASCADE",
        "SET NULL": "SET NULL",
        "RESTRICT": "NO ACTION",
        "NO ACTION": "NO ACTION"
    }
}

mssql_to_oracle = {
    "datatypes": {
        "INT": {"type": "NUMBER(10,0)", "lossy": False, "note": ""},
        "BIGINT": {"type": "NUMBER(19,0)", "lossy": False, "note": ""},
        "SMALLINT": {"type": "NUMBER(5,0)", "lossy": False, "note": ""},
        "TINYINT": {"type": "NUMBER(3,0)", "lossy": False, "note": ""},
        "BIT": {"type": "NUMBER(1)", "lossy": False, "note": "Mapped to NUMBER(1) for boolean (0/1)"},
        "FLOAT": {"type": "BINARY_DOUBLE", "lossy": False, "note": ""},
        "REAL": {"type": "BINARY_FLOAT", "lossy": False, "note": ""},
        "DECIMAL": {"type": "NUMBER", "lossy": False, "note": "Keep precision and scale (p,s)"},
        "NUMERIC": {"type": "NUMBER", "lossy": False, "note": "Keep precision and scale (p,s)"},
        "VARCHAR": {"type": "VARCHAR2", "lossy": False, "note": "Keep length (n)"},
        "NVARCHAR": {"type": "NVARCHAR2", "lossy": False, "note": "Keep length (n)"},
        "TEXT": {"type": "CLOB", "lossy": False, "note": ""},
        "NTEXT": {"type": "NCLOB", "lossy": False, "note": ""},
        "CHAR": {"type": "CHAR", "lossy": False, "note": "Keep length (n)"},
        "NCHAR": {"type": "NCHAR", "lossy": False, "note": "Keep length (n)"},
        "DATETIME": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "DATETIME2": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "DATE": {"type": "DATE", "lossy": False, "note": ""},
        "TIME": {"type": "TIMESTAMP", "lossy": True, "note": "Oracle lacks native TIME, mapped to TIMESTAMP"},
        "TIMESTAMP": {"type": "RAW(8)", "lossy": False, "note": "MSSQL TIMESTAMP is a rowversion. Mapped to RAW(8)."},
        "SMALLDATETIME": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "UNIQUEIDENTIFIER": {"type": "VARCHAR2(36)", "lossy": False, "note": ""},
        "VARBINARY": {"type": "RAW", "lossy": False, "note": "Keep length (n) or map to BLOB if MAX"},
        "IMAGE": {"type": "BLOB", "lossy": False, "note": ""},
        "XML": {"type": "XMLTYPE", "lossy": False, "note": ""},
        "MONEY": {"type": "NUMBER(19,4)", "lossy": False, "note": ""},
        "SMALLMONEY": {"type": "NUMBER(10,4)", "lossy": False, "note": ""},
        "JSON": {"type": "CLOB", "lossy": False, "note": "Oracle 21c supports native JSON, but stored as BLOB/CLOB or JSON datatype. Mapped to CLOB."},
        "UUID": {"type": "VARCHAR2(36)", "lossy": False, "note": ""},
        "SERIAL": {"type": "NUMBER", "lossy": False, "note": ""},
        "BYTEA": {"type": "BLOB", "lossy": False, "note": ""},
        "TINYBLOB": {"type": "BLOB", "lossy": False, "note": ""},
        "MEDIUMBLOB": {"type": "BLOB", "lossy": False, "note": ""},
        "LONGBLOB": {"type": "BLOB", "lossy": False, "note": ""},
        "ENUM": {"type": "VARCHAR2(255)", "lossy": False, "note": ""},
        "SET": {"type": "VARCHAR2(255)", "lossy": False, "note": ""},
        "BOOLEAN": {"type": "NUMBER(1)", "lossy": True, "note": "Oracle has NO native BOOLEAN at the SQL column level. Mapped to NUMBER(1) (0/1)"},
        "BOOL": {"type": "NUMBER(1)", "lossy": True, "note": "Oracle has NO native BOOLEAN at the SQL column level. Mapped to NUMBER(1) (0/1)"}
    },
    "constraints": {
        "PRIMARY KEY": "PRIMARY KEY",
        "FOREIGN KEY": "FOREIGN KEY",
        "UNIQUE": "UNIQUE",
        "CHECK": "CHECK",
        "NOT NULL": "NOT NULL",
        "DEFAULT": "DEFAULT"
    },
    "indexes": {
        "CLUSTERED": "INDEX",
        "NONCLUSTERED": "INDEX",
        "FULLTEXT": "unsupported",
        "SPATIAL": "unsupported",
        "UNIQUE INDEX": "UNIQUE INDEX",
        "COMPOSITE INDEX": "INDEX"
    },
    "pk_strategies": {
        "IDENTITY": "GENERATED BY DEFAULT AS IDENTITY"
    },
    "fk_actions": {
        "CASCADE": "CASCADE",
        "SET NULL": "SET NULL",
        "SET DEFAULT": "unsupported",
        "RESTRICT": "RESTRICT",
        "NO ACTION": "NO ACTION"
    }
}

mysql_to_oracle = {
    "datatypes": {
        "INT": {"type": "NUMBER(10,0)", "lossy": False, "note": ""},
        "BIGINT": {"type": "NUMBER(19,0)", "lossy": False, "note": ""},
        "SMALLINT": {"type": "NUMBER(5,0)", "lossy": False, "note": ""},
        "TINYINT": {"type": "NUMBER(3,0)", "lossy": False, "note": ""},
        "BIT": {"type": "NUMBER(1)", "lossy": False, "note": "Mapped to NUMBER(1)"},
        "FLOAT": {"type": "BINARY_FLOAT", "lossy": False, "note": ""},
        "DOUBLE": {"type": "BINARY_DOUBLE", "lossy": False, "note": ""},
        "DECIMAL": {"type": "NUMBER", "lossy": False, "note": "Keep precision and scale"},
        "NUMERIC": {"type": "NUMBER", "lossy": False, "note": "Keep precision and scale"},
        "VARCHAR": {"type": "VARCHAR2", "lossy": False, "note": "Keep length"},
        "TEXT": {"type": "CLOB", "lossy": False, "note": ""},
        "LONGTEXT": {"type": "CLOB", "lossy": False, "note": ""},
        "CHAR": {"type": "CHAR", "lossy": False, "note": ""},
        "DATETIME": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "DATE": {"type": "DATE", "lossy": False, "note": ""},
        "TIME": {"type": "TIMESTAMP", "lossy": True, "note": "Oracle lacks native TIME"},
        "TIMESTAMP": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "VARBINARY": {"type": "RAW", "lossy": False, "note": ""},
        "BLOB": {"type": "BLOB", "lossy": False, "note": ""},
        "TINYBLOB": {"type": "BLOB", "lossy": False, "note": ""},
        "MEDIUMBLOB": {"type": "BLOB", "lossy": False, "note": ""},
        "LONGBLOB": {"type": "BLOB", "lossy": False, "note": ""},
        "JSON": {"type": "CLOB", "lossy": False, "note": ""},
        "ENUM": {"type": "VARCHAR2(255)", "lossy": False, "note": "Check constraint recommended"},
        "SET": {"type": "VARCHAR2(255)", "lossy": True, "note": ""},
        "BOOLEAN": {"type": "NUMBER(1)", "lossy": True, "note": "Oracle has NO native BOOLEAN at the SQL column level. Mapped to NUMBER(1) (0/1)"},
        "BOOL": {"type": "NUMBER(1)", "lossy": True, "note": "Oracle has NO native BOOLEAN at the SQL column level. Mapped to NUMBER(1) (0/1)"}
    },
    "constraints": {
        "PRIMARY KEY": "PRIMARY KEY",
        "FOREIGN KEY": "FOREIGN KEY",
        "UNIQUE": "UNIQUE",
        "CHECK": "CHECK",
        "NOT NULL": "NOT NULL",
        "DEFAULT": "DEFAULT"
    },
    "indexes": {
        "PRIMARY": "INDEX",
        "INDEX": "INDEX",
        "UNIQUE": "UNIQUE INDEX",
        "FULLTEXT": "unsupported",
        "SPATIAL": "unsupported"
    },
    "pk_strategies": {
        "AUTO_INCREMENT": "GENERATED BY DEFAULT AS IDENTITY"
    },
    "fk_actions": {
        "CASCADE": "CASCADE",
        "SET NULL": "SET NULL",
        "RESTRICT": "RESTRICT",
        "NO ACTION": "NO ACTION"
    }
}

postgres_to_oracle = {
    "datatypes": {
        "INTEGER": {"type": "NUMBER(10,0)", "lossy": False, "note": ""},
        "BIGINT": {"type": "NUMBER(19,0)", "lossy": False, "note": ""},
        "SMALLINT": {"type": "NUMBER(5,0)", "lossy": False, "note": ""},
        "BOOLEAN": {"type": "NUMBER(1)", "lossy": True, "note": "Oracle has NO native BOOLEAN at the SQL column level. Mapped to NUMBER(1) (0/1)"},
        "REAL": {"type": "BINARY_FLOAT", "lossy": False, "note": ""},
        "DOUBLE PRECISION": {"type": "BINARY_DOUBLE", "lossy": False, "note": ""},
        "DECIMAL": {"type": "NUMBER", "lossy": False, "note": ""},
        "NUMERIC": {"type": "NUMBER", "lossy": False, "note": ""},
        "VARCHAR": {"type": "VARCHAR2", "lossy": False, "note": ""},
        "TEXT": {"type": "CLOB", "lossy": False, "note": ""},
        "CHAR": {"type": "CHAR", "lossy": False, "note": ""},
        "TIMESTAMP": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "DATE": {"type": "DATE", "lossy": False, "note": ""},
        "TIME": {"type": "TIMESTAMP", "lossy": True, "note": ""},
        "BYTEA": {"type": "BLOB", "lossy": False, "note": ""},
        "JSON": {"type": "CLOB", "lossy": False, "note": ""},
        "JSONB": {"type": "BLOB", "lossy": False, "note": ""},
        "UUID": {"type": "VARCHAR2(36)", "lossy": False, "note": ""},
        "XML": {"type": "XMLTYPE", "lossy": False, "note": ""},
        "MONEY": {"type": "NUMBER(19,4)", "lossy": False, "note": ""}
    },
    "constraints": {
        "PRIMARY KEY": "PRIMARY KEY",
        "FOREIGN KEY": "FOREIGN KEY",
        "UNIQUE": "UNIQUE",
        "CHECK": "CHECK",
        "NOT NULL": "NOT NULL",
        "DEFAULT": "DEFAULT"
    },
    "indexes": {
        "BTREE": "INDEX",
        "HASH": "INDEX",
        "GIST": "unsupported",
        "GIN": "unsupported"
    },
    "pk_strategies": {
        "SERIAL": "GENERATED BY DEFAULT AS IDENTITY",
        "BIGSERIAL": "GENERATED BY DEFAULT AS IDENTITY",
        "GENERATED ALWAYS AS IDENTITY": "GENERATED BY DEFAULT AS IDENTITY"
    },
    "fk_actions": {
        "CASCADE": "CASCADE",
        "SET NULL": "SET NULL",
        "SET DEFAULT": "unsupported",
        "RESTRICT": "RESTRICT",
        "NO ACTION": "NO ACTION"
    }
}

file_path = r"backend\config\migration_matrix.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

import ast

def find_dict_end(s, start_idx):
    # This assumes 'MIGRATION_MATRIX: Dict[str, Any] = {' is at the top
    stack = []
    for i in range(start_idx, len(s)):
        if s[i] == '{':
            stack.append('{')
        elif s[i] == '}':
            if stack:
                stack.pop()
                if not stack:
                    return i
    return -1

matrix_start = content.find("MIGRATION_MATRIX")
open_brace = content.find("{", matrix_start)
close_brace = find_dict_end(content, open_brace)

new_keys_str = f""",
    "oracle_to_mysql": {json.dumps(oracle_to_mysql, indent=8)},
    "oracle_to_postgres": {json.dumps(oracle_to_postgres, indent=8)},
    "oracle_to_mssql": {json.dumps(oracle_to_mssql, indent=8)},
    "mssql_to_oracle": {json.dumps(mssql_to_oracle, indent=8)},
    "mysql_to_oracle": {json.dumps(mysql_to_oracle, indent=8)},
    "postgres_to_oracle": {json.dumps(postgres_to_oracle, indent=8)}
"""

new_content = content[:close_brace] + new_keys_str + content[close_brace:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Matrix updated successfully.")
