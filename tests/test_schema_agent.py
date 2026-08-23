import pytest
from unittest.mock import patch
from backend.agents.schema_agent import SchemaAgent
from backend.models import DependencyResolution

@pytest.fixture(autouse=True)
def mock_schema_agent_init():
    with patch.object(SchemaAgent, '__init__', return_value=None):
        yield

def test_resolve_dependencies_auto_include():
    agent = SchemaAgent()
    # We must patch __init__ but resolve_table_dependencies requires no self state
    # Wait, if we return None from __init__, agent is empty but we can call methods
    tables = [
        {"name": "users", "has_foreign_keys_to": []},
        {"name": "orders", "has_foreign_keys_to": ["users"]},
        {"name": "order_items", "has_foreign_keys_to": ["orders", "products"]},
        {"name": "products", "has_foreign_keys_to": []}
    ]
    
    # User selects only 'order_items', expecting 'orders', 'users', 'products' to auto_include
    resolution = agent.resolve_table_dependencies(["order_items"], tables, "auto_include")
    
    assert not resolution.blocked
    assert set(resolution.final_table_set) == {"users", "products", "orders", "order_items"}
    # order should be valid: users/products first, then orders, then order_items
    assert resolution.migration_order.index("users") < resolution.migration_order.index("orders")
    assert resolution.migration_order.index("orders") < resolution.migration_order.index("order_items")

def test_resolve_dependencies_strict_blocked():
    agent = SchemaAgent()
    tables = [
        {"name": "users", "has_foreign_keys_to": []},
        {"name": "orders", "has_foreign_keys_to": ["users"]}
    ]
    
    # User selects only 'orders', but strict mode blocks it because 'users' is missing
    resolution = agent.resolve_table_dependencies(["orders"], tables, "strict")
    
    assert resolution.blocked
    assert "users" in resolution.missing_dependencies

def test_resolve_dependencies_drop_constraint():
    agent = SchemaAgent()
    tables = [
        {"name": "users", "has_foreign_keys_to": []},
        {"name": "orders", "has_foreign_keys_to": ["users"]}
    ]
    
    # User selects only 'orders', missing parent 'users' should be dropped constraint
    resolution = agent.resolve_table_dependencies(["orders"], tables, "drop_constraint")
    
    assert not resolution.blocked
    assert set(resolution.final_table_set) == {"orders"}
    assert len(resolution.dropped_constraints) == 1
    assert resolution.dropped_constraints[0].from_table == "orders"
    assert resolution.dropped_constraints[0].to_table == "users"

def test_resolve_dependencies_circular():
    agent = SchemaAgent()
    tables = [
        {"name": "a", "has_foreign_keys_to": ["b"]},
        {"name": "b", "has_foreign_keys_to": ["c"]},
        {"name": "c", "has_foreign_keys_to": ["a"]}
    ]
    
    resolution = agent.resolve_table_dependencies(["a", "b", "c"], tables, "auto_include")
    
    assert not resolution.blocked
    assert set(resolution.final_table_set) == {"a", "b", "c"}
    assert len(resolution.circular_dependency_groups) == 1
    # group should be strongly connected component
    assert set(resolution.circular_dependency_groups[0]) == {"a", "b", "c"}

def test_resolve_dependencies_self_referencing():
    agent = SchemaAgent()
    tables = [
        {"name": "employees", "has_foreign_keys_to": ["employees"]}
    ]
    
    resolution = agent.resolve_table_dependencies(["employees"], tables, "auto_include")
    
    assert not resolution.blocked
    assert "employees" in resolution.self_referencing_tables
