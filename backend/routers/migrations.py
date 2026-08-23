from backend.agents.orchestrator import orchestrator_agent
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()


class MigrationRequest(BaseModel):
    source_conn_id: str
    target_conn_id: str
    options: dict


# Mock database connections
MOCK_CONNS = {
    "1": {
        "db_type": "mssql",
        "host": "localhost",
        "port": 1433,
        "database": "source",
        "user": "sa",
        "password": "password",
    },
    "2": {
        "db_type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "target",
        "user": "postgres",
        "password": "password",
    },
}


@router.post("/")
async def start_migration(req: MigrationRequest, background_tasks: BackgroundTasks):
    job_id = "job_" + str(hash(req.source_conn_id + req.target_conn_id))[:8]

    source_conn = MOCK_CONNS.get(req.source_conn_id)
    target_conn = MOCK_CONNS.get(req.target_conn_id)

    # In a real app, this goes to Celery. For now, BackgroundTasks
    background_tasks.add_task(
        orchestrator_agent.run_migration, job_id, source_conn, target_conn, req.options
    )

    return {"status": "started", "job_id": job_id}


@router.get("/{job_id}")
async def get_migration_status(job_id: str):
    return {"job_id": job_id, "status": "running", "progress": "50%"}
