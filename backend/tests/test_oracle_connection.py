import pytest
from unittest.mock import MagicMock
from backend.connectors.oracle import OracleConnector

def test_oracle_connector_success(mocker):
    mock_oracledb = mocker.patch("backend.connectors.oracle.oracledb")
    
    mock_conn = MagicMock()
    mock_conn.version = "19c Enterprise Edition"
    mock_cursor = MagicMock()
    mock_oracledb.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Privilege check
    mock_cursor.fetchone.return_value = ("SELECT ANY TABLE",)
    
    connector = OracleConnector("localhost", 1521, "XEPDB1", "sys", "sys")
    result = connector.test_connection()
    
    assert result["status"] == "success"
    assert "19c" in result["message"]
    mock_oracledb.connect.assert_called_once()
    assert mock_cursor.execute.call_count == 1

def test_oracle_connector_missing_privilege(mocker):
    mock_oracledb = mocker.patch("backend.connectors.oracle.oracledb")
    
    mock_conn = MagicMock()
    mock_conn.version = "19c Enterprise Edition"
    mock_cursor = MagicMock()
    mock_oracledb.connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    
    # Privilege check fails
    mock_cursor.fetchone.return_value = None
    
    connector = OracleConnector("localhost", 1521, "XEPDB1", "user", "pw")
    result = connector.test_connection()
    
    assert result["status"] == "error"
    assert "missing required 'SELECT ANY TABLE' privilege" in result["message"]
