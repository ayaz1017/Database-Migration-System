import json
import hashlib
import uuid
import datetime
from typing import Any, Dict

from backend.database import get_db
from backend.services.discovery_service import DiscoveryService
from backend.main import ConnectionConfig
from backend.models import DriftResult, DriftChange

def _normalize_schema(raw_schema: dict) -> dict:
    """
    Transforms the raw list-based output from DiscoveryService into 
    the dictionary-based snapshot format required for drift detection.
    """
    normalized = {"tables": {}}
    for table in raw_schema.get("tables", []):
        table_name = table["name"]
        
        # Columns
        columns = {}
        for col in table.get("columns", []):
            col_name = col["name"]
            columns[col_name] = {
                "type": col.get("type", ""),
                "nullable": col.get("nullable", True),
                "default": str(col.get("default")) if col.get("default") is not None else None,
                "is_pk": col_name in table.get("primary_keys", []),
                "is_fk": any(fk["column"] == col_name for fk in table.get("foreign_keys", [])),
                "fk_references": next((fk["references_table"] for fk in table.get("foreign_keys", []) if fk["column"] == col_name), None)
            }
            
        # Indexes
        indexes = {}
        for idx in table.get("indexes", []):
            idx_name = idx["name"]
            indexes[idx_name] = {
                "columns": idx.get("columns", []),
                "unique": idx.get("unique", False),
                "type": idx.get("type", "")
            }
            
        # Constraints (Combining FKs and Checks for now, PK is covered in columns)
        constraints = {}
        for fk in table.get("foreign_keys", []):
            constraints[f"fk_{table_name}_{fk['column']}"] = {
                "type": "FOREIGN KEY",
                "columns": [fk["column"]],
                "references": f"{fk['references_table']}.{fk['references_column']}"
            }
            
        normalized["tables"][table_name] = {
            "columns": columns,
            "indexes": indexes,
            "constraints": constraints
        }
        
    return normalized

def _hash_schema(normalized: dict) -> str:
    """Generate a deterministic hash of the schema."""
    schema_str = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(schema_str.encode('utf-8')).hexdigest()

def capture_schema_snapshot(job_id: str, org_id: str, source_config: ConnectionConfig):
    """
    Captures current source schema state and stores it as a baseline snapshot.
    """
    discovery = DiscoveryService()
    raw_schema = discovery.connect_and_discover(
        host=source_config.host,
        port=source_config.port,
        username=source_config.username,
        password=source_config.password,
        db_type=source_config.db_type,
        database=source_config.database
    )
    
    normalized = _normalize_schema(raw_schema)
    schema_version = _hash_schema(normalized)
    
    snapshot_json = {
        "tables": normalized["tables"],
        "schema_version": schema_version,
        "captured_at": datetime.datetime.now().isoformat()
    }
    
    tables_count = len(normalized["tables"])
    columns_count = sum(len(t["columns"]) for t in normalized["tables"].values())
    
    snapshot_id = str(uuid.uuid4())
    
    with get_db() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO schema_snapshots 
            (id, job_id, org_id, source_db_type, source_host, source_database, snapshot_json, taken_at, tables_count, columns_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_id, 
                job_id, 
                org_id, 
                source_config.db_type, 
                source_config.host, 
                source_config.database, 
                json.dumps(snapshot_json), 
                snapshot_json["captured_at"],
                tables_count,
                columns_count
            )
        )
        
