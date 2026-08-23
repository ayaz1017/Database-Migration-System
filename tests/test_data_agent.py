import pytest
from unittest.mock import Mock, call
from backend.execution.transaction_manager import TransactionManager

def test_transaction_manager_postgres_privilege_check():
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock superuser check returning 'off', but setting role succeeding
    mock_cursor.fetchone.return_value = ('off',)
    
    tm = TransactionManager(mock_conn, 'postgres', ['a', 'b'])
    assert tm.check_privileges() is True
    
    mock_cursor.execute.assert_any_call("SET session_replication_role = 'replica'")
    mock_cursor.execute.assert_any_call("SET session_replication_role = 'origin'")

def test_transaction_manager_postgres_privilege_fail():
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock failure setting role
    mock_cursor.fetchone.return_value = ('off',)
    mock_cursor.execute.side_effect = [
        None, # For SELECT current_setting
        Exception("Permission denied") # For SET session_replication_role
    ]
    
    tm = TransactionManager(mock_conn, 'postgres', ['a'])
    assert tm.check_privileges() is False
    mock_conn.rollback.assert_called_once()

def test_transaction_manager_mysql_privilege_check():
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    
    mock_cursor.fetchall.return_value = [("GRANT SELECT ON *.* TO 'user'",), ("GRANT SUPER ON *.* TO 'user'",)]
    
    tm = TransactionManager(mock_conn, 'mysql', ['a'])
    assert tm.check_privileges() is True
    
def test_transaction_manager_mysql_privilege_fail():
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    
    mock_cursor.fetchall.return_value = [("GRANT SELECT ON *.* TO 'user'",)]
    
    tm = TransactionManager(mock_conn, 'mysql', ['a'])
    assert tm.check_privileges() is False

def test_transaction_manager_rollback_on_failure():
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    
    tm = TransactionManager(mock_conn, 'mssql', ['a', 'b'])
    
    # Disable constraints
    tm.disable_constraints()
    mock_cursor.execute.assert_any_call("ALTER TABLE a NOCHECK CONSTRAINT ALL")
    mock_cursor.execute.assert_any_call("ALTER TABLE b NOCHECK CONSTRAINT ALL")
    
    # Simulate an error causing a rollback
    tm.rollback()
    mock_conn.rollback.assert_called_once()
    
    # It should explicitly re-enable constraints on rollback
    mock_cursor.execute.assert_any_call("ALTER TABLE a CHECK CONSTRAINT ALL")
    mock_cursor.execute.assert_any_call("ALTER TABLE b CHECK CONSTRAINT ALL")

def test_transaction_manager_bulk_insert_postgres():
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    
    tm = TransactionManager(mock_conn, 'postgres', ['a'])
    rows = [{"id": 1, "val": "test"}]
    
    inserted = tm.bulk_insert_chunk('a', rows)
    assert inserted == 1
    assert mock_cursor.copy_expert.called
