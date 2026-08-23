import pytest
import asyncio
from backend.main import update_job_metrics, broadcast_progress, migration_metrics
from backend.models import DependencyResolution


@pytest.mark.asyncio
async def test_progress_calculation_weighted_by_rows():
    job_id = "test_job_progress_weighted"
    
    # Pre-seed metrics for 5 tables of varying sizes (total: 365,150,000 rows)
    # Table 1: 350,000,000 rows
    # Table 2: 150,000 rows
    # Table 3: 5,000,000 rows (invoices)
    # Table 4: 8,000,000 rows (payments)
    # Table 5: 2,000,000 rows
    migration_metrics[job_id] = {
        "eta_seconds": None,
        "active_workers": 1,
        "rps_history": [],
        "_start": 1000.0,
        "_tables_done": {
            "big_table": 0,
            "small_table": 0,
            "invoices": 0,
            "payments": 0,
            "orders": 0,
        },
        "_tables_total": {
            "big_table": 350_000_000,
            "small_table": 150_000,
            "invoices": 5_000_000,
            "payments": 8_000_000,
            "orders": 2_000_000,
        },
    }

    # Simulate small_table (150K rows) completing first
    msg_small = {"step": "data", "status": "running", "table": "small_table", "rows_done": 150_000, "rows_total": 150_000}
    await broadcast_progress(msg_small, job_id=job_id)
    # 150K / 365.15M is ~0.04% - small table completing should NOT make progress 20% (1/5 tables)
    assert msg_small["overall_progress"] < 1.0

    # Simulate big_table (350M rows) completing
    msg_big = {"step": "data", "status": "running", "table": "big_table", "rows_done": 350_000_000, "rows_total": 350_000_000}
    await broadcast_progress(msg_big, job_id=job_id)
    # (350.15M / 365.15M) * 100 = ~95.89% - big table moves the bar significantly!
    assert msg_big["overall_progress"] > 95.0
    assert msg_big["overall_progress"] < 99.0

    # Simulate all rows done while status is still 'running'
    msg_all_done_running = {"step": "data", "status": "running", "table": "payments", "rows_done": 8_000_000, "rows_total": 8_000_000}
    migration_metrics[job_id]["_tables_done"]["invoices"] = 5_000_000
    migration_metrics[job_id]["_tables_done"]["payments"] = 8_000_000
    migration_metrics[job_id]["_tables_done"]["orders"] = 2_000_000
    await broadcast_progress(msg_all_done_running, job_id=job_id)
    
    # 100% safety check: capped at 99.0% while running
    assert msg_all_done_running["overall_progress"] == 99.0

    # Simulate final completion message
    msg_completion = {"step": "completion", "status": "completed"}
    await broadcast_progress(msg_completion, job_id=job_id)
    assert msg_completion["overall_progress"] == 100.0

    # Cleanup
    migration_metrics.pop(job_id, None)


@pytest.mark.asyncio
async def test_completion_with_unmigrated_tables_not_100():
    """Bug 1 regression test: completion must NOT show 100% if tables have 0 rows migrated."""
    job_id = "test_job_not_100"
    
    migration_metrics[job_id] = {
        "eta_seconds": None,
        "active_workers": 1,
        "rps_history": [],
        "_start": 1000.0,
        "_tables_done": {
            "orders": 2_000_000,
            "customers": 150_000,
            "invoices": 0,       # never migrated
            "payments": 0,       # never migrated
        },
        "_tables_total": {
            "orders": 2_000_000,
            "customers": 150_000,
            "invoices": 5_000_000,
            "payments": 8_000_000,
        },
    }

    # Send completion message — should NOT be 100%
    msg = {"step": "completion", "status": "success"}
    await broadcast_progress(msg, job_id=job_id)
    
    # 2.15M / 15.15M = ~14.2% — definitely not 100%
    assert msg["overall_progress"] < 20.0, f"Expected < 20% but got {msg['overall_progress']}%"
    assert msg["overall_progress"] > 10.0, f"Expected > 10% but got {msg['overall_progress']}%"

    # Cleanup
    migration_metrics.pop(job_id, None)


@pytest.mark.asyncio
async def test_completion_with_all_tables_done_shows_100():
    """When all tables are fully migrated, completion should show 100%."""
    job_id = "test_job_all_done"
    
    migration_metrics[job_id] = {
        "eta_seconds": None,
        "active_workers": 1,
        "rps_history": [],
        "_start": 1000.0,
        "_tables_done": {
            "orders": 2_000_000,
            "customers": 150_000,
            "invoices": 5_000_000,
            "payments": 8_000_000,
        },
        "_tables_total": {
            "orders": 2_000_000,
            "customers": 150_000,
            "invoices": 5_000_000,
            "payments": 8_000_000,
        },
    }

    msg = {"step": "completion", "status": "success"}
    await broadcast_progress(msg, job_id=job_id)
    
    assert msg["overall_progress"] == 100.0

    # Cleanup
    migration_metrics.pop(job_id, None)


def test_dependency_resolution_stores_migration_generations():
    """Bug 2 regression test: migration_generations must be stored on the model, not silently dropped."""
    generations = [["customers", "products"], ["orders"], ["invoices", "payments"]]
    
    resolution = DependencyResolution(
        final_table_set=["customers", "products", "orders", "invoices", "payments"],
        originally_selected=["customers", "products", "orders", "invoices", "payments"],
        auto_added=[],
        auto_added_reasons={},
        self_referencing_tables=[],
        circular_dependency_groups=[],
        blocked=False,
        missing_dependencies=[],
        dropped_constraints=[],
        migration_order=["customers", "products", "orders", "invoices", "payments"],
        migration_generations=generations,
    )
    
    # The field must exist and have the correct value — NOT be silently dropped
    assert hasattr(resolution, "migration_generations"), "migration_generations field was silently dropped by Pydantic"
    assert resolution.migration_generations == generations
    assert len(resolution.migration_generations) == 3
    assert resolution.migration_generations[0] == ["customers", "products"]
    assert resolution.migration_generations[2] == ["invoices", "payments"]
    
    # Also verify getattr works (this is how main.py accesses it)
    assert getattr(resolution, "migration_generations", []) == generations


def test_dependency_resolution_defaults_empty_generations():
    """migration_generations should default to [] when not provided (backwards compat)."""
    resolution = DependencyResolution(
        final_table_set=["t1"],
        originally_selected=["t1"],
        auto_added=[],
        auto_added_reasons={},
        self_referencing_tables=[],
        circular_dependency_groups=[],
        blocked=False,
        missing_dependencies=[],
        dropped_constraints=[],
        migration_order=["t1"],
    )
    
    assert resolution.migration_generations == []
    assert getattr(resolution, "migration_generations", []) == []
