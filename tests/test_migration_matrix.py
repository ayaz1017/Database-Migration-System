import pytest
from unittest.mock import patch, MagicMock
from backend.config.migration_matrix import MIGRATION_MATRIX
from backend.agents.schema_agent import SchemaAgent

def test_mssql_to_mysql_all_types_mapped():
    datatypes = MIGRATION_MATRIX["mssql_to_mysql"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)
        assert len(v["type"].strip()) > 0

def test_mssql_to_postgres_all_types_mapped():
    datatypes = MIGRATION_MATRIX["mssql_to_postgres"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)
        assert len(v["type"].strip()) > 0

def test_mysql_to_postgres_all_types_mapped():
    datatypes = MIGRATION_MATRIX["mysql_to_postgres"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)
        assert len(v["type"].strip()) > 0

def test_lossy_flags_present():
    assert MIGRATION_MATRIX["mssql_to_mysql"]["datatypes"]["NTEXT"]["lossy"] is True
    assert MIGRATION_MATRIX["mssql_to_mysql"]["datatypes"]["MONEY"]["lossy"] is True
    assert MIGRATION_MATRIX["mssql_to_mysql"]["datatypes"]["SMALLMONEY"]["lossy"] is True
    assert MIGRATION_MATRIX["mssql_to_mysql"]["datatypes"]["IMAGE"]["lossy"] is True
    assert MIGRATION_MATRIX["mssql_to_mysql"]["datatypes"]["XML"]["lossy"] is True

@patch("backend.agents.schema_agent.LLMService.generate_response")
def test_generate_ddl_never_calls_llm(mock_generate):
    agent = SchemaAgent()
    
    source_schema = {
        "tables": [
            {
                "name": "users",
                "columns": [
                    {"name": "id", "type": "INT", "nullable": False},
                    {"name": "username", "type": "VARCHAR(255)", "nullable": False}
                ],
                "primary_keys": ["id"]
            }
        ]
    }
    
    result = agent.generate_ddl(source_schema, "mssql_to_postgres")
    
    # Assert the mock was NEVER called
    assert mock_generate.call_count == 0
    
    assert len(result["ddl_statements"]) == 1


def test_oracle_to_mysql_all_types_mapped():
    datatypes = MIGRATION_MATRIX["oracle_to_mysql"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_oracle_to_postgres_all_types_mapped():
    datatypes = MIGRATION_MATRIX["oracle_to_postgres"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_oracle_to_mssql_all_types_mapped():
    datatypes = MIGRATION_MATRIX["oracle_to_mssql"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_mssql_to_oracle_all_types_mapped():
    datatypes = MIGRATION_MATRIX["mssql_to_oracle"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_mysql_to_oracle_all_types_mapped():
    datatypes = MIGRATION_MATRIX["mysql_to_oracle"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_postgres_to_oracle_all_types_mapped():
    datatypes = MIGRATION_MATRIX["postgres_to_oracle"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_oracle_lossy_flags_present():
    # BOOLEAN -> NUMBER(1) lossy
    assert MIGRATION_MATRIX["mssql_to_oracle"]["datatypes"]["BOOLEAN"]["lossy"] is True
    assert MIGRATION_MATRIX["mysql_to_oracle"]["datatypes"]["BOOLEAN"]["lossy"] is True
    assert MIGRATION_MATRIX["postgres_to_oracle"]["datatypes"]["BOOLEAN"]["lossy"] is True
    
    # NUMBER no-precision -> DECIMAL(38,10) lossy
    assert MIGRATION_MATRIX["oracle_to_mysql"]["datatypes"]["NUMBER"]["lossy"] is True
    assert MIGRATION_MATRIX["oracle_to_postgres"]["datatypes"]["NUMBER"]["lossy"] is True
    assert MIGRATION_MATRIX["oracle_to_mssql"]["datatypes"]["NUMBER"]["lossy"] is True
    
    # DATE -> DATETIME/TIMESTAMP lossy
    assert MIGRATION_MATRIX["oracle_to_mysql"]["datatypes"]["DATE"]["lossy"] is True
    assert MIGRATION_MATRIX["oracle_to_postgres"]["datatypes"]["DATE"]["lossy"] is True
    assert MIGRATION_MATRIX["oracle_to_mssql"]["datatypes"]["DATE"]["lossy"] is True
