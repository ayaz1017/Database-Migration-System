import pytest
import asyncio
from unittest.mock import patch
from backend.main import run_migration_pipeline, MigrationRequest, ConnectionConfig
from backend.models import MigrationOptions, DependencyResolution

@pytest.mark.asyncio
async def test_execution_dag_ordering():
    conf = ConnectionConfig(
        db_type="postgres", host="localhost", port=5432, username="user", password="password", database="test_db"
    )

    options = MigrationOptions(
        migrate_all_tables=False,
        selected_tables=["departments", "employees", "orders", "order_items", "customers"],
        fk_dependency_mode="auto_include"
    )

    req = MigrationRequest(source=conf, target=conf, mode="full", options=options, id="test_dag_job")

    mock_source_schema = {
        "tables": [
            {"name": "departments", "row_count": 10},
            {"name": "customers", "row_count": 10},
            {"name": "employees", "row_count": 10},
            {"name": "orders", "row_count": 10},
            {"name": "order_items", "row_count": 10},
        ]
    }

    mock_resolution = DependencyResolution(
        final_table_set=["departments", "employees", "orders", "order_items", "customers"],
        originally_selected=["departments", "employees", "orders", "order_items", "customers"],
        auto_added=[], auto_added_reasons={}, self_referencing_tables=[], circular_dependency_groups=[],
        blocked=False, missing_dependencies=[], dropped_constraints=[],
        migration_order=["departments", "customers", "employees", "orders", "order_items"],
        migration_generations=[
            ["departments", "customers"],
            ["employees", "orders"],
            ["order_items"]
        ]
    )

    execution_log = []
    
    async def mock_run_table_worker(table_name, row_count, table_schema_obj, loop):
        execution_log.append(f"START {table_name}")
        if table_name in ["departments", "customers"]:
            await asyncio.sleep(0.5)
        else:
            await asyncio.sleep(0.1)
        execution_log.append(f"END {table_name}")
        return row_count

    with patch("backend.main.test_connection_config", return_value=(True, None)), \
         patch("backend.main.DiscoveryService") as MockDiscovery, \
         patch("backend.main.SchemaAgent") as MockSchemaAgent, \
         patch("backend.main.ValidationAgent"), \
         patch("backend.main.get_raw_conn"), \
         patch("backend.main.get_engine"), \
         patch("backend.main.broadcast_progress"), \
         patch("backend.main.execute_ddl"), \
         patch("asyncio.to_thread") as mock_to_thread:
        
        discovery_instance = MockDiscovery.return_value
        discovery_instance.connect_and_discover.return_value = mock_source_schema
        
        schema_instance = MockSchemaAgent.return_value
        schema_instance.resolve_table_dependencies.return_value = mock_resolution
        schema_instance.generate_ddl.return_value = {"ddl_statements": [], "translation_log": []}
        async def async_analyze_ddl(*args, **kwargs):
            return {"status": "skipped"}
        schema_instance.analyze_ddl.side_effect = async_analyze_ddl
        
        async def fake_to_thread(func, *args, **kwargs):
            if func.__name__ == "run_table_worker":
                return await mock_run_table_worker(*args, **kwargs)
            return await asyncio.sleep(0)

        mock_to_thread.side_effect = fake_to_thread
        
        result = await run_migration_pipeline(req, "test_dag_job")
        
        assert result["status"] == "success"
        
        def index_of(event):
            return execution_log.index(event)

        print("Execution log:", execution_log)
        
        assert index_of("START departments") < index_of("END departments")
        
        assert index_of("START employees") > max(index_of("END departments"), index_of("END customers"))
        assert index_of("START orders") > max(index_of("END departments"), index_of("END customers"))
        
        assert index_of("START order_items") > max(index_of("END employees"), index_of("END orders"))
