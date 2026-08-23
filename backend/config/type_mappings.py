# Type mappings from MSSQL -> PostgreSQL -> MySQL
TYPE_MAPPINGS = {
    "MSSQL": {
        "INT": {"PostgreSQL": "INTEGER", "MySQL": "INT"},
        "BIGINT": {"PostgreSQL": "BIGINT", "MySQL": "BIGINT"},
        "NVARCHAR": {"PostgreSQL": "VARCHAR", "MySQL": "VARCHAR"},
        "TEXT": {"PostgreSQL": "TEXT", "MySQL": "LONGTEXT"},
        "DATETIME": {"PostgreSQL": "TIMESTAMP", "MySQL": "DATETIME"},
        "BIT": {"PostgreSQL": "BOOLEAN", "MySQL": "TINYINT(1)"},
        "FLOAT": {"PostgreSQL": "DOUBLE PRECISION", "MySQL": "DOUBLE"},
        "DECIMAL": {"PostgreSQL": "NUMERIC", "MySQL": "DECIMAL"},
        "UNIQUEIDENTIFIER": {"PostgreSQL": "UUID", "MySQL": "CHAR(36)"},
        "VARBINARY": {"PostgreSQL": "BYTEA", "MySQL": "LONGBLOB"},
        "MONEY": {"PostgreSQL": "NUMERIC(19,4)", "MySQL": "DECIMAL(19,4)"},
        "IDENTITY": {"PostgreSQL": "SERIAL", "MySQL": "AUTO_INCREMENT"},
    }
}


def get_mapping(source_db: str, target_db: str, type_name: str) -> str:
    # Basic lookup
    source_db_upper = source_db.upper()
    if source_db_upper in TYPE_MAPPINGS:
        if type_name.upper() in TYPE_MAPPINGS[source_db_upper]:
            target_map = TYPE_MAPPINGS[source_db_upper][type_name.upper()]
            # Find the closest match if target_db is specified
            for k, v in target_map.items():
                if target_db.upper() == k.upper():
                    return v
    return type_name  # Fallback
