import pprint
import re
import sys

oracle_to_mysql = {
    "datatypes": {
        "VARCHAR2": {"type": "VARCHAR", "lossy": False, "note": ""},
        "NUMBER": {"type": "DECIMAL", "lossy": False, "note": ""},
        "DATE": {"type": "DATETIME", "lossy": False, "note": ""},
        "TIMESTAMP": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "CLOB": {"type": "LONGTEXT", "lossy": False, "note": ""},
        "BLOB": {"type": "LONGBLOB", "lossy": False, "note": ""},
    },
    "constraints": {
        "PRIMARY KEY": "PRIMARY KEY",
        "FOREIGN KEY": "FOREIGN KEY",
        "UNIQUE": "UNIQUE",
        "CHECK": "CHECK",
        "NOT NULL": "NOT NULL",
        "DEFAULT": "DEFAULT",
    },
    "indexes": {"NORMAL": "INDEX", "UNIQUE": "UNIQUE INDEX", "BITMAP": "INDEX"},
    "pk_strategies": {"GENERATED ALWAYS AS IDENTITY": "AUTO_INCREMENT"},
    "fk_actions": {
        "CASCADE": "CASCADE",
        "SET NULL": "SET NULL",
        "NO ACTION": "NO ACTION",
        "RESTRICT": "RESTRICT",
    },
}

oracle_to_postgres = {
    "datatypes": {
        "VARCHAR2": {"type": "VARCHAR", "lossy": False, "note": ""},
        "NUMBER": {"type": "NUMERIC", "lossy": False, "note": ""},
        "DATE": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "TIMESTAMP": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "CLOB": {"type": "TEXT", "lossy": False, "note": ""},
        "BLOB": {"type": "BYTEA", "lossy": False, "note": ""},
    },
    "constraints": oracle_to_mysql["constraints"],
    "indexes": oracle_to_mysql["indexes"],
    "pk_strategies": {"GENERATED ALWAYS AS IDENTITY": "GENERATED ALWAYS AS IDENTITY"},
    "fk_actions": oracle_to_mysql["fk_actions"],
}

oracle_to_mssql = {
    "datatypes": {
        "VARCHAR2": {"type": "NVARCHAR", "lossy": False, "note": ""},
        "NUMBER": {"type": "DECIMAL", "lossy": False, "note": ""},
        "DATE": {"type": "DATETIME2", "lossy": False, "note": ""},
        "TIMESTAMP": {"type": "DATETIME2", "lossy": False, "note": ""},
        "CLOB": {"type": "NVARCHAR(MAX)", "lossy": False, "note": ""},
        "BLOB": {"type": "VARBINARY(MAX)", "lossy": False, "note": ""},
    },
    "constraints": oracle_to_mysql["constraints"],
    "indexes": oracle_to_mysql["indexes"],
    "pk_strategies": {"GENERATED ALWAYS AS IDENTITY": "IDENTITY"},
    "fk_actions": oracle_to_mysql["fk_actions"],
}

mysql_to_oracle = {
    "datatypes": {
        "INT": {"type": "NUMBER", "lossy": False, "note": ""},
        "VARCHAR": {"type": "VARCHAR2", "lossy": False, "note": ""},
        "TEXT": {"type": "CLOB", "lossy": False, "note": ""},
        "DATETIME": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "DATE": {"type": "DATE", "lossy": False, "note": ""},
        "BOOLEAN": {"type": "NUMBER(1)", "lossy": False, "note": ""},
    },
    "constraints": oracle_to_mysql["constraints"],
    "indexes": {"PRIMARY KEY": "NORMAL", "INDEX": "NORMAL", "UNIQUE INDEX": "UNIQUE"},
    "pk_strategies": {"AUTO_INCREMENT": "GENERATED ALWAYS AS IDENTITY"},
    "fk_actions": oracle_to_mysql["fk_actions"],
}

postgres_to_oracle = {
    "datatypes": {
        "INTEGER": {"type": "NUMBER", "lossy": False, "note": ""},
        "VARCHAR": {"type": "VARCHAR2", "lossy": False, "note": ""},
        "TEXT": {"type": "CLOB", "lossy": False, "note": ""},
        "TIMESTAMP": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "DATE": {"type": "DATE", "lossy": False, "note": ""},
        "BOOLEAN": {"type": "NUMBER(1)", "lossy": False, "note": ""},
    },
    "constraints": oracle_to_mysql["constraints"],
    "indexes": {"PRIMARY KEY": "NORMAL", "INDEX": "NORMAL", "UNIQUE INDEX": "UNIQUE"},
    "pk_strategies": {
        "GENERATED ALWAYS AS IDENTITY": "GENERATED ALWAYS AS IDENTITY",
        "SERIAL": "GENERATED ALWAYS AS IDENTITY",
    },
    "fk_actions": oracle_to_mysql["fk_actions"],
}

mssql_to_oracle = {
    "datatypes": {
        "INT": {"type": "NUMBER", "lossy": False, "note": ""},
        "NVARCHAR": {"type": "VARCHAR2", "lossy": False, "note": ""},
        "VARCHAR": {"type": "VARCHAR2", "lossy": False, "note": ""},
        "DATETIME": {"type": "TIMESTAMP", "lossy": False, "note": ""},
        "DATE": {"type": "DATE", "lossy": False, "note": ""},
        "BIT": {"type": "NUMBER(1)", "lossy": False, "note": ""},
    },
    "constraints": oracle_to_mysql["constraints"],
    "indexes": {"PRIMARY KEY": "NORMAL", "INDEX": "NORMAL", "UNIQUE INDEX": "UNIQUE"},
    "pk_strategies": {"IDENTITY": "GENERATED ALWAYS AS IDENTITY"},
    "fk_actions": oracle_to_mysql["fk_actions"],
}

new_entries = {
    "oracle_to_mysql": oracle_to_mysql,
    "oracle_to_postgres": oracle_to_postgres,
    "oracle_to_mssql": oracle_to_mssql,
    "mysql_to_oracle": mysql_to_oracle,
    "postgres_to_oracle": postgres_to_oracle,
    "mssql_to_oracle": mssql_to_oracle,
}

filename = "c:/Users/Ayaz Khan/Desktop/Database Migration Agent/backend/config/migration_matrix.py"
with open(filename) as f:
    content = f.read()

match = re.search(r"\}\s*\}\s*$", content)
if not match:
    print("Could not find end of dict")
    sys.exit(1)

new_str = ""
for k, v in new_entries.items():
    new_str += f',\n    "{k}": ' + pprint.pformat(v, indent=4).replace("\n", "\n    ")

new_content = content[: match.start()] + "}    " + new_str + "\n}\n"
with open(filename, "w") as f:
    f.write(new_content)

print("Successfully appended 6 new directions to migration_matrix.py")
