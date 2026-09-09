import pytest
import asyncio
from backend.agents.object_translation_agent import ObjectTranslationAgent
from backend.models import MigratableObject

@pytest.fixture
def agent():
    return ObjectTranslationAgent()

def test_trigger_function_skip(agent):
    raw_def = """
    CREATE OR REPLACE FUNCTION fn_audit_orders()
    RETURNS TRIGGER AS $function$
    BEGIN
        RETURN NEW;
    END;
    $function$ LANGUAGE plpgsql;
    """
    obj = MigratableObject(name="fn_audit_orders", object_type="function", source_definition=raw_def)
    result, success = agent._pg_to_mysql_function(obj, raw_def, "postgres")
    assert success is True
    assert "-- Trigger functions are inlined" in result

def test_scalar_function(agent):
    raw_def = """
    CREATE OR REPLACE FUNCTION fn_get_customer_spend(p_cust_id INT)
    RETURNS NUMERIC(14, 2) AS $function$
    DECLARE
        v_total NUMERIC(14, 2);
    BEGIN
        SELECT COALESCE(SUM(total_amount), 0.00) INTO v_total
        FROM orders
        WHERE customer_id = p_cust_id AND status <> 'CANCELLED';
        RETURN v_total;
    END;
    $function$ LANGUAGE plpgsql;
    """
    obj = MigratableObject(name="fn_get_customer_spend", object_type="function", source_definition=raw_def)
    result, success = agent._pg_to_mysql_function(obj, raw_def, "postgres")
    assert success is True
    assert "CREATE FUNCTION fn_get_customer_spend(p_cust_id INT) RETURNS DECIMAL(14, 2) READS SQL DATA" in result
    assert "DECLARE v_total DECIMAL(14, 2);" in result
    assert "SELECT COALESCE(SUM(total_amount), 0.00) INTO v_total" in result

def test_procedure_with_cursor(agent):
    raw_def = """
    CREATE OR REPLACE PROCEDURE sp_recalculate_department_budgets(p_min_headcount INT DEFAULT 10)
    LANGUAGE plpgsql
    AS $procedure$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN 
            SELECT department_id, SUM(salary) AS total_sal
            FROM employees
            WHERE status = 'ACTIVE'
            GROUP BY department_id
            HAVING COUNT(employee_id) >= p_min_headcount
        LOOP
            UPDATE departments
            SET budget = r.total_sal * 1.25
            WHERE department_id = r.department_id;
        END LOOP;
        
        INSERT INTO audit_logs (table_name, operation, record_id, details)
        VALUES ('departments', 'PROCEDURE', NULL, 'sp_recalculate_department_budgets completed successfully');
    END;
    $procedure$;
    """
    obj = MigratableObject(name="sp_recalculate_department_budgets", object_type="procedure", source_definition=raw_def)
    result, success = agent._pg_to_mysql_procedure(obj, raw_def, "postgres")
    assert success is True
    assert "CREATE PROCEDURE sp_recalculate_department_budgets(p_min_headcount INT )" in result
    assert "DECLARE cur_sp_recalculate_department_budgets CURSOR FOR SELECT" in result
    assert "v_department_id" in result
    assert "v_total_sal" in result
    assert "FETCH cur_sp_recalculate_department_budgets INTO v_department_id, v_total_sal;" in result
    assert "budget = v_total_sal * 1.25" in result

def test_simple_procedure(agent):
    raw_def = """
    CREATE OR REPLACE PROCEDURE sp_mark_order_delivered(p_order_id INT)
    LANGUAGE plpgsql
    AS $procedure$
    BEGIN
        UPDATE orders
        SET status = 'DELIVERED'
        WHERE order_id = p_order_id;

        UPDATE payments
        SET status = 'COMPLETED'
        WHERE order_id = p_order_id;
    END;
    $procedure$;
    """
    obj = MigratableObject(name="sp_mark_order_delivered", object_type="procedure", source_definition=raw_def)
    result, success = agent._pg_to_mysql_procedure(obj, raw_def, "postgres")
    assert success is True
    assert "CREATE PROCEDURE sp_mark_order_delivered(p_order_id INT)" in result
    assert "UPDATE orders" in result

def test_trigger_multiple_events(agent):
    raw_def = """
    CREATE OR REPLACE FUNCTION fn_audit_orders()
    RETURNS TRIGGER AS $function$
    BEGIN
        IF (TG_OP = 'INSERT') THEN
            INSERT INTO audit_logs (table_name, operation, record_id, details)
            VALUES ('orders', 'INSERT', NEW.order_id, 'Created order for customer ' || NEW.customer_id || ' status ' || NEW.status);
            RETURN NEW;
        ELSIF (TG_OP = 'UPDATE') THEN
            INSERT INTO audit_logs (table_name, operation, record_id, details)
            VALUES ('orders', 'UPDATE', NEW.order_id, 'Status changed from ' || OLD.status || ' to ' || NEW.status || ', Total: ' || NEW.total_amount);
            RETURN NEW;
        END IF;
        RETURN NULL;
    END;
    $function$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_audit_orders
    AFTER INSERT OR UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION fn_audit_orders();
    """
    obj = MigratableObject(name="trg_audit_orders", object_type="trigger", source_definition=raw_def)
    result, success = agent._pg_to_mysql_trigger(obj, raw_def, "postgres")
    assert success is True
    assert "CREATE TRIGGER trg_audit_orders_insert AFTER INSERT ON orders" in result
    assert "CREATE TRIGGER trg_audit_orders_update AFTER UPDATE ON orders" in result
    assert "RETURN NEW;" not in result
    assert "RETURN NULL;" not in result
    assert "CONCAT('Created order for customer ', NEW.customer_id, ' status ', NEW.status)" in result

def test_trigger_single_event(agent):
    raw_def = """
    CREATE OR REPLACE FUNCTION fn_update_product_stock()
    RETURNS TRIGGER AS $function$
    BEGIN
        UPDATE products
        SET stock_quantity = stock_quantity - NEW.quantity
        WHERE product_id = NEW.product_id;
        RETURN NEW;
    END;
    $function$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_update_stock
    AFTER INSERT ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION fn_update_product_stock();
    """
    obj = MigratableObject(name="trg_update_stock", object_type="trigger", source_definition=raw_def)
    result, success = agent._pg_to_mysql_trigger(obj, raw_def, "postgres")
    assert success is True
    assert "CREATE TRIGGER trg_update_stock AFTER INSERT ON order_items" in result
    assert "RETURN NEW;" not in result
    assert "stock_quantity - NEW.quantity" in result
