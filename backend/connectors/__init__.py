from .mssql import MSSQLConnector
from .mysql import MySQLConnector
from .postgres import PostgresConnector


def get_connector(db_type: str, host, port, database, user, password):
    db_type = db_type.lower()
    if db_type == "mssql":
        return MSSQLConnector(host, port, database, user, password)
    elif db_type == "mysql":
        return MySQLConnector(host, port, database, user, password)
    elif db_type == "postgresql":
        return PostgresConnector(host, port, database, user, password)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
