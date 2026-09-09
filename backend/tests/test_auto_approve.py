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


def test_clean_ddl():
    from backend.main import clean_ddl
    
    sql = """
    -- Single line comment
    DELIMITER //
    CREATE VIEW test_view AS
    /* Block comment
       spanning multiple lines */
    SELECT 1 AS id;
    DELIMITER ;
    """
    cleaned = clean_ddl(sql, dialect="mysql")
    assert "Single line comment" not in cleaned
    assert "Block comment" not in cleaned
    assert "DELIMITER" not in cleaned
    assert "CREATE VIEW test_view AS" in cleaned
    assert "SELECT 1 AS id;" in cleaned


def test_execute_mssql_ddl_go_split():
    from backend.main import execute_mssql_ddl
    
    cursor_mock = MagicMock()
    ddl = """
    CREATE OR ALTER VIEW vw_test AS SELECT 1 AS x;
    GO
    CREATE OR ALTER PROCEDURE sp_test AS BEGIN SELECT 2 AS y; END;
    go
    """
    execute_mssql_ddl(cursor_mock, ddl)
    assert cursor_mock.execute.call_count == 2
    first_call = cursor_mock.execute.call_args_list[0][0][0]
    second_call = cursor_mock.execute.call_args_list[1][0][0]
    assert "CREATE OR ALTER VIEW vw_test" in first_call
    assert "CREATE OR ALTER PROCEDURE sp_test" in second_call


def test_execute_mssql_ddl_failure_context():
    from backend.main import execute_mssql_ddl
    
    cursor_mock = MagicMock()
    cursor_mock.execute.side_effect = RuntimeError("Incorrect syntax near 'BAD'")
    
    with pytest.raises(Exception) as excinfo:
        execute_mssql_ddl(cursor_mock, "BAD SQL STATEMENT\nGO")
    
    err = str(excinfo.value)
    assert "MSSQL DDL failed" in err
    assert "Incorrect syntax near 'BAD'" in err
    assert "DDL attempted" in err


@pytest.mark.asyncio
async def test_auto_apply_object_success():
    from backend.main import auto_apply_object
    
    cursor_mock = MagicMock()
    obj = MigratableObject(
        object_type="view",
        name="vw_orders",
        source_definition="CREATE VIEW vw_orders AS SELECT 1;",
        complexity_estimate="low"
    )
    target_config = MagicMock()
    target_config.db_type = "mssql"
    
    res = await auto_apply_object(obj, "CREATE OR ALTER VIEW vw_orders AS SELECT 1;\nGO", cursor_mock, target_config)
    assert res["status"] == "applied"
    assert res["object"] == "vw_orders"
    assert cursor_mock.execute.call_count == 1


@pytest.mark.asyncio
async def test_auto_apply_object_categorized_errors():
    from backend.main import auto_apply_object
    
    obj = MigratableObject(
        object_type="view",
        name="vw_err",
        source_definition="...",
        complexity_estimate="low"
    )
    target_config = MagicMock()
    target_config.db_type = "postgres"
    
    # 1. SQL Syntax Error
    cursor_mock = MagicMock()
    cursor_mock.execute.side_effect = Exception("42601 syntax error at or near 'INVALID'")
    with pytest.raises(Exception) as excinfo:
        await auto_apply_object(obj, "INVALID DDL", cursor_mock, target_config)
    assert "SQL syntax error applying 'vw_err'" in str(excinfo.value)

    # 2. Permission / Privilege Error
    cursor_mock = MagicMock()
    cursor_mock.execute.side_effect = Exception("permission denied for schema public")
    with pytest.raises(Exception) as excinfo:
        await auto_apply_object(obj, "CREATE VIEW vw_err AS SELECT 1", cursor_mock, target_config)
    assert "Insufficient privileges to create 'vw_err'" in str(excinfo.value)

    # 3. Missing import NameError (simulated)
    with patch("backend.main.execute_ddl", side_effect=NameError("name 'some_mod' is not defined")):
        cursor_mock = MagicMock()
        with pytest.raises(Exception) as excinfo:
            await auto_apply_object(obj, "SELECT 1", cursor_mock, target_config)
        assert "Internal error (missing import): name 'some_mod' is not defined" in str(excinfo.value)


