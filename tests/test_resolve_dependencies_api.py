import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.agents.schema_agent import SchemaAgent

client = TestClient(app)

def test_resolve_dependencies_api_pass_through():
    # Mock data
    all_tables_metadata = [
        {
            "name": "users",
            "has_foreign_keys_to": [],
            "referenced_by": ["orders"]
        },
        {
            "name": "orders",
            "has_foreign_keys_to": ["users"],
            "referenced_by": []
        }
    ]
    
    # 1. Call the function directly
    schema_agent = SchemaAgent()
    direct_result = schema_agent.resolve_table_dependencies(
        selected_tables=["orders"],
        all_tables_metadata=all_tables_metadata,
        mode="auto_include"
    )
    
    # 2. We need to mock DiscoveryService.list_tables_only for the API call
    from backend.services.discovery_service import DiscoveryService
    original_list_tables = DiscoveryService.list_tables_only
    
    def mock_list_tables(*args, **kwargs):
        return {"tables": all_tables_metadata}
        
    DiscoveryService.list_tables_only = mock_list_tables
    
    try:
        # Call the API
        response = client.post(
            "/api/discover/resolve_dependencies",
            json={
                "config": {
                    "db_type": "postgres",
                    "host": "localhost",
                    "port": 5432,
                    "username": "test",
                    "password": "test",
                    "database": "test"
                },
                "selected_tables": ["orders"],
                "fk_dependency_mode": "auto_include"
            }
        )
        
        assert response.status_code == 200
        api_result = response.json()
        
        # Verify the structure is exactly the same
        assert api_result["final_table_set"] == direct_result.final_table_set
        assert api_result["auto_added"] == direct_result.auto_added
        assert api_result["auto_added_reasons"] == direct_result.auto_added_reasons
        assert api_result["missing_dependencies"] == direct_result.missing_dependencies
        assert api_result["blocked"] == direct_result.blocked
    finally:
        # Restore mock
        DiscoveryService.list_tables_only = original_list_tables
