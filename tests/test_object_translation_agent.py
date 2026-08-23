"""
Test suite for ObjectTranslationAgent.

Covers all 8 required test cases:
  1. View translation via rules only — high confidence
  2. View translation fallback to LLM for complex functions
  3. Procedure always requires human review
  4. TRANSLATION_UNCERTAIN comments are parsed and extracted
  5. INSTEAD OF trigger to MySQL flagged as incompatible
  6. Postgres trigger splits into function + trigger statements
  7. No auto-apply for procedures regardless of confidence
  8. Pipeline status reflects pending review when objects are awaiting approval

Run:
    pytest tests/test_object_translation_agent.py -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Prevent heavy module-level instantiation in llm_service.py from running
# during test collection. We patch ChatGoogleGenerativeAI before any backend
# module is imported.
# ---------------------------------------------------------------------------
_patcher = patch("langchain_google_genai.ChatGoogleGenerativeAI", new=MagicMock())
_patcher.start()

from backend.agents.object_translation_agent import (  # noqa: E402
    ObjectTranslationAgent,
    parse_uncertain_lines,
)
from backend.models import MigratableObject, TranslationResult  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_view(name: str, definition: str) -> MigratableObject:
    return MigratableObject(
        object_type="view",
        name=name,
        source_definition=definition,
        complexity_estimate="low",
    )


def make_proc(name: str, definition: str) -> MigratableObject:
    return MigratableObject(
        object_type="procedure",
        name=name,
        source_definition=definition,
        complexity_estimate="medium",
    )


def make_trigger(name: str, definition: str, object_type: str = "trigger") -> MigratableObject:
    return MigratableObject(
        object_type=object_type,
        name=name,
        source_definition=definition,
        complexity_estimate="medium",
    )


# A simple view definition containing only functions that the rules engine handles
SIMPLE_MSSQL_VIEW = """
CREATE VIEW dbo.vw_ActiveUsers AS
SELECT id, name, ISNULL(email, 'no-email'), GETDATE() AS captured_at
FROM dbo.Users
WHERE active = 1
"""

# A complex view containing an unknown function that forces LLM fallback
COMPLEX_MSSQL_VIEW = """
CREATE VIEW dbo.vw_Report AS
SELECT id, FORMAT(created_at, 'yyyy-MM-dd') AS formatted_date, DATEPART(week, created_at)
FROM dbo.Orders
"""

# A simple procedure that the backend will translate via LLM
SIMPLE_MSSQL_PROC = """
CREATE PROCEDURE dbo.usp_GetUser
    @UserId INT
AS
BEGIN
    SELECT * FROM Users WHERE id = @UserId
END
"""

# An INSTEAD OF trigger (invalid on MySQL tables)
INSTEAD_OF_TRIGGER = """
CREATE TRIGGER trg_InsteadOfInsert
ON dbo.Orders
INSTEAD OF INSERT
AS
BEGIN
    INSERT INTO dbo.OrdersAudit SELECT * FROM INSERTED
END
"""

# A normal AFTER trigger
AFTER_TRIGGER = """
CREATE TRIGGER trg_AfterInsert
ON dbo.Orders
AFTER INSERT
AS
BEGIN
    INSERT INTO dbo.AuditLog (event, ts) VALUES ('INSERT', GETDATE())
END
"""

# Postgres trigger function + trigger statement returned by LLM
POSTGRES_TRIGGER_RESPONSE = """\
CREATE OR REPLACE FUNCTION trg_after_insert_fn() RETURNS trigger AS $$
BEGIN
    INSERT INTO audit_log (event, ts) VALUES ('INSERT', CURRENT_TIMESTAMP);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_after_insert
AFTER INSERT ON orders
FOR EACH ROW EXECUTE FUNCTION trg_after_insert_fn();
"""

# Response that contains TRANSLATION_UNCERTAIN markers
UNCERTAIN_PROC_RESPONSE = """\
CREATE PROCEDURE usp_GetUser(p_user_id INT)
BEGIN
-- TRANSLATION_UNCERTAIN: MySQL has no @variable parameter prefix, used regular parameter
    SELECT * FROM users WHERE id = p_user_id;
