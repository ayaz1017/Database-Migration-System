import asyncio
import os
import time

from backend.main import run_migration_pipeline, MigrationRequest, ConnectionConfig
from backend.models import MigrationOptions

async def main():
    source_conf = ConnectionConfig(
        db_type="mysql", host="localhost", port=3306,
        username="root", password="Ayaz@123", database="large_test_db"
    )
    target_conf = ConnectionConfig(
        db_type="postgres", host="localhost", port=5432,
        username="postgres", password="Ayaz@123", database="migration_target"
    )

    req = MigrationRequest(
        source=source_conf,
        target=target_conf,
        mode="data_only",
        options=MigrationOptions(
            migrate_all_tables=False,
            selected_tables=["test_1m_a", "test_1m_b"],
            fk_dependency_mode="auto_include",
            auto_fix=True
        ),
        id="test_1m_migration"
    )

    print("Starting 1M+ rows migration test...")
    start_time = time.time()
    result = await run_migration_pipeline(req, job_id="test_1m_migration", org_id="default_org")
    end_time = time.time()
    
    print("\n--- MIGRATION REPORT ---")
    print(f"Total rows migrated: {result.get('total_rows')}")
    print(f"Total duration: {result.get('duration_seconds'):.2f}s")
    print(f"Rows per second: {result.get('total_rows', 0) / result.get('duration_seconds', 1):.2f}")
    print(f"Validation Score: {result.get('validation_score')}")
    if result.get("validation_report"):
        print(f"Validation Details: {result['validation_report']}")
    print("------------------------")

if __name__ == "__main__":
    asyncio.run(main())
