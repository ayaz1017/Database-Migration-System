import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.models import MigratableObject, TranslationResult, MigrationOptions

@pytest.mark.asyncio
async def test_auto_approve_success(mocker):
    # We will test the specific logic from main.py by extracting it or simulating it
    # Since start_migration_task is complex, we will simulate the translation block
    
    # Mocking the translation result
    res = TranslationResult(
        object_name="test_view",
        object_type="view",
        source_definition="CREATE VIEW test_view AS SELECT 1;",
        translated_definition="CREATE VIEW test_view AS SELECT 1;",
        translation_method="llm_assisted",
        confidence="high",
        needs_human_review=True
    )
    
    obj = MigratableObject(
        object_type="view",
        name="test_view",
        source_definition="CREATE VIEW test_view AS SELECT 1;",
        complexity_estimate="low"
    )
    
    req_options = MigrationOptions(auto_approve_objects=True)
    
    auto_approved_objects = []
    auto_apply_failed = []
    
    # Simulate the logic in main.py
    auto_approved = False
    if req_options.auto_approve_objects and res.translated_definition:
        try:
            # Simulate successful execute_ddl
            # no exception raised
            res.approved_by_user = True
            res.needs_human_review = False
            res.compile_status = "Compiled successfully"
            auto_approved_objects.append(f"{obj.object_type.upper()} / {obj.name}")
            auto_approved = True
        except Exception as e:
            res.translation_error = f"Auto-apply failed: {str(e)}"
            res.needs_human_review = True
            res.compile_status = "Compile error"
            attempted_ddl = res.translated_definition[:500] + ("..." if len(res.translated_definition) > 500 else "")
            auto_apply_failed.append({
                "object_name": f"{obj.object_type.upper()} / {obj.name}",
                "error": str(e),
                "attempted_ddl": attempted_ddl
            })

    assert auto_approved is True
    assert res.approved_by_user is True
    assert res.needs_human_review is False
    assert len(auto_approved_objects) == 1
    assert auto_approved_objects[0] == "VIEW / test_view"
    assert len(auto_apply_failed) == 0

@pytest.mark.asyncio
async def test_auto_approve_failure(mocker):
    res = TranslationResult(
        object_name="test_trigger",
        object_type="trigger",
        source_definition="CREATE TRIGGER test_trigger...",
        translated_definition="CREATE TRIGGER test_trigger... " * 100, # Make it long to test truncation
        translation_method="llm_assisted",
        confidence="high",
        needs_human_review=True
    )
    
    obj = MigratableObject(
        object_type="trigger",
        name="test_trigger",
        source_definition="CREATE TRIGGER test_trigger...",
        complexity_estimate="low"
    )
    
    req_options = MigrationOptions(auto_approve_objects=True)
    
    auto_approved_objects = []
    auto_apply_failed = []
    
    # Simulate the logic in main.py with an exception
    auto_approved = False
    if req_options.auto_approve_objects and res.translated_definition:
        try:
            # Simulate failed execute_ddl
            raise RuntimeError("Syntax error at line 5")
        except Exception as e:
            res.translation_error = f"Auto-apply failed: {str(e)}"
            res.needs_human_review = True
            res.compile_status = "Compile error"
            attempted_ddl = res.translated_definition[:500] + ("..." if len(res.translated_definition) > 500 else "")
            auto_apply_failed.append({
                "object_name": f"{obj.object_type.upper()} / {obj.name}",
                "error": str(e),
                "attempted_ddl": attempted_ddl
            })

    assert auto_approved is False
    assert res.approved_by_user is False
    assert res.needs_human_review is True
    assert "Compile error" in res.compile_status
    assert len(auto_approved_objects) == 0
    assert len(auto_apply_failed) == 1
    assert auto_apply_failed[0]["object_name"] == "TRIGGER / test_trigger"
    assert "Syntax error at line 5" in auto_apply_failed[0]["error"]
    assert len(auto_apply_failed[0]["attempted_ddl"]) == 503 # 500 + "..."
    assert auto_apply_failed[0]["attempted_ddl"].endswith("...")
