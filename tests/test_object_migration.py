import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from backend.main import run_migration_pipeline, MigrationRequest, ConnectionConfig
from backend.models import (
    MigrationOptions,
    TranslationResult,
    MigratableObject
)

@pytest.fixture
def mock_req():
    return MigrationRequest(
        source=ConnectionConfig(host="localhost", port=1433, username="sa", password="password", database="test", db_type="mssql"),
        target=ConnectionConfig(host="localhost", port=5432, username="postgres", password="password", database="test", db_type="postgres"),
        mode="schema_only",
        options=MigrationOptions(
            migrate_all_tables=True,
            migrate_data=False,
            migrate_views=True,
            migrate_procedures=True,
            migrate_triggers=True
        )
    )

@pytest.mark.asyncio
@patch("backend.main.DiscoveryService")
@patch("backend.main.SchemaAgent")
@patch("backend.agents.object_translation_agent.ObjectTranslationAgent")
@patch("backend.main.execute_ddl")
@patch("backend.main.get_raw_conn")
@patch("sqlite3.connect")
async def test_view_applied_directly_no_gate(mock_sqlite, mock_get_db_conn, mock_execute_ddl, mock_trans_agent, mock_schema_agent, mock_discovery, mock_req):
    mock_source_schema = {
        "tables": [],
        "views": [{"object_type": "view", "name": "vw_test", "source_definition": "create view vw_test", "complexity_estimate": "low"}],
        "procedures": [],
        "triggers": []
    }
    
    mock_discovery_instance = mock_discovery.return_value
    mock_discovery_instance.connect_and_discover.return_value = {"tables": []}
    mock_discovery_instance.list_migratable_objects.return_value = mock_source_schema

    mock_schema_agent_instance = mock_schema_agent.return_value
    mock_schema_agent_instance.translate_schema = AsyncMock(return_value={"tables": [], "warnings": []})
    mock_schema_agent_instance.analyze_ddl = AsyncMock(return_value={"tables": []})
    
    mock_trans_agent_instance = mock_trans_agent.return_value
    mock_trans_agent_instance.translate_view = AsyncMock(return_value=TranslationResult(
        object_name="vw_test",
        object_type="view",
        translated_definition="CREATE VIEW vw_test AS SELECT * FROM test;",
        needs_human_review=False,
        uncertain_lines=[],
        translation_error=None
    ))
    
    # Target DB connection
    mock_target_conn = MagicMock()
    mock_get_db_conn.return_value = mock_target_conn
    
    saved_payload = await run_migration_pipeline(mock_req, "job-123")
    
    mock_execute_ddl.assert_called_once_with(mock_target_conn.cursor.return_value, "CREATE VIEW vw_test AS SELECT * FROM test;", "postgres")
    assert len(saved_payload["object_translations"]) == 1
    assert saved_payload["object_translations"][0]["compile_status"] == "Compiled successfully"
    assert saved_payload["status"] == "success"


@pytest.mark.asyncio
@patch("backend.main.DiscoveryService")
@patch("backend.main.SchemaAgent")
@patch("backend.agents.object_translation_agent.ObjectTranslationAgent")
@patch("backend.main.execute_ddl")
@patch("backend.main.get_raw_conn")
@patch("sqlite3.connect")
async def test_apply_failure_continues_to_next_object(mock_sqlite, mock_get_db_conn, mock_execute_ddl, mock_trans_agent, mock_schema_agent, mock_discovery, mock_req):
    mock_source_schema = {
        "tables": [],
        "views": [
            {"object_type": "view", "name": "vw_test_1", "source_definition": "create view vw_test_1", "complexity_estimate": "low"},
            {"object_type": "view", "name": "vw_test_2", "source_definition": "create view vw_test_2", "complexity_estimate": "low"}
        ],
        "procedures": [],
        "triggers": []
    }
    
    mock_discovery_instance = mock_discovery.return_value
    mock_discovery_instance.connect_and_discover.return_value = {"tables": []}
    mock_discovery_instance.list_migratable_objects.return_value = mock_source_schema
    
    mock_schema_agent_instance = mock_schema_agent.return_value
    mock_schema_agent_instance.translate_schema = AsyncMock(return_value={"tables": [], "warnings": []})
    mock_schema_agent_instance.analyze_ddl = AsyncMock(return_value={"tables": []})
    
    mock_trans_agent_instance = mock_trans_agent.return_value
    mock_trans_agent_instance.translate_view = AsyncMock(side_effect=[
        TranslationResult(
            object_name="vw_test_1", object_type="view",
            translated_definition="CREATE VIEW vw_test_1 AS SELECT * FROM test;",
            uncertain_lines=[], translation_error=None
        ),
        TranslationResult(
            object_name="vw_test_2", object_type="view",
            translated_definition="CREATE VIEW vw_test_2 AS SELECT * FROM test;",
            uncertain_lines=[], translation_error=None
        )
    ])
    
    # First execution fails, second succeeds
    mock_target_conn = MagicMock()
    mock_get_db_conn.return_value = mock_target_conn
    mock_execute_ddl.side_effect = [Exception("Syntax error near 'VIEW'"), None]
    
    saved_payload = await run_migration_pipeline(mock_req, "job-456")
    
    assert mock_execute_ddl.call_count == 2
    assert len(saved_payload["object_translations"]) == 2
    assert saved_payload["object_translations"][0]["compile_status"] == "Compile error"
    assert "Syntax error near 'VIEW'" in saved_payload["object_translations"][0]["translation_error"]
    assert saved_payload["object_translations"][1]["compile_status"] == "Compiled successfully"


@pytest.mark.asyncio
@patch("backend.main.DiscoveryService")
@patch("backend.main.SchemaAgent")
@patch("backend.agents.object_translation_agent.ObjectTranslationAgent")
@patch("backend.main.execute_ddl")
@patch("backend.main.get_raw_conn")
@patch("sqlite3.connect")
async def test_translation_failure_continues(mock_sqlite, mock_get_db_conn, mock_execute_ddl, mock_trans_agent, mock_schema_agent, mock_discovery, mock_req):
    mock_source_schema = {
        "tables": [],
        "views": [
            {"object_type": "view", "name": "vw_test_fail", "source_definition": "create view vw_test_fail", "complexity_estimate": "low"}
        ],
        "procedures": [],
        "triggers": []
    }
    
    mock_discovery_instance = mock_discovery.return_value
    mock_discovery_instance.connect_and_discover.return_value = {"tables": []}
    mock_discovery_instance.list_migratable_objects.return_value = mock_source_schema
    
    mock_schema_agent_instance = mock_schema_agent.return_value
    mock_schema_agent_instance.translate_schema = AsyncMock(return_value={"tables": [], "warnings": []})
    mock_schema_agent_instance.analyze_ddl = AsyncMock(return_value={"tables": []})
    
    mock_trans_agent_instance = mock_trans_agent.return_value
    mock_trans_agent_instance.translate_view = AsyncMock(return_value=TranslationResult(
        object_name="vw_test_fail", object_type="view",
        translated_definition=None, uncertain_lines=[], translation_error="LLM timeout"
    ))
    
    mock_target_conn = MagicMock()
    mock_get_db_conn.return_value = mock_target_conn
    
    saved_payload = await run_migration_pipeline(mock_req, "job-789")
    
    mock_execute_ddl.assert_not_called()
    assert len(saved_payload["object_translations"]) == 1
    assert saved_payload["object_translations"][0]["translation_error"] == "LLM timeout"
