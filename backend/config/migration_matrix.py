from typing import Any, Dict

MIGRATION_MATRIX: Dict[str, Any] = {
    "mssql_to_mysql": {
        "datatypes": {
            "INT": {
                "type": "INT",
                "lossy": False,
                "note": ""
            },
            "BIGINT": {
                "type": "BIGINT",
                "lossy": False,
                "note": ""
            },
            "SMALLINT": {
                "type": "SMALLINT",
                "lossy": False,
                "note": ""
            },
            "TINYINT": {
                "type": "TINYINT",
                "lossy": False,
                "note": "MySQL TINYINT is signed by default (-128 to 127). MSSQL TINYINT is unsigned (0 to 255). Check data range."
            },
            "BIT": {
                "type": "TINYINT(1)",
                "lossy": False,
                "note": "Mapped to TINYINT(1) representing boolean"
            },
            "FLOAT": {
                "type": "DOUBLE",
                "lossy": False,
                "note": "MSSQL FLOAT maps to DOUBLE in MySQL for precision preservation"
            },
            "REAL": {
                "type": "FLOAT",
                "lossy": False,
                "note": ""
            },
            "DECIMAL": {
                "type": "DECIMAL",
                "lossy": False,
                "note": "Keep precision and scale (p,s)"
            },
            "NUMERIC": {
                "type": "DECIMAL",
                "lossy": False,
                "note": "Keep precision and scale (p,s)"
            },
            "VARCHAR": {
                "type": "VARCHAR",
                "lossy": False,
                "note": "Keep length (n)"
            },
            "NVARCHAR": {
                "type": "VARCHAR",
                "lossy": False,
                "note": "Keep length (n), ensure utf8mb4 encoding in MySQL"
            },
            "TEXT": {
                "type": "TEXT",
                "lossy": False,
                "note": ""
            },
            "NTEXT": {
                "type": "LONGTEXT",
                "lossy": True,
                "note": "Mapped to LONGTEXT"
            },
            "CHAR": {
                "type": "CHAR",
                "lossy": False,
                "note": "Keep length (n)"
            },
            "NCHAR": {
                "type": "CHAR",
                "lossy": False,
                "note": "Keep length (n), ensure utf8mb4 encoding"
            },
            "DATETIME": {
                "type": "DATETIME",
                "lossy": False,
                "note": ""
            },
            "DATETIME2": {
                "type": "DATETIME(6)",
                "lossy": True,
                "note": "MSSQL DATETIME2 has 100ns precision (7 digits), MySQL max is microsecond (6 digits)"
            },
            "DATE": {
                "type": "DATE",
                "lossy": False,
                "note": ""
            },
            "TIME": {
                "type": "TIME",
                "lossy": False,
                "note": ""
            },
            "TIMESTAMP": {
                "type": "BINARY(8)",
                "lossy": False,
                "note": "MSSQL TIMESTAMP is a rowversion, not a date. Mapped to BINARY(8)."
            },
            "SMALLDATETIME": {
                "type": "DATETIME",
                "lossy": False,
                "note": ""
            },
            "UNIQUEIDENTIFIER": {
                "type": "CHAR(36)",
                "lossy": False,
                "note": "Stored as string UUID"
            },
            "VARBINARY": {
                "type": "VARBINARY",
                "lossy": False,
                "note": "Keep length (n) or map to BLOB if MAX"
            },
            "IMAGE": {
                "type": "LONGBLOB",
                "lossy": True,
                "note": ""
            },
            "XML": {
                "type": "LONGTEXT",
                "lossy": True,
                "note": "MySQL does not have native XML, using LONGTEXT"
            },
            "MONEY": {
                "type": "DECIMAL(19,4)",
                "lossy": True,
                "note": ""
            },
            "SMALLMONEY": {
                "type": "DECIMAL(10,4)",
                "lossy": True,
                "note": ""
            },
            "JSON": {
                "type": "JSON",
                "lossy": False,
                "note": "MSSQL JSON is NVARCHAR, but conceptual mapping is JSON"
            },
            "UUID": {
                "type": "CHAR(36)",
                "lossy": False,
                "note": ""
            },
            "SERIAL": {
                "type": "BIGINT",
                "lossy": False,
                "note": ""
            },
            "BYTEA": {
                "type": "LONGBLOB",
                "lossy": False,
                "note": ""
            },
            "TINYBLOB": {
                "type": "TINYBLOB",
                "lossy": False,
                "note": ""
            },
            "MEDIUMBLOB": {
                "type": "MEDIUMBLOB",
                "lossy": False,
                "note": ""
            },
            "LONGBLOB": {
                "type": "LONGBLOB",
                "lossy": False,
                "note": ""
            },
            "ENUM": {
                "type": "ENUM",
                "lossy": False,
                "note": ""
            },
            "SET": {
                "type": "SET",
                "lossy": False,
                "note": ""
            },
            "BOOLEAN": {
                "type": "TINYINT(1)",
                "lossy": False,
                "note": ""
            },
            "BOOL": {
                "type": "TINYINT(1)",
                "lossy": False,
                "note": ""
            }
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
            "CLUSTERED": "PRIMARY KEY / INDEX",
            "NONCLUSTERED": "INDEX",
            "FULLTEXT": "FULLTEXT INDEX",
            "SPATIAL": "SPATIAL INDEX",
            "UNIQUE INDEX": "UNIQUE INDEX",
            "COMPOSITE INDEX": "INDEX"
        },
        "pk_strategies": {
            "IDENTITY": "AUTO_INCREMENT"
        },
        "fk_actions": {
            "CASCADE": "CASCADE",
            "SET NULL": "SET NULL",
            "SET DEFAULT": "RESTRICT",
            "RESTRICT": "RESTRICT",
            "NO ACTION": "NO ACTION"
        }
    },
    "mssql_to_postgres": {
        "datatypes": {
            "INT": {
                "type": "INTEGER",
                "lossy": False,
                "note": ""
            },
            "BIGINT": {
                "type": "BIGINT",
                "lossy": False,
                "note": ""
            },
            "SMALLINT": {
                "type": "SMALLINT",
                "lossy": False,
                "note": ""
            },
            "TINYINT": {
                "type": "SMALLINT",
                "lossy": False,
                "note": "Postgres lacks TINYINT, mapped to SMALLINT"
            },
            "BIT": {
                "type": "BOOLEAN",
                "lossy": False,
                "note": "Assuming bit corresponds to a boolean flag"
            },
            "FLOAT": {
                "type": "DOUBLE PRECISION",
                "lossy": False,
                "note": ""
            },
            "REAL": {
                "type": "REAL",
                "lossy": False,
                "note": ""
            },
            "DECIMAL": {
                "type": "DECIMAL",
                "lossy": False,
                "note": "Keep precision and scale (p,s)"
            },
            "NUMERIC": {
                "type": "NUMERIC",
                "lossy": False,
                "note": "Keep precision and scale (p,s)"
            },
            "VARCHAR": {
                "type": "VARCHAR",
                "lossy": False,
                "note": "Keep length (n)"
            },
            "NVARCHAR": {
                "type": "VARCHAR",
                "lossy": False,
                "note": "Keep length (n)"
            },
            "TEXT": {
                "type": "TEXT",
                "lossy": False,
                "note": ""
            },
            "NTEXT": {
                "type": "TEXT",
                "lossy": False,
                "note": ""
            },
            "CHAR": {
                "type": "CHAR",
                "lossy": False,
                "note": "Keep length (n)"
            },
            "NCHAR": {
                "type": "CHAR",
                "lossy": False,
                "note": "Keep length (n)"
            },
            "DATETIME": {
                "type": "TIMESTAMP",
                "lossy": False,
                "note": ""
            },
            "DATETIME2": {
                "type": "TIMESTAMP",
                "lossy": True,
                "note": "Postgres TIMESTAMP is up to microsecond (6 digits). MSSQL DATETIME2 is 100ns (7 digits)."
            },
            "DATETIMEOFFSET": {
                "type": "TIMESTAMPTZ",
                "lossy": True,
                "note": "Postgres TIMESTAMPTZ stores as UTC internally. MSSQL DATETIMEOFFSET preserves original offset."
            },
            "DATE": {
                "type": "DATE",
                "lossy": False,
                "note": ""
            },
            "TIME": {
                "type": "TIME",
                "lossy": False,
                "note": ""
            },
            "TIMESTAMP": {
                "type": "BYTEA",
                "lossy": False,
                "note": "MSSQL TIMESTAMP is rowversion. Mapped to BYTEA."
            },
            "SMALLDATETIME": {
                "type": "TIMESTAMP",
                "lossy": False,
                "note": ""
            },
            "UNIQUEIDENTIFIER": {
                "type": "UUID",
                "lossy": False,
                "note": ""
            },
            "VARBINARY": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "IMAGE": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "XML": {
                "type": "XML",
                "lossy": False,
                "note": ""
            },
            "MONEY": {
                "type": "MONEY",
                "lossy": False,
                "note": ""
            },
            "SMALLMONEY": {
                "type": "MONEY",
                "lossy": False,
                "note": ""
            },
            "JSON": {
                "type": "JSONB",
                "lossy": False,
                "note": ""
            },
            "UUID": {
                "type": "UUID",
                "lossy": False,
                "note": ""
            },
            "SERIAL": {
                "type": "SERIAL",
                "lossy": False,
                "note": ""
            },
            "BYTEA": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "TINYBLOB": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "MEDIUMBLOB": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "LONGBLOB": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "ENUM": {
                "type": "VARCHAR",
                "lossy": False,
                "note": "Postgres needs explicit CREATE TYPE for ENUM, fallback to VARCHAR"
            },
            "SET": {
                "type": "VARCHAR",
                "lossy": True,
                "note": "Mapped to VARCHAR array or string"
            },
            "BOOLEAN": {
                "type": "BOOLEAN",
                "lossy": False,
                "note": ""
            },
            "BOOL": {
                "type": "BOOLEAN",
                "lossy": False,
                "note": ""
            }
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
            "CLUSTERED": "PRIMARY KEY / INDEX",
            "NONCLUSTERED": "INDEX",
            "FULLTEXT": "unsupported",
            "SPATIAL": "GIST INDEX",
            "UNIQUE INDEX": "UNIQUE INDEX",
            "COMPOSITE INDEX": "INDEX"
        },
        "pk_strategies": {
            "IDENTITY": "GENERATED ALWAYS AS IDENTITY"
        },
        "fk_actions": {
            "CASCADE": "CASCADE",
            "SET NULL": "SET NULL",
            "SET DEFAULT": "SET DEFAULT",
            "RESTRICT": "RESTRICT",
            "NO ACTION": "NO ACTION"
        }
    },
    "mysql_to_mssql": {
        "datatypes": {
            "INT": {
                "type": "INT",
                "lossy": False,
                "note": ""
            },
            "BIGINT": {
                "type": "BIGINT",
                "lossy": False,
                "note": ""
            },
            "SMALLINT": {
                "type": "SMALLINT",
                "lossy": False,
                "note": ""
            },
            "TINYINT": {
                "type": "TINYINT",
                "lossy": False,
                "note": ""
            },
            "BIT": {
                "type": "BIT",
                "lossy": False,
                "note": ""
            },
            "FLOAT": {
                "type": "REAL",
                "lossy": False,
                "note": ""
            },
            "DOUBLE": {
                "type": "FLOAT",
                "lossy": False,
                "note": ""
            },
            "DECIMAL": {
                "type": "DECIMAL",
                "lossy": False,
                "note": "Keep precision and scale"
            },
            "NUMERIC": {
                "type": "NUMERIC",
                "lossy": False,
                "note": "Keep precision and scale"
            },
            "VARCHAR": {
                "type": "NVARCHAR",
                "lossy": False,
                "note": "Using NVARCHAR for better Unicode support"
            },
            "TEXT": {
                "type": "NVARCHAR(MAX)",
                "lossy": False,
                "note": "Using NVARCHAR(MAX) instead of deprecated TEXT"
            },
            "CHAR": {
                "type": "NCHAR",
                "lossy": False,
                "note": ""
            },
            "DATETIME": {
                "type": "DATETIME2",
                "lossy": False,
                "note": ""
            },
            "DATE": {
                "type": "DATE",
                "lossy": False,
                "note": ""
            },
            "TIME": {
                "type": "TIME",
                "lossy": False,
                "note": ""
            },
            "TIMESTAMP": {
                "type": "DATETIME2",
                "lossy": False,
                "note": "MySQL TIMESTAMP is datetime, MSSQL TIMESTAMP is rowversion. Map to DATETIME2."
            },
            "VARBINARY": {
                "type": "VARBINARY",
                "lossy": False,
                "note": ""
            },
            "BLOB": {
                "type": "VARBINARY(MAX)",
                "lossy": False,
                "note": ""
            },
            "TINYBLOB": {
                "type": "VARBINARY(255)",
                "lossy": False,
                "note": ""
            },
            "MEDIUMBLOB": {
                "type": "VARBINARY(MAX)",
                "lossy": False,
                "note": ""
            },
            "LONGBLOB": {
                "type": "VARBINARY(MAX)",
                "lossy": False,
                "note": ""
            },
            "JSON": {
                "type": "NVARCHAR(MAX)",
                "lossy": False,
                "note": "MSSQL stores JSON in NVARCHAR(MAX)"
            },
            "ENUM": {
                "type": "NVARCHAR(255)",
                "lossy": False,
                "note": "Needs CHECK constraint for strictness"
            },
            "SET": {
                "type": "NVARCHAR(255)",
                "lossy": True,
                "note": "String representation of SET"
            },
            "BOOLEAN": {
                "type": "BIT",
                "lossy": False,
                "note": ""
            },
            "BOOL": {
                "type": "BIT",
                "lossy": False,
                "note": ""
            }
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
            "PRIMARY": "CLUSTERED INDEX",
            "INDEX": "NONCLUSTERED INDEX",
            "UNIQUE": "UNIQUE NONCLUSTERED INDEX",
            "FULLTEXT": "FULLTEXT INDEX",
            "SPATIAL": "SPATIAL INDEX"
        },
        "pk_strategies": {
            "AUTO_INCREMENT": "IDENTITY"
        },
        "fk_actions": {
            "CASCADE": "CASCADE",
            "SET NULL": "SET NULL",
            "RESTRICT": "NO ACTION",
            "NO ACTION": "NO ACTION"
        }
    },
    "mysql_to_postgres": {
        "datatypes": {
            "INT": {
                "type": "INTEGER",
                "lossy": False,
                "note": ""
            },
            "BIGINT": {
                "type": "BIGINT",
                "lossy": False,
                "note": ""
            },
            "SMALLINT": {
                "type": "SMALLINT",
                "lossy": False,
                "note": ""
            },
            "TINYINT": {
                "type": "SMALLINT",
                "lossy": False,
                "note": "Postgres lacks TINYINT"
            },
            "BIT": {
                "type": "BIT",
                "lossy": False,
                "note": ""
            },
            "FLOAT": {
                "type": "REAL",
                "lossy": False,
                "note": ""
            },
            "DOUBLE": {
                "type": "DOUBLE PRECISION",
                "lossy": False,
                "note": ""
            },
            "DECIMAL": {
                "type": "DECIMAL",
                "lossy": False,
                "note": ""
            },
            "NUMERIC": {
                "type": "NUMERIC",
                "lossy": False,
                "note": ""
            },
            "VARCHAR": {
                "type": "VARCHAR",
                "lossy": False,
                "note": ""
            },
            "TEXT": {
                "type": "TEXT",
                "lossy": False,
                "note": ""
            },
            "LONGTEXT": {
                "type": "TEXT",
                "lossy": False,
                "note": ""
            },
            "CHAR": {
                "type": "CHAR",
                "lossy": False,
                "note": ""
            },
            "DATETIME": {
                "type": "TIMESTAMP",
                "lossy": False,
                "note": ""
            },
            "DATE": {
                "type": "DATE",
                "lossy": False,
                "note": ""
            },
            "TIME": {
                "type": "TIME",
                "lossy": False,
                "note": ""
            },
            "TIMESTAMP": {
                "type": "TIMESTAMP",
                "lossy": False,
                "note": ""
            },
            "VARBINARY": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "BLOB": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "TINYBLOB": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "MEDIUMBLOB": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "LONGBLOB": {
                "type": "BYTEA",
                "lossy": False,
                "note": ""
            },
            "JSON": {
                "type": "JSONB",
                "lossy": False,
                "note": ""
            },
            "ENUM": {
                "type": "VARCHAR",
                "lossy": False,
                "note": "Map to VARCHAR or native ENUM type"
            },
            "SET": {
                "type": "VARCHAR",
                "lossy": True,
                "note": "Mapped to string or array"
            },
            "BOOLEAN": {
                "type": "BOOLEAN",
                "lossy": False,
                "note": ""
            },
            "BOOL": {
                "type": "BOOLEAN",
                "lossy": False,
                "note": ""
            }
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
            "PRIMARY": "PRIMARY KEY",
            "INDEX": "INDEX",
            "UNIQUE": "UNIQUE INDEX",
            "FULLTEXT": "unsupported",
            "SPATIAL": "GIST INDEX"
        },
        "pk_strategies": {
            "AUTO_INCREMENT": "SERIAL"
        },
        "fk_actions": {
            "CASCADE": "CASCADE",
            "SET NULL": "SET NULL",
            "RESTRICT": "RESTRICT",
            "NO ACTION": "NO ACTION"
        }
    },
    "postgres_to_mssql": {
        "datatypes": {
            "INTEGER": {
                "type": "INT",
                "lossy": False,
                "note": ""
            },
            "BIGINT": {
                "type": "BIGINT",
                "lossy": False,
                "note": ""
            },
            "SMALLINT": {
                "type": "SMALLINT",
                "lossy": False,
                "note": ""
            },
            "BOOLEAN": {
                "type": "BIT",
                "lossy": False,
                "note": ""
            },
            "REAL": {
                "type": "REAL",
                "lossy": False,
                "note": ""
            },
            "DOUBLE PRECISION": {
                "type": "FLOAT",
                "lossy": False,
                "note": ""
            },
            "DECIMAL": {
                "type": "DECIMAL",
                "lossy": False,
                "note": ""
            },
            "NUMERIC": {
                "type": "NUMERIC",
                "lossy": False,
                "note": ""
            },
            "VARCHAR": {
                "type": "NVARCHAR",
                "lossy": False,
                "note": ""
            },
            "TEXT": {
                "type": "NVARCHAR(MAX)",
                "lossy": False,
                "note": ""
            },
            "CHAR": {
                "type": "NCHAR",
                "lossy": False,
                "note": ""
            },
            "TIMESTAMP": {
                "type": "DATETIME2",
                "lossy": False,
                "note": ""
            },
            "DATE": {
                "type": "DATE",
                "lossy": False,
                "note": ""
            },
            "TIME": {
                "type": "TIME",
                "lossy": False,
                "note": ""
            },
            "BYTEA": {
                "type": "VARBINARY(MAX)",
                "lossy": False,
                "note": ""
            },
            "JSON": {
                "type": "NVARCHAR(MAX)",
                "lossy": False,
                "note": "MSSQL stores JSON as text"
            },
            "JSONB": {
                "type": "NVARCHAR(MAX)",
                "lossy": False,
                "note": "Binary representation lost"
            },
            "UUID": {
                "type": "UNIQUEIDENTIFIER",
                "lossy": False,
                "note": ""
            },
            "XML": {
                "type": "XML",
                "lossy": False,
                "note": ""
            },
            "MONEY": {
                "type": "MONEY",
                "lossy": False,
                "note": ""
            }
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
            "BTREE": "NONCLUSTERED INDEX",
            "HASH": "NONCLUSTERED INDEX",
            "GIST": "SPATIAL INDEX",
            "GIN": "FULLTEXT INDEX"
        },
        "pk_strategies": {
            "SERIAL": "IDENTITY",
            "BIGSERIAL": "IDENTITY",
            "GENERATED ALWAYS AS IDENTITY": "IDENTITY"
        },
        "fk_actions": {
            "CASCADE": "CASCADE",
            "SET NULL": "SET NULL",
            "SET DEFAULT": "SET DEFAULT",
            "RESTRICT": "NO ACTION",
            "NO ACTION": "NO ACTION"
        }
    },
    "postgres_to_mysql": {
        "datatypes": {
            "INTEGER": {
                "type": "INT",
                "lossy": False,
                "note": ""
            },
            "BIGINT": {
                "type": "BIGINT",
                "lossy": False,
                "note": ""
            },
            "SMALLINT": {
                "type": "SMALLINT",
                "lossy": False,
                "note": ""
            },
            "BOOLEAN": {
                "type": "TINYINT(1)",
                "lossy": False,
                "note": ""
            },
            "REAL": {
                "type": "FLOAT",
                "lossy": False,
                "note": ""
            },
            "DOUBLE PRECISION": {
                "type": "DOUBLE",
                "lossy": False,
                "note": ""
            },
            "DECIMAL": {
                "type": "DECIMAL",
                "lossy": False,
                "note": ""
            },
            "NUMERIC": {
                "type": "NUMERIC",
                "lossy": False,
                "note": ""
            },
            "VARCHAR": {
                "type": "VARCHAR",
                "lossy": False,
                "note": ""
            },
            "TEXT": {
                "type": "TEXT",
                "lossy": False,
                "note": ""
            },
            "CHAR": {
                "type": "CHAR",
                "lossy": False,
                "note": ""
            },
            "TIMESTAMP": {
                "type": "DATETIME",
                "lossy": False,
                "note": ""
            },
            "DATE": {
                "type": "DATE",
                "lossy": False,
                "note": ""
            },
            "TIME": {
                "type": "TIME",
                "lossy": False,
                "note": ""
            },
            "BYTEA": {
                "type": "LONGBLOB",
                "lossy": False,
                "note": ""
            },
            "JSON": {
                "type": "JSON",
                "lossy": False,
                "note": ""
            },
            "JSONB": {
                "type": "JSON",
                "lossy": False,
                "note": "Binary structure lost"
            },
            "UUID": {
                "type": "CHAR(36)",
                "lossy": False,
                "note": ""
            },
            "XML": {
                "type": "LONGTEXT",
                "lossy": False,
                "note": ""
            },
            "MONEY": {
                "type": "DECIMAL(19,4)",
                "lossy": False,
                "note": ""
            }
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
            "GIST": "SPATIAL INDEX",
            "GIN": "FULLTEXT INDEX"
        },
        "pk_strategies": {
            "SERIAL": "AUTO_INCREMENT",
            "BIGSERIAL": "AUTO_INCREMENT",
            "GENERATED ALWAYS AS IDENTITY": "AUTO_INCREMENT"
        },
        "fk_actions": {
            "CASCADE": "CASCADE",
            "SET NULL": "SET NULL",
            "SET DEFAULT": "RESTRICT",
            "RESTRICT": "RESTRICT",
            "NO ACTION": "NO ACTION"
        }
    },
        "oracle_to_mysql": {   'constraints': {   'CHECK': 'CHECK',
                           'DEFAULT': 'DEFAULT',
                           'FOREIGN KEY': 'FOREIGN KEY',
                           'NOT NULL': 'NOT NULL',
                           'PRIMARY KEY': 'PRIMARY KEY',
                           'UNIQUE': 'UNIQUE'},
        'datatypes': {   'BLOB': {'lossy': False, 'note': '', 'type': 'LONGBLOB'},
                         'CLOB': {'lossy': False, 'note': '', 'type': 'LONGTEXT'},
                         'DATE': {'lossy': True, 'note': '', 'type': 'DATETIME'},
                         'NUMBER': {'lossy': True, 'note': '', 'type': 'DECIMAL'},
                         'TIMESTAMP': {   'lossy': False,
                                          'note': '',
                                          'type': 'TIMESTAMP'},
                         'VARCHAR2': {   'lossy': False,
                                         'note': '',
                                         'type': 'VARCHAR'}},
        'fk_actions': {   'CASCADE': 'CASCADE',
                          'NO ACTION': 'NO ACTION',
                          'RESTRICT': 'RESTRICT',
                          'SET NULL': 'SET NULL'},
        'indexes': {'BITMAP': 'INDEX', 'NORMAL': 'INDEX', 'UNIQUE': 'UNIQUE INDEX'},
        'pk_strategies': {'GENERATED ALWAYS AS IDENTITY': 'AUTO_INCREMENT'}},
    "oracle_to_postgres": {   'constraints': {   'CHECK': 'CHECK',
                           'DEFAULT': 'DEFAULT',
                           'FOREIGN KEY': 'FOREIGN KEY',
                           'NOT NULL': 'NOT NULL',
                           'PRIMARY KEY': 'PRIMARY KEY',
                           'UNIQUE': 'UNIQUE'},
        'datatypes': {   'BLOB': {'lossy': False, 'note': '', 'type': 'BYTEA'},
                         'CLOB': {'lossy': False, 'note': '', 'type': 'TEXT'},
                         'DATE': {'lossy': True, 'note': '', 'type': 'TIMESTAMP'},
                         'NUMBER': {'lossy': True, 'note': '', 'type': 'NUMERIC'},
                         'TIMESTAMP': {   'lossy': False,
                                          'note': '',
                                          'type': 'TIMESTAMP'},
                         'VARCHAR2': {   'lossy': False,
                                         'note': '',
                                         'type': 'VARCHAR'}},
        'fk_actions': {   'CASCADE': 'CASCADE',
                          'NO ACTION': 'NO ACTION',
                          'RESTRICT': 'RESTRICT',
                          'SET NULL': 'SET NULL'},
        'indexes': {'BITMAP': 'INDEX', 'NORMAL': 'INDEX', 'UNIQUE': 'UNIQUE INDEX'},
        'pk_strategies': {   'GENERATED ALWAYS AS IDENTITY': 'GENERATED ALWAYS AS '
                                                             'IDENTITY'}},
    "oracle_to_mssql": {   'constraints': {   'CHECK': 'CHECK',
                           'DEFAULT': 'DEFAULT',
                           'FOREIGN KEY': 'FOREIGN KEY',
                           'NOT NULL': 'NOT NULL',
                           'PRIMARY KEY': 'PRIMARY KEY',
                           'UNIQUE': 'UNIQUE'},
        'datatypes': {   'BLOB': {   'lossy': False,
                                     'note': '',
                                     'type': 'VARBINARY(MAX)'},
                         'CLOB': {   'lossy': False,
                                     'note': '',
                                     'type': 'NVARCHAR(MAX)'},
                         'DATE': {'lossy': True, 'note': '', 'type': 'DATETIME2'},
                         'NUMBER': {'lossy': True, 'note': '', 'type': 'DECIMAL'},
                         'TIMESTAMP': {   'lossy': False,
                                          'note': '',
                                          'type': 'DATETIME2'},
                         'VARCHAR2': {   'lossy': False,
                                         'note': '',
                                         'type': 'NVARCHAR'}},
        'fk_actions': {   'CASCADE': 'CASCADE',
                          'NO ACTION': 'NO ACTION',
                          'RESTRICT': 'RESTRICT',
                          'SET NULL': 'SET NULL'},
        'indexes': {'BITMAP': 'INDEX', 'NORMAL': 'INDEX', 'UNIQUE': 'UNIQUE INDEX'},
        'pk_strategies': {'GENERATED ALWAYS AS IDENTITY': 'IDENTITY'}},
    "mysql_to_oracle": {   'constraints': {   'CHECK': 'CHECK',
                           'DEFAULT': 'DEFAULT',
                           'FOREIGN KEY': 'FOREIGN KEY',
                           'NOT NULL': 'NOT NULL',
                           'PRIMARY KEY': 'PRIMARY KEY',
                           'UNIQUE': 'UNIQUE'},
        'datatypes': {   'BOOLEAN': {   'lossy': True,
                                        'note': '',
                                        'type': 'NUMBER(1)'},
                         'DATE': {'lossy': False, 'note': '', 'type': 'DATE'},
                         'DATETIME': {   'lossy': False,
                                         'note': '',
                                         'type': 'TIMESTAMP'},
                         'INT': {'lossy': False, 'note': '', 'type': 'NUMBER'},
                         'TEXT': {'lossy': False, 'note': '', 'type': 'CLOB'},
                         'VARCHAR': {   'lossy': False,
                                        'note': '',
                                        'type': 'VARCHAR2'}},
        'fk_actions': {   'CASCADE': 'CASCADE',
                          'NO ACTION': 'NO ACTION',
                          'RESTRICT': 'RESTRICT',
                          'SET NULL': 'SET NULL'},
        'indexes': {   'INDEX': 'NORMAL',
                       'PRIMARY KEY': 'NORMAL',
                       'UNIQUE INDEX': 'UNIQUE'},
        'pk_strategies': {'AUTO_INCREMENT': 'GENERATED ALWAYS AS IDENTITY'}},
    "postgres_to_oracle": {   'constraints': {   'CHECK': 'CHECK',
                           'DEFAULT': 'DEFAULT',
                           'FOREIGN KEY': 'FOREIGN KEY',
                           'NOT NULL': 'NOT NULL',
                           'PRIMARY KEY': 'PRIMARY KEY',
                           'UNIQUE': 'UNIQUE'},
        'datatypes': {   'BOOLEAN': {   'lossy': True,
                                        'note': '',
                                        'type': 'NUMBER(1)'},
                         'DATE': {'lossy': False, 'note': '', 'type': 'DATE'},
                         'INTEGER': {'lossy': False, 'note': '', 'type': 'NUMBER'},
                         'TEXT': {'lossy': False, 'note': '', 'type': 'CLOB'},
                         'TIMESTAMP': {   'lossy': False,
                                          'note': '',
                                          'type': 'TIMESTAMP'},
                         'VARCHAR': {   'lossy': False,
                                        'note': '',
                                        'type': 'VARCHAR2'}},
        'fk_actions': {   'CASCADE': 'CASCADE',
                          'NO ACTION': 'NO ACTION',
                          'RESTRICT': 'RESTRICT',
                          'SET NULL': 'SET NULL'},
        'indexes': {   'INDEX': 'NORMAL',
                       'PRIMARY KEY': 'NORMAL',
                       'UNIQUE INDEX': 'UNIQUE'},
        'pk_strategies': {   'GENERATED ALWAYS AS IDENTITY': 'GENERATED ALWAYS AS '
                                                             'IDENTITY',
                             'SERIAL': 'GENERATED ALWAYS AS IDENTITY'}},
    "mssql_to_oracle": {   'constraints': {   'CHECK': 'CHECK',
                           'DEFAULT': 'DEFAULT',
                           'FOREIGN KEY': 'FOREIGN KEY',
                           'NOT NULL': 'NOT NULL',
                           'PRIMARY KEY': 'PRIMARY KEY',
                           'UNIQUE': 'UNIQUE'},
        'datatypes': {   'BIT': {'lossy': False, 'note': '', 'type': 'NUMBER(1)'},
                         'BOOLEAN': {   'lossy': True,
                                        'note': '',
                                        'type': 'NUMBER(1)'},
                         'DATE': {'lossy': False, 'note': '', 'type': 'DATE'},
                         'DATETIME': {   'lossy': False,
                                         'note': '',
                                         'type': 'TIMESTAMP'},
                         'INT': {'lossy': False, 'note': '', 'type': 'NUMBER'},
                         'NVARCHAR': {   'lossy': False,
                                         'note': '',
                                         'type': 'VARCHAR2'},
                         'VARCHAR': {   'lossy': False,
                                        'note': '',
                                        'type': 'VARCHAR2'}},
        'fk_actions': {   'CASCADE': 'CASCADE',
                          'NO ACTION': 'NO ACTION',
                          'RESTRICT': 'RESTRICT',
                          'SET NULL': 'SET NULL'},
        'indexes': {   'INDEX': 'NORMAL',
                       'PRIMARY KEY': 'NORMAL',
                       'UNIQUE INDEX': 'UNIQUE'},
        'pk_strategies': {'IDENTITY': 'GENERATED ALWAYS AS IDENTITY'}}
}
