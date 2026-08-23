import re

with open(r"tests\test_discovery_service.py", "a", encoding="utf-8") as f:
    f.write("""

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
""")

print("tests/test_discovery_service.py patched successfully.")
