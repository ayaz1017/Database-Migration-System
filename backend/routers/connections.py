from backend.connectors import get_connector
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ConnectionTestRequest(BaseModel):
    db_type: str
    host: str
    port: int
    database: str
    user: str
    password: str


@router.post("/test")
async def test_connection(req: ConnectionTestRequest):
    try:
        connector = get_connector(
            db_type=req.db_type,
            host=req.host,
            port=req.port,
            database=req.database,
            user=req.user,
            password=req.password,
        )
        result = connector.test_connection()
        if result["status"] == "success":
            return {"status": "success", "message": "Connection verified"}
        else:
            raise HTTPException(status_code=400, detail="Connection failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/")
async def save_connection(req: ConnectionTestRequest):
    # In a real app, encrypt the password and save to SQLite/Postgres
    return {"status": "success", "connection_id": "12345"}


from async_lru import alru_cache

@router.get("/")
@alru_cache(maxsize=32)
async def list_connections():
    # Mock data
    return [
        {"id": "1", "name": "Prod MSSQL", "db_type": "mssql"},
        {"id": "2", "name": "Dev PostgreSQL", "db_type": "postgresql"},
    ]
