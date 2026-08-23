import os
import pytest
from backend.connectors.oracle import OracleConnector

# Skip all tests in this module if Oracle test config is not provided
pytestmark = pytest.mark.skipif(
    not os.getenv("ORACLE_TEST_DSN"),
    reason="Oracle XE not configured"
)

def test_oracle_live_connection():
    dsn = os.getenv("ORACLE_TEST_DSN")
    user = os.getenv("ORACLE_TEST_USER")
    password = os.getenv("ORACLE_TEST_PASSWORD")
    
    # Parse DSN (assuming host:port/service_name format)
    parts = dsn.split("/")
    host_port = parts[0].split(":")
    host = host_port[0]
    port = int(host_port[1])
    service_name = parts[1]
    
    connector = OracleConnector(host, port, service_name, user, password)
    result = connector.test_connection()
    
    assert result["status"] == "success", f"Connection failed: {result.get('message')}"
    
    # Run a simple query
    res = connector.execute_query("SELECT 1 AS VAL FROM DUAL")
    assert len(res) == 1
    assert res[0]["val"] == 1