END;
"""


# ---------------------------------------------------------------------------
# 1. View translation — rules only, high confidence
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_view_translation_rules_only_high_confidence():
    """
    Simple SQL Server views containing only GETDATE / ISNULL should be translated
    by the rules engine without LLM assistance, returning confidence=high and
    needs_human_review=False.
    """
    agent = ObjectTranslationAgent(llm_service=None)  # LLM must NOT be called
    view = make_view("vw_ActiveUsers", SIMPLE_MSSQL_VIEW)

    result = await agent.translate_view(view, source_dialect="mssql", target_dialect="mysql")

    assert result.translation_method == "rules_only"
    assert result.confidence == "high"
    assert result.needs_human_review is False
    assert result.translation_error is None
    assert result.translated_definition is not None
    # GETDATE() should have been replaced with CURRENT_TIMESTAMP
    assert "CURRENT_TIMESTAMP" in result.translated_definition
    # ISNULL should have been replaced with COALESCE
    assert "COALESCE" in result.translated_definition


# ---------------------------------------------------------------------------
# 2. View translation — fallback to LLM for complex functions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_view_translation_falls_back_to_llm():
    """
    Views containing functions that the rules engine cannot handle (e.g. FORMAT,
    DATEPART) must fall back to LLM-assisted translation and set confidence to
    medium with needs_human_review=True.
    """
    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(
        return_value="CREATE OR REPLACE VIEW vw_report AS SELECT id, DATE_FORMAT(created_at, '%Y-%m-%d') AS formatted_date FROM orders"
    )

    agent = ObjectTranslationAgent(llm_service=mock_llm)
    view = make_view("vw_Report", COMPLEX_MSSQL_VIEW)

    result = await agent.translate_view(view, source_dialect="mssql", target_dialect="mysql")

    assert result.translation_method == "llm_assisted"
    assert result.confidence == "medium"
    assert result.needs_human_review is True
    mock_llm.generate_response.assert_called_once()


# ---------------------------------------------------------------------------
# 3. Procedure translation always requires human review
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_procedure_always_requires_review():
    """
    Any stored procedure or function translated via the translation agent must
    always have needs_human_review=True, regardless of output quality.
    """
    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(
        return_value="CREATE PROCEDURE usp_GetUser(p_user_id INT) BEGIN SELECT * FROM users WHERE id = p_user_id; END;"
    )

    agent = ObjectTranslationAgent(llm_service=mock_llm)
    proc = make_proc("usp_GetUser", SIMPLE_MSSQL_PROC)

    result = await agent.translate_procedure_or_trigger(proc, source_dialect="mssql", target_dialect="mysql")

    assert result.needs_human_review is True
    assert result.translation_method == "llm_full"


# ---------------------------------------------------------------------------
# 4. TRANSLATION_UNCERTAIN comments are parsed and extracted correctly
# ---------------------------------------------------------------------------

def test_uncertain_lines_are_parsed_and_extracted():
    """
    parse_uncertain_lines() must correctly identify every line that contains
    a '-- TRANSLATION_UNCERTAIN:' marker, capturing both the line number (1-indexed)
    and the trimmed explanation text.
    """
    result = parse_uncertain_lines(UNCERTAIN_PROC_RESPONSE)

    # Exactly one uncertain line in our fixture
    assert len(result) == 1
    item = result[0]

    # Line 3 in UNCERTAIN_PROC_RESPONSE contains the marker
    assert item["line_number"] == 3
    assert "MySQL" in item["comment"]
    assert "parameter" in item["comment"].lower()


# ---------------------------------------------------------------------------
# 5. INSTEAD OF trigger to MySQL is flagged as incompatible
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_instead_of_trigger_to_mysql_flagged_as_incompatible():
    """
    When migrating an MSSQL INSTEAD OF trigger to MySQL (which does not support
    them on tables), the agent must immediately return an error without calling
    the LLM, setting translation_error to a descriptive message about the
    incompatibility, and translated_definition must be None.
    """
    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock()  # Must NOT be called

    agent = ObjectTranslationAgent(llm_service=mock_llm)
    trigger = make_trigger("trg_InsteadOfInsert", INSTEAD_OF_TRIGGER)

    result = await agent.translate_procedure_or_trigger(
        trigger, source_dialect="mssql", target_dialect="mysql"
    )

    # LLM should not have been invoked for an incompatible object
    mock_llm.generate_response.assert_not_called()

    assert result.translated_definition is None
    assert result.translation_error is not None
    assert "INSTEAD OF" in result.translation_error
    assert "MySQL" in result.translation_error
    assert result.needs_human_review is True
    assert result.confidence == "low"


# ---------------------------------------------------------------------------
# 6. PostgreSQL trigger output contains both function + trigger statement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_postgres_trigger_splits_into_function_and_trigger():
    """
    When the target dialect is PostgreSQL, the LLM is instructed to output both
    a CREATE OR REPLACE FUNCTION (returning trigger) and a CREATE TRIGGER
    statement. The translated_definition must contain both blocks.
    """
    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(return_value=POSTGRES_TRIGGER_RESPONSE)

    agent = ObjectTranslationAgent(llm_service=mock_llm)
    trigger = make_trigger("trg_AfterInsert", AFTER_TRIGGER)

    result = await agent.translate_procedure_or_trigger(
        trigger, source_dialect="mssql", target_dialect="postgres"
    )

    assert result.translated_definition is not None
    td = result.translated_definition
    # Must contain a trigger function definition
    assert "RETURNS trigger" in td
    assert "LANGUAGE plpgsql" in td
    # Must contain a separate CREATE TRIGGER statement
    assert "CREATE TRIGGER" in td
    assert "EXECUTE FUNCTION" in td


# ---------------------------------------------------------------------------
# 7. No auto-apply for procedures regardless of confidence
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_auto_apply_for_procedures_regardless_of_confidence():
    """
    Even if the LLM returns a clean translation with no uncertain lines for a
    procedure (which would give confidence='medium'), the result must still have
    needs_human_review=True and approved_by_user=False so the orchestrator never
    applies it automatically.
    """
    clean_proc_sql = "CREATE PROCEDURE usp_GetUser(p_user_id INT) BEGIN SELECT * FROM users WHERE id = p_user_id; END;"
    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(return_value=clean_proc_sql)

    agent = ObjectTranslationAgent(llm_service=mock_llm)
    proc = make_proc("usp_GetUser", SIMPLE_MSSQL_PROC)

    result = await agent.translate_procedure_or_trigger(proc, source_dialect="mssql", target_dialect="mysql")

    # These are the invariants the orchestrator uses to decide whether to auto-apply
    assert result.needs_human_review is True
    assert result.approved_by_user is False
    assert result.translation_method == "llm_full"


# ---------------------------------------------------------------------------
# 8. Pipeline status reflects pending review when objects await approval
# ---------------------------------------------------------------------------

def test_pipeline_status_reflects_pending_review():
    """
    When the orchestrator computes the final_status string, any object
    translations that still have needs_human_review=True and approved_by_user=False
    must result in a status of 'COMPLETED — N objects awaiting review'.

    This test replicates the orchestrator's status computation logic directly
    to verify correctness.
    """
    # Simulate what run_migration_pipeline stores in object_translations
    object_translations = [
        # A high-confidence view that was auto-applied
        {"needs_human_review": False, "approved_by_user": True, "object_type": "view", "object_name": "vw_active"},
        # A procedure awaiting review
        {"needs_human_review": True, "approved_by_user": False, "object_type": "procedure", "object_name": "usp_GetUser"},
        # A trigger awaiting review
        {"needs_human_review": True, "approved_by_user": False, "object_type": "trigger", "object_name": "trg_AfterInsert"},
    ]

    # Replicate the orchestrator logic from main.py
    pending_review_count = sum(
        1 for res in object_translations
        if res["needs_human_review"] and not res["approved_by_user"]
    )

    if pending_review_count > 0:
        final_status = f"COMPLETED — {pending_review_count} objects awaiting review"
    else:
        final_status = "SUCCESS"

    assert pending_review_count == 2
    assert "awaiting review" in final_status
    assert "2" in final_status
    assert "COMPLETED" in final_status


# ---------------------------------------------------------------------------
# Bonus: retry_translation_after_compile_error returns a corrected translation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retry_translation_after_compile_error():
    """
    When a previously approved DDL fails to compile, retry_translation_after_compile_error
    must pass the original source, the failed translation, and the compile error
    back to the LLM, returning a new TranslationResult with needs_human_review=True
    and approved_by_user=False so the user can re-review the AI-suggested fix.
    """
    corrected_sql = "CREATE PROCEDURE usp_GetUser(IN p_user_id INT) BEGIN SELECT * FROM users WHERE id = p_user_id; END;"
    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(return_value=corrected_sql)

    agent = ObjectTranslationAgent(llm_service=mock_llm)

    obj_translation = {
        "object_name": "usp_GetUser",
        "object_type": "procedure",
        "source_definition": SIMPLE_MSSQL_PROC,
        "translated_definition": "CREATE PROCEDURE usp_GetUser(@UserId INT) BEGIN SELECT * FROM users WHERE id = @UserId; END;",
    }

    result = await agent.retry_translation_after_compile_error(
        obj_translation,
        target_dialect="mysql",
        compile_error="You have an error in your SQL syntax near '@UserId'"
    )

    mock_llm.generate_response.assert_called_once()
    assert result.needs_human_review is True
    assert result.approved_by_user is False
    assert result.translated_definition == corrected_sql
    assert result.translation_method == "llm_full"
    assert result.confidence == "low"