def compare_schemas(baseline: dict, current: dict) -> DriftResult:
    """
    Compares a baseline snapshot with the current schema.
    """
    base_version = baseline.get("schema_version")
    curr_version = current.get("schema_version")
    
    if base_version and curr_version and base_version == curr_version:
        return DriftResult(
            drift_detected=False,
            overall_severity="none",
            changes=[],
            tables_added=[],
            tables_removed=[],
            schema_version_changed=False,
            summary="No drift detected."
        )
        
    changes = []
    base_tables = baseline.get("tables", {})
    curr_tables = current.get("tables", {})
    
    tables_added = []
    tables_removed = []
    
    # Check for removed tables
    for t_name, t_base in base_tables.items():
        if t_name not in curr_tables:
            tables_removed.append(t_name)
            changes.append(DriftChange(
                change_type="table_removed",
                table_name=t_name,
                object_name=t_name,
                severity="high",
                description=f"Table '{t_name}' was removed."
            ))
            
    # Check for added and modified tables
    for t_name, t_curr in curr_tables.items():
        if t_name not in base_tables:
            tables_added.append(t_name)
            changes.append(DriftChange(
                change_type="table_added",
                table_name=t_name,
                object_name=t_name,
                severity="medium",
                description=f"Table '{t_name}' was added."
            ))
            continue
            
        t_base = base_tables[t_name]
        
        # Check columns
        base_cols = t_base.get("columns", {})
        curr_cols = t_curr.get("columns", {})
        
        for c_name, c_base in base_cols.items():
            if c_name not in curr_cols:
                changes.append(DriftChange(
                    change_type="column_removed",
                    table_name=t_name,
                    object_name=c_name,
                    severity="high",
                    description=f"Column '{c_name}' removed from table '{t_name}'."
                ))
            else:
                c_curr = curr_cols[c_name]
                if c_base["type"] != c_curr["type"]:
                    changes.append(DriftChange(
                        change_type="column_type_changed",
                        table_name=t_name,
                        object_name=c_name,
                        old_value=c_base["type"],
                        new_value=c_curr["type"],
                        severity="medium",
                        description=f"Column '{c_name}' type changed from {c_base['type']} to {c_curr['type']}."
                    ))
                if c_base["nullable"] != c_curr["nullable"]:
                    changes.append(DriftChange(
                        change_type="column_nullable_changed",
                        table_name=t_name,
                        object_name=c_name,
                        old_value=str(c_base["nullable"]),
                        new_value=str(c_curr["nullable"]),
                        severity="low" if c_curr["nullable"] else "medium",
                        description=f"Column '{c_name}' nullable changed to {c_curr['nullable']}."
                    ))
                if c_base["default"] != c_curr["default"]:
                    changes.append(DriftChange(
                        change_type="column_default_changed",
                        table_name=t_name,
                        object_name=c_name,
                        old_value=str(c_base["default"]),
                        new_value=str(c_curr["default"]),
                        severity="low",
                        description=f"Column '{c_name}' default value changed."
                    ))
                    
        for c_name, c_curr in curr_cols.items():
            if c_name not in base_cols:
                changes.append(DriftChange(
                    change_type="column_added",
                    table_name=t_name,
                    object_name=c_name,
                    severity="medium" if not c_curr["nullable"] and not c_curr["default"] else "low",
                    description=f"Column '{c_name}' added to table '{t_name}'."
                ))
                
        # Check Indexes
        base_idxs = t_base.get("indexes", {})
        curr_idxs = t_curr.get("indexes", {})
        for idx_name in base_idxs:
            if idx_name not in curr_idxs:
                changes.append(DriftChange(
                    change_type="index_removed", table_name=t_name, object_name=idx_name, severity="low", description=f"Index '{idx_name}' removed."
                ))
        for idx_name in curr_idxs:
            if idx_name not in base_idxs:
                changes.append(DriftChange(
                    change_type="index_added", table_name=t_name, object_name=idx_name, severity="low", description=f"Index '{idx_name}' added."
                ))
                
        # Constraints (simplified)
        base_cons = t_base.get("constraints", {})
        curr_cons = t_curr.get("constraints", {})
        for con_name in base_cons:
            if con_name not in curr_cons:
                changes.append(DriftChange(
                    change_type="constraint_removed", table_name=t_name, object_name=con_name, severity="medium", description=f"Constraint '{con_name}' removed."
                ))
        for con_name in curr_cons:
            if con_name not in base_cons:
                changes.append(DriftChange(
                    change_type="constraint_added", table_name=t_name, object_name=con_name, severity="medium", description=f"Constraint '{con_name}' added."
                ))
                
    overall_severity = "none"
    if changes:
        if any(c.severity == "high" for c in changes):
            overall_severity = "high"
        elif any(c.severity == "medium" for c in changes):
            overall_severity = "medium"
        else:
            overall_severity = "low"
            
    summary = f"{len(changes)} changes detected" if changes else "No drift detected."
    
    return DriftResult(
        drift_detected=len(changes) > 0,
        overall_severity=overall_severity,
        changes=changes,
        tables_added=tables_added,
        tables_removed=tables_removed,
        schema_version_changed=True,
        summary=summary
    )
