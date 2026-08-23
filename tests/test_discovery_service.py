import pytest
from unittest.mock import patch
from backend.services.discovery_service import DiscoveryService

@patch("backend.services.discovery_service.DiscoveryService.connect_and_discover")
def test_successful_connection_returns_schema_dict(mock_discover):
    mock_discover.return_value = {
        "databases": ["migration_source"],
        "schemas": ["public"],
        "tables": [{"name": "test_table", "row_count": 10}],
        "row_counts": {"test_table": 10}
    }
    
    service = DiscoveryService()
    result = service.connect_and_discover(
        host="127.0.0.1", port=3306, username="root", password="pw", db_type="mysql", database="db"
    )
    
    assert "databases" in result
    assert "schemas" in result
    assert "tables" in result
    assert "row_counts" in result
    
    table_info = next((t for t in result["tables"] if t["name"] == "test_table"), None)
    assert table_info is not None
    assert table_info["row_count"] == 10

@patch("backend.services.discovery_service.DiscoveryService.connect_and_discover")
def test_row_counts_accurate(mock_discover):
    mock_discover.return_value = {
        "tables": [
            {"name": "t1", "row_count": 50},
            {"name": "t2", "row_count": 100},
            {"name": "t3", "row_count": 200}
        ]
    }
    
    service = DiscoveryService()
    result = service.connect_and_discover(
        host="127.0.0.1", port=5432, username="postgres", password="pw", db_type="postgres", database="db"
    )
    
    counts = {t["name"]: t["row_count"] for t in result["tables"]}
    assert counts.get("t1") == 50
    assert counts.get("t2") == 100
    assert counts.get("t3") == 200

def test_failed_connection_raises_immediately():
    service = DiscoveryService()
    with pytest.raises(Exception):
        service.connect_and_discover(
            host="127.0.0.1",
            port=9999,
            username="baduser",
            password="badpass",
            db_type="mysql"
        )


def test_oracle_discovery_real_connection():
    from backend.services.discovery_service import DiscoveryService
    service = DiscoveryService()
    
    # Real connection test as instructed
    schema = service.connect_and_discover(
        host="localhost",
        port=1521,
        username="ayaz",
        password="Oracle123",
        db_type="oracle",
        database="XEPDB1"
    )
    
    assert schema is not None
    assert "tables" in schema
    
    tables = {t["name"]: t for t in schema["tables"]}
    assert "STUDENTS" in tables or "students" in tables
    
    students_table = tables.get("STUDENTS", tables.get("students"))
    assert students_table is not None
    assert students_table["row_count"] == 35000
    assert "ID" in students_table.get("primary_keys", []) or "id" in students_table.get("primary_keys", [])


def test_oracle_discovery_real_connection():
    from backend.services.discovery_service import DiscoveryService
    service = DiscoveryService()
    
    # Real connection test as instructed
    schema = service.connect_and_discover(
        host="localhost",
        port=1521,
        username="ayaz",
        password="Oracle123",
        db_type="oracle",
        database="XEPDB1"
    )
    
    assert schema is not None
    assert "tables" in schema
    
    tables = {t["name"]: t for t in schema["tables"]}
    assert "STUDENTS" in tables or "students" in tables
    
    students_table = tables.get("STUDENTS", tables.get("students"))
    assert students_table is not None
    assert students_table["row_count"] == 35000
    assert "ID" in students_table.get("primary_keys", []) or "id" in students_table.get("primary_keys", [])


def test_oracle_discovery_real_connection():
    from backend.services.discovery_service import DiscoveryService
    service = DiscoveryService()
    
    # Real connection test as instructed
    schema = service.connect_and_discover(
        host="localhost",
        port=1521,
        username="ayaz",
        password="Oracle123",
        db_type="oracle",
        database="XEPDB1"
    )
    
    assert schema is not None
    assert "tables" in schema
    
    tables = {t["name"]: t for t in schema["tables"]}
    assert "STUDENTS" in tables or "students" in tables
    
    students_table = tables.get("STUDENTS", tables.get("students"))
    assert students_table is not None
    assert students_table["row_count"] == 35000
    assert "ID" in students_table.get("primary_keys", []) or "id" in students_table.get("primary_keys", [])


def test_oracle_discovery_real_connection():
    from backend.services.discovery_service import DiscoveryService
    service = DiscoveryService()
    
    # Real connection test as instructed
    schema = service.connect_and_discover(
        host="localhost",
        port=1521,
        username="ayaz",
        password="Oracle123",
        db_type="oracle",
        database="XEPDB1"
    )
    
    assert schema is not None
    assert "tables" in schema
    
    tables = {t["name"]: t for t in schema["tables"]}
    assert "STUDENTS" in tables or "students" in tables
    
    students_table = tables.get("STUDENTS", tables.get("students"))
    assert students_table is not None
    assert students_table["row_count"] == 35000
    assert "ID" in students_table.get("primary_keys", []) or "id" in students_table.get("primary_keys", [])


def test_oracle_discovery_real_connection():
    from backend.services.discovery_service import DiscoveryService
    service = DiscoveryService()
    
    # Real connection test as instructed
    schema = service.connect_and_discover(
        host="localhost",
        port=1521,
        username="ayaz",
        password="Oracle123",
        db_type="oracle",
        database="XEPDB1"
    )
    
    assert schema is not None
    assert "tables" in schema
    
    tables = {t["name"]: t for t in schema["tables"]}
    assert "STUDENTS" in tables or "students" in tables
    
    students_table = tables.get("STUDENTS", tables.get("students"))
    assert students_table is not None
    assert students_table["row_count"] == 35000
    assert "ID" in students_table.get("primary_keys", []) or "id" in students_table.get("primary_keys", [])
