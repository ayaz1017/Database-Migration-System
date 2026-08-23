import pytest
from unittest.mock import patch, MagicMock
from backend.execution.oracle_execution_engine import OracleExecutionEngine
from backend.config.migration_matrix import MIGRATION_MATRIX
from backend.agents.validation_agent import ValidationAgent

def test_oracle_matrix_keys_exist():
    assert "oracle_to_mysql" in MIGRATION_MATRIX
    assert "oracle_to_postgres" in MIGRATION_MATRIX
    assert "oracle_to_mssql" in MIGRATION_MATRIX
    assert "mysql_to_oracle" in MIGRATION_MATRIX
    assert "postgres_to_oracle" in MIGRATION_MATRIX
    assert "mssql_to_oracle" in MIGRATION_MATRIX

@patch("backend.execution.oracle_execution_engine.oracledb.connect")
def test_oracle_execution_engine_get_row_count(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [42]

    engine = OracleExecutionEngine("localhost", 1521, "user", "pass", "XEPDB1")
    count = engine.get_row_count("students")

    assert count == 42
    mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM students")

@patch("backend.execution.oracle_execution_engine.oracledb.connect")
def test_oracle_execution_engine_stream_table(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    mock_cursor.description = [("ID",), ("NAME",)]
    mock_cursor.fetchmany.side_effect = [
        [(1, "Alice"), (2, "Bob")],
        []
    ]

    engine = OracleExecutionEngine("localhost", 1521, "user", "pass", "XEPDB1")
    chunks = list(engine.stream_table("students", chunk_size=2))

    assert len(chunks) == 1
    assert chunks[0] == [{"ID": 1, "NAME": "Alice"}, {"ID": 2, "NAME": "Bob"}]

@patch("backend.execution.oracle_execution_engine.oracledb.connect")
def test_oracle_execution_engine_bulk_insert(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.rowcount = 2

    engine = OracleExecutionEngine("localhost", 1521, "user", "pass", "XEPDB1")
    rows = [{"ID": 1, "NAME": "Alice"}, {"ID": 2, "NAME": "Bob"}]
    inserted = engine.bulk_insert("students", rows)

    assert inserted == 2
    mock_cursor.executemany.assert_called_once()
    sql_call = mock_cursor.executemany.call_args[0][0]
    assert "INSERT INTO students" in sql_call
    assert ":1" in sql_call and ":2" in sql_call

def test_validation_agent_oracle_checksum_query():
    agent = ValidationAgent()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ["123456789"]

    checksum = agent._get_checksum(mock_conn, "students", ["ID", "NAME"], "ID", "oracle")
    
    assert checksum == "123456789"
    mock_cursor.execute.assert_called_once()
    query = mock_cursor.execute.call_args[0][0]
    assert "ORA_HASH" in query
    assert "NVL(CAST(ID AS VARCHAR2(4000)), '')" in query
    assert "NVL(CAST(NAME AS VARCHAR2(4000)), '')" in query
