# pyrefly: ignore [missing-import]
import pytest
import json
from backend.services.drift_service import capture_schema_snapshot, compare_schemas, _normalize_schema, _hash_schema
from backend.main import ConnectionConfig
from backend.database import get_db

@pytest.fixture
def mock_schema():
    return {
        "tables": [
            {
                "name": "customers",
                "columns": [
                    {"name": "id", "type": "INT", "nullable": False, "default": None},
                    {"name": "email", "type": "VARCHAR", "nullable": False, "default": None},
                    {"name": "status", "type": "VARCHAR", "nullable": True, "default": "'active'"}
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
                "indexes": [{"name": "idx_email", "columns": ["email"], "unique": True, "type": "BTREE"}],
                "check_constraints": [],
                "row_count": 100
            }
        ]
    }

def test_normalize_schema(mock_schema):
    normalized = _normalize_schema(mock_schema)
    assert "customers" in normalized["tables"]
    cust = normalized["tables"]["customers"]
    
    assert cust["columns"]["id"]["type"] == "INT"
    assert cust["columns"]["id"]["is_pk"] is True
    assert cust["columns"]["id"]["is_fk"] is False
    assert cust["columns"]["status"]["default"] == "'active'"
    
    assert "idx_email" in cust["indexes"]
    assert cust["indexes"]["idx_email"]["unique"] is True

def test_hash_schema_deterministic(mock_schema):
    norm1 = _normalize_schema(mock_schema)
    norm2 = _normalize_schema(mock_schema)
    assert _hash_schema(norm1) == _hash_schema(norm2)

def test_capture_snapshot_db(monkeypatch, mock_schema):
    from backend.main import init_db
    init_db()
    
    class MockDiscovery:
        def connect_and_discover(self, **kwargs):
            return mock_schema
            
    monkeypatch.setattr("backend.services.drift_service.DiscoveryService", MockDiscovery)
    
    config = ConnectionConfig(
        db_type="postgres", host="localhost", port=5432, username="user", password="pwd", database="db"
    )
    
    job_id = "test_job_123"
    org_id = "test_org"
    
    # Run capture
    capture_schema_snapshot(job_id, org_id, config)
    
    # Verify DB
    with get_db(row_factory=True) as (conn, cursor):
        cursor.execute("SELECT * FROM schema_snapshots WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        
    assert row is not None
    assert row["source_db_type"] == "postgres"
    
    snapshot_json = json.loads(row["snapshot_json"])
    assert "customers" in snapshot_json["tables"]
    print("Snapshot JSON captured successfully:", json.dumps(snapshot_json, indent=2))
    
def test_compare_schemas_no_drift(mock_schema):
    norm1 = _normalize_schema(mock_schema)
    snap1 = {"tables": norm1["tables"], "schema_version": _hash_schema(norm1)}
    
    res = compare_schemas(snap1, snap1)
    assert res.drift_detected is False
    assert res.overall_severity == "none"

def test_compare_schemas_column_added(mock_schema):
    norm_base = _normalize_schema(mock_schema)
    snap_base = {"tables": norm_base["tables"], "schema_version": _hash_schema(norm_base)}
    
    # Modify mock schema
    modified_schema = json.loads(json.dumps(mock_schema))
    modified_schema["tables"][0]["columns"].append(
        {"name": "new_col", "type": "INT", "nullable": True, "default": None}
    )
    
    norm_curr = _normalize_schema(modified_schema)
    snap_curr = {"tables": norm_curr["tables"], "schema_version": _hash_schema(norm_curr)}
    
    res = compare_schemas(snap_base, snap_curr)
    
    assert res.drift_detected is True
    assert res.overall_severity == "low"  
    assert len(res.changes) == 1
    assert res.changes[0].change_type == "column_added"
    assert res.changes[0].object_name == "new_col"
    
def test_compare_schemas_column_removed(mock_schema):
    norm_base = _normalize_schema(mock_schema)
    snap_base = {"tables": norm_base["tables"], "schema_version": _hash_schema(norm_base)}
    
    modified_schema = json.loads(json.dumps(mock_schema))
    modified_schema["tables"][0]["columns"].pop(1) 
    
    norm_curr = _normalize_schema(modified_schema)
    snap_curr = {"tables": norm_curr["tables"], "schema_version": _hash_schema(norm_curr)}
    
    res = compare_schemas(snap_base, snap_curr)
    
    assert res.drift_detected is True
    assert res.overall_severity == "high" # column removed is high severity
    assert res.changes[0].change_type == "column_removed"
    
def test_compare_schemas_type_changed(mock_schema):
    norm_base = _normalize_schema(mock_schema)
    snap_base = {"tables": norm_base["tables"], "schema_version": _hash_schema(norm_base)}
    
    modified_schema = json.loads(json.dumps(mock_schema))
    modified_schema["tables"][0]["columns"][0]["type"] = "BIGINT" # id changed to BIGINT
    
    norm_curr = _normalize_schema(modified_schema)
    snap_curr = {"tables": norm_curr["tables"], "schema_version": _hash_schema(norm_curr)}
    
    res = compare_schemas(snap_base, snap_curr)
    
    assert res.drift_detected is True
    assert res.overall_severity == "medium"
    assert res.changes[0].change_type == "column_type_changed"