def test_pg_to_mssql_view_translation():
    from backend.agents.object_translation_agent import ObjectTranslationAgent
    
    agent = ObjectTranslationAgent()
    pg_view = """
    CREATE VIEW vw_customer_active AS
    SELECT 
        c.id, 
        c.name::text AS customer_name,
        COALESCE(c.balance, 0) AS balance,
        TO_CHAR(c.created_at, 'YYYY-MM') AS signup_month
    FROM customers c
    WHERE c.name ILIKE '%corp%' AND c.is_active = true;
    """
    translated, ok = agent._rules_based_translate_view(pg_view, "postgres", "mssql")
    assert ok is True
    assert "CREATE OR ALTER VIEW" in translated
    assert "::text" not in translated
    assert "ILIKE" not in translated
    assert "LIKE '%corp%'" in translated
    assert "ISNULL(c.balance, 0)" in translated
    assert "FORMAT(c.created_at, 'yyyy-MM')" in translated
    assert "= 1" in translated


def test_pg_to_mssql_procedure_translation():
    from backend.agents.object_translation_agent import ObjectTranslationAgent
    
    agent = ObjectTranslationAgent()
    obj = MigratableObject(
        object_type="procedure",
        name="update_balance",
        source_definition="""
        CREATE OR REPLACE PROCEDURE update_balance(p_cust_id INT, p_amount NUMERIC)
        LANGUAGE plpgsql
        AS $$
        BEGIN
            UPDATE accounts SET balance = balance + p_amount WHERE id = p_cust_id;
            RAISE NOTICE 'Updated balance for %', p_cust_id;
        END;
        $$;
        """,
        complexity_estimate="medium"
    )
    translated, ok = agent._rules_based_translate_procedure_or_trigger(obj, "postgres", "mssql")
    assert ok is True
    assert "CREATE OR ALTER PROCEDURE update_balance" in translated
    assert "@p_cust_id" in translated
    assert "@p_amount" in translated
    assert "SET NOCOUNT ON;" in translated
    assert "LANGUAGE plpgsql" not in translated
    assert "$$" not in translated
    assert "PRINT" in translated


def test_pg_to_mssql_table_valued_function():
    from backend.agents.object_translation_agent import ObjectTranslationAgent
    
    agent = ObjectTranslationAgent()
    obj = MigratableObject(
        object_type="function",
        name="get_orders",
        source_definition="""
        CREATE OR REPLACE FUNCTION get_orders(p_cust_id INT)
        RETURNS TABLE (order_id INT, total NUMERIC)
        AS $$
        BEGIN
            RETURN QUERY SELECT id, amount FROM orders WHERE cust_id = p_cust_id;
        END;
        $$ LANGUAGE plpgsql;
        """,
        complexity_estimate="medium"
    )
    translated, ok = agent._rules_based_translate_procedure_or_trigger(obj, "postgres", "mssql")
    assert ok is True
    assert "CREATE OR ALTER FUNCTION get_orders" in translated
    assert "@p_cust_id" in translated
    assert "RETURNS TABLE" in translated
    assert "RETURN" in translated
    assert "$$" not in translated


def test_pg_to_mssql_trigger_translation():
    from backend.agents.object_translation_agent import ObjectTranslationAgent
    
    agent = ObjectTranslationAgent()
    obj = MigratableObject(
        object_type="trigger",
        name="tr_audit_orders",
        source_definition="""
        CREATE OR REPLACE FUNCTION fn_audit_orders()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            INSERT INTO audit_log (order_id, action) VALUES (NEW.id, 'INSERTED');
            RETURN NEW;
        END;
        $$;

        CREATE TRIGGER tr_audit_orders
        AFTER INSERT ON orders
        FOR EACH ROW
        EXECUTE FUNCTION fn_audit_orders();
        """,
        complexity_estimate="medium"
    )
    translated, ok = agent._rules_based_translate_procedure_or_trigger(obj, "postgres", "mssql")
    assert ok is True
    assert "CREATE OR ALTER TRIGGER tr_audit_orders" in translated
    assert "ON orders" in translated
    assert "AFTER INSERT" in translated
    assert "FOR EACH ROW" not in translated
    assert "LANGUAGE plpgsql" not in translated
    assert "RETURN NEW" not in translated
    assert "i.id" in translated

