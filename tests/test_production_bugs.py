import pytest
import time
import json
from unittest.mock import patch, MagicMock, AsyncMock

from backend.main import app, clear_lock
from backend.agents.schema_agent import SchemaAgent
from backend.agents.validation_agent import ValidationAgent

def test_stale_lock_clear():
    import backend.main as main_module
    main_module.is_migrating = True
    main_module.migration_start_time = time.time() - 1900  # 31 minutes ago
    
    res = clear_lock()
    assert res["status"] == "success"
    assert main_module.is_migrating == False
    assert main_module.migration_start_time == 0

@pytest.mark.asyncio
async def test_llm_skipped_status():
    with patch("backend.services.llm_service.LLMService.generate_response", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = Exception("API_KEY_INVALID")
        
        agent = SchemaAgent()
        result = await agent.analyze_ddl([{"statement": "CREATE TABLE"}], "mysql", "postgres")
        
        assert result.get("status") == "skipped"
        assert len(result.get("warnings")) == 1
        assert "API_KEY_INVALID" in result["warnings"][0]

def test_validation_agent_none_score():
    val = ValidationAgent()
    
    source_conn = MagicMock()
    target_conn = MagicMock()
    
    with patch.object(val, '_get_row_count', return_value=10):
        res = val.validate_migration(source_conn, target_conn, [{"name": "t1"}], "mysql_to_postgres", llm_skipped=True)
        assert res["validation_score"] is None
        assert res["summary"]["overall_score"] is None
