from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks, Query, Depends
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
import os
import re
from dotenv import load_dotenv

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path, override=True)
api_key = os.environ.get("OPENAI_API_KEY")
if api_key:
    print(f"OpenAI API key loaded: [REDACTED, ends in ...{api_key[-4:]}]")
else:
    print("WARNING: OpenAI API key not found in environment")


from backend.services.discovery_service import DiscoveryService
from backend.agents.schema_agent import SchemaAgent
from backend.agents.validation_agent import ValidationAgent
from backend.execution.mssql_execution_engine import MSSQLExecutionEngine
from backend.execution.mysql_execution_engine import MySQLExecutionEngine
from backend.execution.postgres_execution_engine import PostgresExecutionEngine
from backend.execution.oracle_execution_engine import OracleExecutionEngine
from backend.routers.auth import router as auth_router
from backend.services.auth_service import get_current_user

app = FastAPI(title="Universal Migration Engine")
app.include_router(auth_router)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.services.cache_service import cache

from typing import Dict
active_websockets: Dict[str, WebSocket] = {}

import sqlite3
import json
import datetime

# SQLite database setup
DB_FILE = os.environ.get("DB_PATH", "migrations.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_jobs (
            id TEXT PRIMARY KEY,
            org_id TEXT,
            source_db TEXT,
            target_db TEXT,
            status TEXT,
            tables_migrated INTEGER,
            rows_migrated INTEGER,
            duration TEXT,
            timestamp TEXT,
            full_payload TEXT,
            user_id TEXT
        )
    """)
    # Ensure org_id, user_id, and full_payload exist for existing databases
    cursor.execute("PRAGMA table_info(migration_jobs)")
    columns = [row[1] for row in cursor.fetchall()]
    if "org_id" not in columns:
        cursor.execute("ALTER TABLE migration_jobs ADD COLUMN org_id TEXT")
        cursor.execute("UPDATE migration_jobs SET org_id = 'default_org' WHERE org_id IS NULL")
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE migration_jobs ADD COLUMN user_id TEXT")
    if "full_payload" not in columns:
        cursor.execute("ALTER TABLE migration_jobs ADD COLUMN full_payload TEXT")

    # Indexes for efficient history queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON migration_jobs(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_timestamp ON migration_jobs(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_org_id ON migration_jobs(org_id)")
    # Migration logs table for persistent log storage
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migration_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            level TEXT DEFAULT 'info',
            step TEXT,
            message TEXT,
            metadata TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_job_id ON migration_logs(job_id, log_id)")

    # Auth tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            org_id TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL,
            oauth_provider TEXT,
            oauth_provider_id TEXT,
            avatar_url TEXT,
            name TEXT,
            FOREIGN KEY(org_id) REFERENCES organizations(id)
        )
    """)
    # Migration: Ensure oauth_provider, oauth_provider_id, avatar_url, name exist on users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [row[1] for row in cursor.fetchall()]
    if "oauth_provider" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN oauth_provider TEXT")
    if "oauth_provider_id" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN oauth_provider_id TEXT")
    if "avatar_url" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
    if "name" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_oauth ON users(oauth_provider, oauth_provider_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        from backend.services.auth_service import get_password_hash
        hashed_pw = get_password_hash("admin")
        cursor.execute("INSERT OR IGNORE INTO organizations (id, name) VALUES (?, ?)", ("2517228a-aff0-4c0d-9a2c-8e326d00ca9c", "Default Workspace Org"))
        cursor.execute(
            "INSERT INTO users (id, org_id, email, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
            ("default_admin", "2517228a-aff0-4c0d-9a2c-8e326d00ca9c", "admin@example.com", hashed_pw, "Admin")
        )

    conn.commit()
    conn.close()

def persist_log(job_id: str, message: dict):
    """Persist a log entry to the migration_logs table."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO migration_logs (job_id, timestamp, level, step, message, metadata) VALUES (?, ?, ?, ?, ?, ?)",
            (
                job_id,
                datetime.datetime.now().isoformat(),
                message.get("status", "info"),
                message.get("step", ""),
                message.get("message", json.dumps({k: v for k, v in message.items() if k not in ("step", "status", "message")})),
                json.dumps(message),
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # Log persistence must never block migration execution

init_db()

class ConnectionConfig(BaseModel):
    db_type: str
    host: str
    port: int
    username: str
    password: str
    database: str

from typing import Literal
from backend.models import FKEdge, DependencyResolution, TableGroupResult, MigrationOptions

class ResolveDependenciesRequest(BaseModel):
    config: ConnectionConfig
    selected_tables: list[str]
    fk_dependency_mode: Literal["auto_include", "strict", "drop_constraint"] = "auto_include"

class MigrationRequest(BaseModel):
    source: ConnectionConfig
    target: ConnectionConfig
    mode: str
    options: MigrationOptions = MigrationOptions()
    id: str | None = None

def get_engine(config: ConnectionConfig):
    if config.db_type.lower() == "mssql":
        return MSSQLExecutionEngine(config.host, config.port, config.username, config.password, config.database)
    elif config.db_type.lower() == "mysql":
        return MySQLExecutionEngine(config.host, config.port, config.username, config.password, config.database)
    elif config.db_type.lower() in ["postgres", "postgresql"]:
        return PostgresExecutionEngine(config.host, config.port, config.username, config.password, config.database)
    elif config.db_type.lower() == "oracle":
        return OracleExecutionEngine(config.host, config.port, config.username, config.password, config.database)
    else:
        raise ValueError(f"Unsupported db_type: {config.db_type}")

from contextlib import asynccontextmanager

@asynccontextmanager
async def run_stage(job_id: str, stage_id: str, label: str):
    await broadcast_progress({
        "type": "stage_update",
        "stage": stage_id,
        "status": "in_progress",
        "message": f"Starting {label}..."
    }, job_id=job_id)
    try:
        yield
        await broadcast_progress({
            "type": "stage_update",
            "stage": stage_id,
            "status": "completed",
            "message": f"Completed {label}"
        }, job_id=job_id)
    except Exception as e:
        await broadcast_progress({
            "type": "stage_update",
            "stage": stage_id,
            "status": "failed",
            "message": str(e)
        }, job_id=job_id)
        raise e

async def broadcast_progress(message: dict, job_id: str | None = None):
    # Persist to SQLite (non-blocking via to_thread)
    if job_id:
        try:
            await asyncio.to_thread(persist_log, job_id, message)
        except Exception:
            pass
    
    for ws in list(active_websockets.values()):
        try:
            await ws.send_json(message)
        except Exception:
            pass

@app.post("/discover")
@app.post("/api/discover")
def discover(config: ConnectionConfig):
    try:
        discovery_service = DiscoveryService()
        source_schema = discovery_service.connect_and_discover(
            config.host, config.port, config.username, config.password, config.db_type, config.database
        )
        return source_schema
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/discover/tables")
async def discover_tables(config: ConnectionConfig):
    cache_key = cache.make_key("discover_tables", config.host, config.port, config.db_type, config.database, config.username)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        discovery_service = DiscoveryService()
        result = await asyncio.to_thread(
            discovery_service.list_tables_only,
            config.host, config.port, config.username, config.password, config.db_type, config.database
        )
        cache.set(cache_key, result, ttl_seconds=60, tags=["discover_tables"])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/discover/resolve_dependencies")
def resolve_dependencies(req: ResolveDependenciesRequest):
    try:
        discovery_service = DiscoveryService()
        result = discovery_service.list_tables_only(
            req.config.host, req.config.port, req.config.username, req.config.password, req.config.db_type, req.config.database
        )
        all_tables_metadata = result.get("tables", [])
        
        schema_agent = SchemaAgent()
        resolution = schema_agent.resolve_table_dependencies(
            selected_tables=req.selected_tables,
            all_tables_metadata=all_tables_metadata,
            mode=req.fk_dependency_mode
        )
        return resolution.dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health():
    import pyodbc
    import shutil
    import subprocess
    import platform
    
    mssql_driver = "ODBC Driver 17 for SQL Server" in pyodbc.drivers()
    
    pgloader_available = False
    pgloader_mode = "not_found"
    os_name = platform.system().lower()
    
    if os_name == "windows":
        try:
            res = subprocess.run(["wsl", "which", "pgloader"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                pgloader_available = True
                pgloader_mode = "wsl_pgloader"
        except Exception:
            pass
    elif shutil.which("pgloader"):
        pgloader_available = True
        pgloader_mode = "native"
        
    return {
        "status": "ok",
        "mssql_driver": mssql_driver,
        "pgloader_available": pgloader_available,
        "pgloader_mode": pgloader_mode,
        "version": "1.0.0"
    }

import time

@app.get("/api/health/llm")
async def health_llm():
    from backend.services.llm_service import LLMService
    import os

    cache_key = "llm_health"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    try:
        service = LLMService()
        await service.generate_response("Respond with OK")
        result = {"llm_available": True, "error": None, "model": model_name}
    except Exception as e:
        result = {"llm_available": False, "error": str(e), "model": model_name}

    cache.set(cache_key, result, ttl_seconds=30, tags=["llm_health"])
    return result

is_migrating = False
migration_start_time = 0

@app.on_event("startup")
def cleanup_stale_jobs():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE migration_jobs SET status = 'FAILED: Server Restarted' WHERE status = 'IN_PROGRESS' OR status = 'RUNNING'")
        conn.commit()
        conn.close()
    except Exception as e:
        print("Failed to clean up stale jobs on startup:", e)

@app.post("/api/migrations/clear_lock")
def clear_lock():
    global is_migrating, migration_start_time
    is_migrating = False
    migration_start_time = 0
    return {"status": "success", "message": "Migration lock cleared."}

def get_raw_conn(conf):
    import pyodbc, psycopg2, mysql.connector, oracledb
    if conf.db_type.lower() == "mssql":
        def _config(c):
            c.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
            c.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
            c.setencoding(encoding='utf-8')
            return c
        try:
            return _config(pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={conf.host},{conf.port};UID={conf.username};PWD={conf.password};DATABASE={conf.database}", autocommit=True))
        except Exception as e:
            if conf.host.lower() in ("localhost", "127.0.0.1"):
                alt_host = "127.0.0.1" if conf.host.lower() == "localhost" else "localhost"
                return _config(pyodbc.connect(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={alt_host},{conf.port};UID={conf.username};PWD={conf.password};DATABASE={conf.database}", autocommit=True))
            raise e
    elif conf.db_type.lower() == "mysql":
        try:
            return mysql.connector.connect(host=conf.host, port=conf.port, user=conf.username, password=conf.password, database=conf.database)
        except Exception as e:
            if conf.host.lower() in ("localhost", "127.0.0.1"):
                alt_host = "127.0.0.1" if conf.host.lower() == "localhost" else "localhost"
                return mysql.connector.connect(host=alt_host, port=conf.port, user=conf.username, password=conf.password, database=conf.database)
            raise e
    elif conf.db_type.lower() in ["postgres", "postgresql"]:
        return psycopg2.connect(host=conf.host, port=conf.port, user=conf.username, password=conf.password, dbname=conf.database)
    elif conf.db_type.lower() == "oracle":
        return oracledb.connect(user=conf.username, password=conf.password, dsn=f"{conf.host}:{conf.port}/{conf.database}")
    else:
        raise ValueError(f"Unsupported db_type: {conf.db_type}")

def check_oracle_target_privileges(conn, username: str):
    """Pre-flight check: verify Oracle target user has privileges needed for DDL migration."""
    cursor = conn.cursor()
    
    required_privs = [
        'CREATE TABLE', 'CREATE SEQUENCE', 'CREATE TRIGGER', 
        'CREATE SESSION', 'CREATE VIEW', 'CREATE PROCEDURE',
        'CREATE TYPE', 'CREATE INDEX'
    ]
    missing = []
    for priv in required_privs:
        cursor.execute("SELECT COUNT(*) FROM SESSION_PRIVS WHERE PRIVILEGE = :priv", {"priv": priv})
        count = cursor.fetchone()[0]
        if count == 0:
            missing.append(priv)
    
    # Check tablespace quota
    has_quota = False
    try:
        cursor.execute("SELECT MAX_BYTES FROM USER_TS_QUOTAS WHERE ROWNUM = 1")
        row = cursor.fetchone()
        has_quota = row is not None and (row[0] == -1 or row[0] > 0)
    except Exception:
        pass  # USER_TS_QUOTAS may not be accessible — treat as no quota
    
    cursor.close()
    
    if missing or not has_quota:
        user_upper = username.upper()
        error_parts = []
        if missing:
            error_parts.append(f"Missing Oracle privileges: {', '.join(missing)}")
        if not has_quota:
            error_parts.append("No tablespace quota assigned")
        
        grant_lines = [f"GRANT {p} TO {user_upper};" for p in missing]
        grant_lines.append(f"ALTER USER {user_upper} QUOTA UNLIMITED ON USERS;")
        
        raise PermissionError(
            "Oracle target user lacks required privileges. "
            + " | ".join(error_parts)
            + "\n\nRun as SYSDBA:\n"
            + "\n".join(grant_lines)
        )
    
    return True

def test_connection_config(conf, label: str = "Database"):
    try:
        conn = get_raw_conn(conf)
        if hasattr(conn, "close"):
            conn.close()
        return True, None
    except Exception as e:
        err_str = str(e)
        is_missing_db = ("1049" in err_str or "unknown database" in err_str.lower() or "does not exist" in err_str.lower() or "3d000" in err_str.lower())
        if is_missing_db and getattr(conf, "database", None):
            try:
                class ConfNoDb:
                    def __init__(self, c):
                        self.db_type = getattr(c, "db_type", "")
                        self.host = getattr(c, "host", "")
                        self.port = getattr(c, "port", 0)
                        self.username = getattr(c, "username", "")
                        self.password = getattr(c, "password", "")
                        self.database = ""
                conn = get_raw_conn(ConfNoDb(conf))
                if hasattr(conn, "close"):
                    conn.close()
                return True, None
            except Exception as e2:
                err_str = str(e2)
        return False, f"Connection test failed for {label} ({conf.db_type} on {conf.host}:{conf.port}): {err_str}"

@app.post("/api/test-db")
def test_db(config: ConnectionConfig):
    ok, err = test_connection_config(config, label="Database")
    if not ok:
        raise HTTPException(status_code=400, detail=err)
    return {"status": "success", "message": f"Successfully verified connection to {config.db_type} at {config.host}:{config.port}"}

def clean_ddl(ddl: str, dialect: str = "") -> str:
    import re
    if not ddl or not ddl.strip():
        return ""
    clean = ddl.strip()

    # Remove single line comments
    clean = re.sub(r'--[^\n]*', '', clean)
    # Remove block comments
    clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)

    # Clean MySQL DELIMITER directives if present
    clean = re.sub(r'(?i)^\s*DELIMITER\s+\S+\s*', '', clean)
    clean = re.sub(r'(?i)\s*DELIMITER\s+;\s*$', '', clean)
    clean = re.sub(r'(?i)DELIMITER\s+\S+\s*\n', '\n', clean)

    return clean.strip()

def execute_mssql_ddl(cursor, ddl: str):
    import re
    if not ddl or not ddl.strip():
        return
    # Split on GO separator
    batches = re.split(
        r'^\s*GO\s*$', ddl,
        flags=re.MULTILINE | re.IGNORECASE
    )
    for batch in batches:
        batch = batch.strip()
        if batch:
            try:
                cursor.execute(batch)
            except Exception as e:
                raise Exception(
                    f"MSSQL DDL failed: {str(e)}\n"
                    f"DDL attempted:\n"
                    f"{batch[:500]}"
                )

def execute_ddl(cursor, ddl: str, dialect: str):
    import re
    if not ddl or not ddl.strip():
        return
    dialect = dialect.lower()
    clean_sql = clean_ddl(ddl, dialect)
    if not clean_sql:
        return

    # Handle MSSQL batches via GO
    if dialect in ["mssql", "sqlserver", "sql server"]:
        execute_mssql_ddl(cursor, clean_sql)
        return

    # For MySQL: multi-statement object handling
    if dialect == "mysql":
        # Safely remove DELIMITER commands without crossing newlines
        ddl_clean = re.sub(r'(?i)^[ \t]*(\$\$[ \t]*)?DELIMITER[ \t]*.*$', '', clean_sql, flags=re.MULTILINE)
        ddl_clean = re.sub(r'\$\$[ \t]*$', '', ddl_clean, flags=re.MULTILINE)
        ddl_clean = ddl_clean.replace('$$', '').strip()
        
        try:
            # Extract and execute any DROP statements first
            while True:
                drop_match = re.match(r'(?i)^\s*(DROP\s+(PROCEDURE|FUNCTION|TRIGGER)\s+IF\s+EXISTS\s+[a-zA-Z0-9_`]+)\s*;?', ddl_clean)
                if not drop_match:
                    break
                cursor.execute(drop_match.group(1))
                ddl_clean = ddl_clean[drop_match.end():].strip()
                
            # Execute the remaining CREATE statement
            if ddl_clean:
                cursor.execute(ddl_clean)
            return
        except Exception:
            raise

    # Dollar-quote-aware multi-statement splitter for PostgreSQL
    # Splits on blank-line boundaries while respecting $$ ... $$ blocks
    if dialect in ["postgres", "postgresql"] and "$$" in clean_sql:
        statements = []
        current = []
        in_dollar_quote = False
        for line in clean_sql.splitlines():
            stripped = line.strip()
            # Track $$ open/close
            dollar_count = stripped.count("$$")
            if dollar_count % 2 == 1:
                in_dollar_quote = not in_dollar_quote
            # Blank line boundary outside $$ block = statement separator
            if not stripped and not in_dollar_quote and current:
                stmt = "\n".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
            else:
                current.append(line)
        if current:
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)

        for stmt in statements:
            if stmt:
                cursor.execute(stmt if stmt.rstrip().endswith(";") else stmt + ";")
        return

    # Simple multi-statement split on blank-line boundaries (non-Postgres)
    if ";\n\n" in clean_sql or ";\r\n\r\n" in clean_sql:
        statements = [s.strip() for s in re.split(r';\s*\n\s*\n', clean_sql) if s.strip()]
        for stmt in statements:
            if stmt:
                cursor.execute(stmt if stmt.endswith(";") else stmt + ";")
        return

    uppercase_ddl = clean_sql.upper()
    if any(kw in uppercase_ddl for kw in ["CREATE PROCEDURE", "CREATE FUNCTION", "CREATE TRIGGER", "CREATE VIEW", "CREATE OR REPLACE"]):
        cursor.execute(clean_sql)
        return

    if dialect in ["postgres", "postgresql", "mysql"]:
        parts = re.split(r';\s*(?=\n|\r|$)', clean_sql)
        for part in parts:
            stmt = part.strip()
            if stmt:
                cursor.execute(stmt)
    else:
        cursor.execute(clean_sql)

async def auto_apply_object(obj, translated_ddl: str, cursor, target_config):
    import re
    obj_name = getattr(obj, "name", str(obj)) if hasattr(obj, "name") else (obj.get("name") if isinstance(obj, dict) else str(obj))
    db_type = getattr(target_config, "db_type", None) or (target_config.get("db_type") if isinstance(target_config, dict) else str(target_config))

    try:
        # Clean up DDL
        cleaned_ddl = clean_ddl(translated_ddl, db_type)
        if not cleaned_ddl:
            return {"status": "skipped", "object": obj_name}

        # Execute on target
        execute_ddl(cursor, cleaned_ddl, db_type)

        return {
            "status": "applied",
            "object": obj_name
        }

    except NameError as e:
        # Python code bug — missing import
        raise Exception(
            f"Internal error (missing import): {str(e)}. Please report this bug."
        )

    except SyntaxError as e:
        # Bad DDL syntax
        raise Exception(
            f"DDL syntax error in '{obj_name}': {str(e)}\n"
            f"The LLM translation may have produced invalid {db_type} SQL."
        )

    except Exception as e:
        error_str = str(e)

        # Database-specific errors
        if '42601' in error_str or 'syntax error' in error_str.lower():
            raise Exception(
                f"SQL syntax error applying '{obj_name}': {error_str}"
            )
        elif 'permission' in error_str.lower() or 'privilege' in error_str.lower():
            raise Exception(
                f"Insufficient privileges to create '{obj_name}' on target database."
            )
        else:
            raise Exception(
                f"Failed to apply '{obj_name}': {error_str}"
            )

class ApproveObjectRequest(BaseModel):
    object_name: str
    object_type: str
    action: Literal["approve", "skip"]
    approved_definition: str | None = None

@app.post("/api/discover/objects")
def discover_objects(config: ConnectionConfig):
    try:
        discovery_service = DiscoveryService()
        result = discovery_service.list_migratable_objects(
            config.host, config.port, config.username, config.password, config.db_type, config.database
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/migrations/{job_id}/approve_object")
async def approve_object(job_id: str, req: ApproveObjectRequest, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT full_payload FROM migration_jobs WHERE id = ? AND org_id = ?", (job_id, current_user["org_id"]))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Migration job not found")
        
    full_payload = json.loads(row[0])
    
    source_conf_dict = full_payload.get("_source_config")
    target_conf_dict = full_payload.get("_target_config")
    
    if not source_conf_dict or not target_conf_dict:
        conn.close()
        raise HTTPException(status_code=400, detail="Connection configurations not stored in job payload")
        
    source_conf = ConnectionConfig(**source_conf_dict)
    target_conf = ConnectionConfig(**target_conf_dict)
    
    translations = full_payload.get("object_translations", [])
    obj_index = next((i for i, t in enumerate(translations) if t["object_name"] == req.object_name and t["object_type"] == req.object_type), None)
    
    if obj_index is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Object not found in migration job translations")
        
    obj_translation = translations[obj_index]
    
    if req.action == "skip":
        obj_translation["approved_by_user"] = True
        obj_translation["needs_human_review"] = False
        obj_translation["skipped"] = True
        obj_translation["status"] = "skipped"
        obj_translation["compile_status"] = "Skipped by user"
        obj_translation["translation_error"] = None
        
    elif req.action == "approve":
        ddl_to_apply = req.approved_definition or obj_translation["translated_definition"]
        obj_translation["translated_definition"] = ddl_to_apply
        
        try:
            target_raw = get_raw_conn(target_conf)
            target_cursor = target_raw.cursor()
            execute_ddl(target_cursor, ddl_to_apply, target_conf.db_type)
            if hasattr(target_raw, "commit"):
                target_raw.commit()
                
            val_agent = ValidationAgent()
            compile_status = val_agent.validate_compiled_object(target_raw, target_conf.db_type, req.object_name, req.object_type)
            target_raw.close()
            
            if compile_status["compiled"]:
                obj_translation["approved_by_user"] = True
                obj_translation["needs_human_review"] = False
                obj_translation["status"] = "applied"
                obj_translation["compile_status"] = "Compiled successfully"
                obj_translation["translation_error"] = None
            else:
                obj_translation["compile_status"] = "Compile error"
                obj_translation["translation_error"] = compile_status["error"]
                
                # AI Fix retry loop
                from backend.agents.object_translation_agent import ObjectTranslationAgent
                translation_agent = ObjectTranslationAgent()
                fixed_res = await translation_agent.retry_translation_after_compile_error(
                    obj_translation, target_conf.db_type, compile_status["error"], source_database=source_conf.database if source_conf else None
                )
                obj_translation["translated_definition"] = fixed_res.translated_definition
                obj_translation["needs_human_review"] = True
                obj_translation["approved_by_user"] = False
                obj_translation["status"] = "needs_review_after_fix"
                obj_translation["translation_error"] = f"Previous compile error: {compile_status['error']}. AI has proposed a fix."
                
        except Exception as e:
            obj_translation["compile_status"] = "Compile error"
            obj_translation["translation_error"] = str(e)
            
            # AI Fix loop
            from backend.agents.object_translation_agent import ObjectTranslationAgent
            translation_agent = ObjectTranslationAgent()
            fixed_res = await translation_agent.retry_translation_after_compile_error(
                obj_translation, target_conf.db_type, str(e), source_database=source_conf.database if source_conf else None
            )
            obj_translation["translated_definition"] = fixed_res.translated_definition
            obj_translation["needs_human_review"] = True
            obj_translation["approved_by_user"] = False
            obj_translation["status"] = "needs_review_after_fix"
            obj_translation["translation_error"] = f"Previous execution error: {str(e)}. AI has proposed a fix."
            
    pending_review_count = sum(1 for res in translations if res["needs_human_review"] and not res["approved_by_user"])
    if pending_review_count > 0:
        new_status = f"COMPLETED — {pending_review_count} objects awaiting review"
    else:
        compile_errors_count = sum(1 for res in translations if res.get("compile_status") == "Compile error")
        if compile_errors_count > 0:
            new_status = f"COMPLETED — {compile_errors_count} compile errors"
        else:
            new_status = "SUCCESS"
            
    full_payload["status"] = new_status.lower() if "awaiting review" not in new_status and "compile errors" not in new_status else new_status
    full_payload["object_translations"] = translations
    
    # Save back
    cursor.execute("""
        UPDATE migration_jobs 
        SET status = ?, full_payload = ?
        WHERE id = ?
    """, (new_status, json.dumps(full_payload), job_id))
    conn.commit()
    conn.close()
    
    # Broadcast status change
    await broadcast_progress({"step": "approval_update", "status": new_status, "object_name": req.object_name})
    
    return full_payload

async def run_migration_pipeline(req: MigrationRequest, job_id: str):
    import time
    start_time = time.time()
    try:
        # Step 1: Connect and Pre-Flight Verification
        async with run_stage(job_id, "connect", f"Verifying Connections for Source & Target"):
            # Pre-flight check Source Connection
            ok_src, err_src = test_connection_config(req.source, label="SOURCE")
            if not ok_src:
                await broadcast_progress({"step": "error", "status": "failed", "message": err_src}, job_id=job_id)
                raise RuntimeError(err_src)

            # Pre-flight check Target Connection
            ok_tgt, err_tgt = test_connection_config(req.target, label="TARGET")
            if not ok_tgt:
                await broadcast_progress({"step": "error", "status": "failed", "message": err_tgt}, job_id=job_id)
                raise RuntimeError(err_tgt)

            await broadcast_progress({"step": "info", "message": "Pre-flight check passed: Source and Target connections verified successfully."}, job_id=job_id)

            discovery_service = DiscoveryService()
            source_schema = discovery_service.connect_and_discover(
                req.source.host, req.source.port, req.source.username, req.source.password, req.source.db_type, req.source.database
            )
            
        async with run_stage(job_id, "discovery", "Extracting schema"):
            schema_agent = SchemaAgent()
            all_tables_metadata = source_schema.get("tables", [])
            
            if not req.options.migrate_all_tables:
                resolution = schema_agent.resolve_table_dependencies(
                    req.options.selected_tables,
                    all_tables_metadata,
                    req.options.fk_dependency_mode
                )
                if resolution.blocked:
                    raise RuntimeError(f"Strict mode blocked migration due to missing dependencies: {resolution.missing_dependencies}")
                
                # Filter source schema to ONLY include final_table_set
                source_schema["tables"] = [t for t in all_tables_metadata if t["name"] in resolution.final_table_set]
            else:
                resolution = schema_agent.resolve_table_dependencies(
                    [t["name"] for t in all_tables_metadata],
                    all_tables_metadata,
                    "auto_include"
                )
            
            await broadcast_progress({"type": "stage_details", "tables": [t["name"] for t in source_schema.get("tables", [])]}, job_id=job_id)
        
        # Step 2: Schema generation
        async with run_stage(job_id, "schema", "Transforming DDL"):
            # Pre-flight: check Oracle target privileges before attempting any DDL
            if req.target.db_type.lower() == "oracle":
                await broadcast_progress({"step": "info", "message": "Checking Oracle target privileges..."}, job_id=job_id)
                preflight_conn = None
                try:
                    preflight_conn = get_raw_conn(req.target)
                    check_oracle_target_privileges(preflight_conn, req.target.username)
                    await broadcast_progress({"step": "info", "message": "Oracle privileges: OK"}, job_id=job_id)
                except PermissionError as perm_err:
                    await broadcast_progress({"step": "error", "status": "failed", "message": str(perm_err)}, job_id=job_id)
                    raise RuntimeError(str(perm_err))
                finally:
                    if preflight_conn:
                        try:
                            preflight_conn.close()
                        except Exception:
                            pass

            schema_agent = SchemaAgent()
            direction = f"{req.source.db_type.lower()}_to_{req.target.db_type.lower()}"
            ddl_result = schema_agent.generate_ddl(source_schema, direction)
            
            # Step 3: LLM Analysis
            if getattr(req, "mode", "") == "data_only":
                analysis_report = {"status": "skipped"}
            else:
                analysis_report = await schema_agent.analyze_ddl(ddl_result["ddl_statements"])
            
            # Step 4: Apply DDL
            target_raw = get_raw_conn(req.target)
            cursor = target_raw.cursor()
            for stmt in ddl_result["ddl_statements"]:
                try:
                    cursor.execute(stmt)
                    if hasattr(target_raw, "commit"):
                        target_raw.commit()
                except Exception as e:
                    if hasattr(target_raw, "rollback"):
                        target_raw.rollback()
                    
                    error_str = str(e)
                    error_msg = error_str.lower()
                    
                    if req.target.db_type.lower() == 'oracle':
                        if 'ORA-01031' in error_str:
                            friendly_error = (
                                "Oracle insufficient privileges. "
                                "The connected Oracle user lacks "
                                "permission to create database "
                                "objects. Grant required privileges "
                                "using SYSDBA:\n\n"
                                "GRANT CREATE TABLE TO {user};\n"
                                "GRANT CREATE SEQUENCE TO {user};\n"
                                "GRANT CREATE TRIGGER TO {user};\n"
                                "ALTER USER {user} QUOTA "
                                "UNLIMITED ON USERS;\n\n"
                                "See Settings → Oracle Setup "
                                "for full instructions."
                            ).format(
                                user=req.target.username.upper()
                            )
                            await broadcast_progress({"type": "log", "level": "ERROR", "message": friendly_error}, job_id=job_id)
                            raise ValueError(friendly_error)
                        
                        elif 'ORA-01536' in error_str or 'ORA-01950' in error_str:
                            friendly_error = (
                                "Oracle tablespace quota exceeded. "
                                f"Run: ALTER USER {req.target.username.upper()} "
                                "QUOTA UNLIMITED ON USERS;"
                            )
                            await broadcast_progress({"type": "log", "level": "ERROR", "message": friendly_error}, job_id=job_id)
                            raise ValueError(friendly_error)
                            
                        elif 'ORA-00955' in error_str:
                            await broadcast_progress({"type": "log", "level": "WARN", "message": f"Object already exists on target Oracle (skipping): {error_str}"}, job_id=job_id)
                            continue

                    if "already exists" not in error_msg and "already an object" not in error_msg and "1050" not in error_msg and "2714" not in error_msg:
                        raise e
            target_raw.close()
            
            await broadcast_progress({"type": "stage_details", "ddl_count": len(ddl_result["ddl_statements"])}, job_id=job_id)
            
       
        source_engine = get_engine(req.source)
        target_engine = get_engine(req.target)
        
        from backend.execution.transaction_manager import TransactionManager
        import time
        import os
        
        async with run_stage(job_id, "data", "Migrating Data"):
            def get_chunk_size(row_count: int) -> int:
                if not row_count or row_count < 10000: return int(os.environ.get("CHUNK_SIZE_TIER1", 1000))
                if row_count < 100000: return int(os.environ.get("CHUNK_SIZE_TIER2", 5000))
                if row_count < 1000000: return int(os.environ.get("CHUNK_SIZE_TIER3", 10000))
                return int(os.environ.get("CHUNK_SIZE_TIER4", 25000))
            
            total_inserted = 0
            migrated_tables = set()
        
            cyclic_groups = resolution.circular_dependency_groups
            self_refs = resolution.self_referencing_tables
        
            groups_to_migrate = []
            for g in cyclic_groups:
                groups_to_migrate.append(g)
            for t in self_refs:
                if not any(t in g for g in cyclic_groups):
                    groups_to_migrate.append([t])
                
            last_bcast = 0
            async def throttled_broadcast(payload):
                nonlocal last_bcast
                now = time.time()
                if payload.get("status") == "done" or (now - last_bcast) > 0.1:
                    await broadcast_progress(payload, job_id=job_id)
                    last_bcast = now
                
            # Phase 1: Sequential Cyclic Groups
            for group in groups_to_migrate:
                target_raw = get_raw_conn(req.target)
                tm = TransactionManager(target_raw, req.target.db_type, group, job_id=job_id)
                if not tm.check_privileges():
                    tm.close()
                    target_raw.close()
                    raise RuntimeError(tm.get_missing_privilege_error(req.target.username))
                
                tm.begin_transaction()
                group_inserted = 0
                txn_start = time.time()
                try:
                    tm.disable_constraints()
                    for table_name in group:
                        table_schema_obj = next((t for t in source_schema["tables"] if t["name"] == table_name), None)
                        if not table_schema_obj: continue
                    
                        row_count = table_schema_obj.get("row_count", 0)
                        chunk_size = get_chunk_size(row_count)
                        await broadcast_progress({"type": "table_progress", "step": "data", "status": "running", "table": table_name, "rows_done": 0, "rows_total": row_count}, job_id=job_id)
                    
                        tm.disable_indexes_for_table(table_name, row_count)
                    
                        if hasattr(source_engine, "stream_table"):
                            if req.source.db_type.lower() == "mysql":
                                pk = table_schema_obj.get("primary_keys", ["id"])[0] if table_schema_obj.get("primary_keys") else table_schema_obj.get("columns", [{"name": "id"}])[0]["name"]
                                stream = source_engine.stream_table(table_name, pk, chunk_size=chunk_size)
                            else:
                                if req.source.db_type.lower() == "mssql":
                                    stream = source_engine.stream_table(table_name, chunk_size=chunk_size, table_schema=table_schema_obj)
                                else:
                                    stream = source_engine.stream_table(table_name, chunk_size=chunk_size)
                                
                            table_inserted = 0
                            for chunk in stream:
                                inserted = tm.bulk_insert_chunk(table_name, chunk)
                                actual_inserted = len(chunk) if inserted < 0 else inserted
                                table_inserted += actual_inserted
                                group_inserted += actual_inserted
                                await asyncio.sleep(0)
                                await throttled_broadcast({"type": "table_progress", "step": "data", "status": "running", "table": table_name, "rows_done": table_inserted, "rows_total": row_count})
                            
                        tm.enable_indexes_for_table(table_name)
                        migrated_tables.add(table_name)
                
                    tm.enable_constraints()
                    violations = tm.validate_constraints()
                    if violations:
                        raise RuntimeError(f"Constraint violations found: {violations}")
                    tm.commit()
                    total_inserted += group_inserted
                    if time.time() - txn_start > 300:
                        print(f"WARNING: Transaction for group {group} took longer than 300 seconds.")
                except Exception as e:
                    tm.rollback()
                    for table_name in group:
                        tm.enable_indexes_for_table(table_name)
                    raise RuntimeError(f"Transaction failed for group {group}: {e}")
                finally:
                    tm.close()
                    target_raw.close()

            # Phase 2: Parallel Independent Tables by Topological Generation
            MAX_PARALLEL_TABLES = int(os.environ.get("MAX_PARALLEL_TABLES", 4))
            semaphore = asyncio.Semaphore(MAX_PARALLEL_TABLES)
        
            def run_table_worker(table_name, row_count, table_schema_obj, loop):
                worker_src = get_engine(req.source)
                worker_tgt_raw = get_raw_conn(req.target)
                tm = TransactionManager(worker_tgt_raw, req.target.db_type, [table_name], job_id=job_id)
                try:
                    tm.begin_transaction()
                    tm.disable_indexes_for_table(table_name, row_count)
                
                    chunk_size = get_chunk_size(row_count)
                    if hasattr(worker_src, "stream_table"):
                        if req.source.db_type.lower() == "mysql":
                            pk = table_schema_obj.get("primary_keys", ["id"])[0] if table_schema_obj.get("primary_keys") else table_schema_obj.get("columns", [{"name": "id"}])[0]["name"]
                            start_pk = None
                            try:
                                # best effort max pk logic
                                tr_cur = worker_tgt_raw.cursor()
                                tr_cur.execute(f"SELECT MAX({pk}) FROM {table_name}")
                                max_val = tr_cur.fetchone()
                                if max_val and max_val[0] is not None: start_pk = max_val[0]
                            except: pass
                            stream = worker_src.stream_table(table_name, pk, chunk_size=chunk_size, start_pk=start_pk)
                        else:
                            if req.source.db_type.lower() == "mssql":
                                stream = worker_src.stream_table(table_name, chunk_size=chunk_size, table_schema=table_schema_obj)
                            else:
                                stream = worker_src.stream_table(table_name, chunk_size=chunk_size)
                            
                        table_inserted = 0
                        for chunk in stream:
                            inserted = tm.bulk_insert_chunk(table_name, chunk)
                            actual_inserted = len(chunk) if inserted < 0 else inserted
                            table_inserted += actual_inserted
                            
                            asyncio.run_coroutine_threadsafe(
                                broadcast_progress({
                                    "type": "table_progress", 
                                    "step": "data", 
                                    "status": "running", 
                                    "table": table_name, 
                                    "rows_done": table_inserted, 
                                    "rows_total": row_count
                                }, job_id=job_id),
                                loop
                            )
                        
                    tm.enable_indexes_for_table(table_name)
                    tm.commit()
                    return table_inserted
                except Exception as e:
                    tm.rollback()
                    tm.enable_indexes_for_table(table_name)
                    raise e
                finally:
                    tm.close()
                    worker_tgt_raw.close()
                
            async def migrate_table_task(table_name):
                async with semaphore:
                    table_schema_obj = next((t for t in source_schema.get("tables", []) if t["name"] == table_name), None)
                    if not table_schema_obj: return 0
                    row_count = table_schema_obj.get("row_count", 0)
                    await broadcast_progress({"type": "table_progress", "step": "data", "status": "running", "table": table_name, "rows_done": 0, "rows_total": row_count}, job_id=job_id)
                
                    loop = asyncio.get_running_loop()
                    table_inserted = await asyncio.to_thread(run_table_worker, table_name, row_count, table_schema_obj, loop)
                
                    await broadcast_progress({"type": "table_progress", "step": "data", "status": "running", "table": table_name, "rows_done": table_inserted, "rows_total": row_count}, job_id=job_id)
                    return table_inserted
                
            for generation in getattr(resolution, "migration_generations", []):
                gen_tasks = []
                for table_name in generation:
                    if table_name not in migrated_tables:
                        gen_tasks.append(migrate_table_task(table_name))
                        migrated_tables.add(table_name)
            
                if gen_tasks:
                    results = await asyncio.gather(*gen_tasks, return_exceptions=False)
                    total_inserted += sum(results)
                
            # Also catch any tables missing from the generation graph just in case
            fallback_tasks = []
            for table in source_schema.get("tables", []):
                if table["name"] not in migrated_tables:
                    fallback_tasks.append(migrate_table_task(table["name"]))
                    migrated_tables.add(table["name"])
            if fallback_tasks:
                results = await asyncio.gather(*fallback_tasks, return_exceptions=False)
                total_inserted += sum(results)

            duration = time.time() - start_time
            rows_per_sec = total_inserted / duration if duration > 0 else 0
            await broadcast_progress({"type": "stage_details", "rows_per_sec": rows_per_sec}, job_id=job_id)
        # Step 6: Validation
        async with run_stage(job_id, "validation", "Data Verification"):
            val_agent = ValidationAgent()
            
            llm_skipped = analysis_report.get("status") == "skipped"
            
            try:
                source_raw = get_raw_conn(req.source)
                target_raw = get_raw_conn(req.target)
                validation_report = val_agent.validate_migration(source_raw, target_raw, source_schema.get("tables", []), direction, llm_skipped=llm_skipped)
                source_raw.close()
                target_raw.close()
            except Exception as e:
                validation_report = {"error": f"Validation failed to execute: {str(e)}", "validation_score": None if llm_skipped else 0}

            score = validation_report.get("validation_score")
            await broadcast_progress({"type": "stage_details", "score": score, "report": validation_report}, job_id=job_id)
        
        # Step 5b: Views, Procedures, Triggers Migration (NEW)
        object_translations = []
        if req.options.migrate_views or req.options.migrate_procedures or req.options.migrate_triggers:
            async with run_stage(job_id, "objects", "Migrate Objects"):
                try:
                    discovered_objects = discovery_service.list_migratable_objects(
                        req.source.host, req.source.port, req.source.username, req.source.password, req.source.db_type, req.source.database
                    )
                except Exception as e:
                    discovered_objects = {"views": [], "procedures": [], "triggers": []}
                    print("Failed to discover non-table objects:", e)
                
                to_translate = []
            
                if req.options.migrate_views:
                    views_to_mig = discovered_objects.get("views", [])
                    if req.options.selected_views:
                        views_to_mig = [v for v in views_to_mig if v["name"] in req.options.selected_views]
                    to_translate.extend(views_to_mig)
                
                if req.options.migrate_procedures:
                    procs_to_mig = discovered_objects.get("procedures", [])
                    if req.options.selected_procedures:
                        procs_to_mig = [p for p in procs_to_mig if p["name"] in req.options.selected_procedures]
                    to_translate.extend(procs_to_mig)
                
                if req.options.migrate_triggers:
                    trigs_to_mig = discovered_objects.get("triggers", [])
                    if req.options.selected_triggers:
                        trigs_to_mig = [t for t in trigs_to_mig if t["name"] in req.options.selected_triggers]
                    to_translate.extend(trigs_to_mig)
                
                from backend.agents.object_translation_agent import ObjectTranslationAgent
                from backend.models import MigratableObject
            
                translation_agent = ObjectTranslationAgent()
            
                for obj_dict in to_translate:
                    try:
                        obj = MigratableObject(**obj_dict)
                    except Exception as e:
                        obj_name = obj_dict.get("name", "unknown")
                        print(f"Warning: Skipping invalid migratable object {obj_name}: {e}")
                        await broadcast_progress({"type": "log", "level": "WARN", "message": f"Skipping invalid object '{obj_name}': {e}", "stage": "migrate_data"}, job_id=job_id)
                        continue

                    direction = f"{req.source.db_type.lower()}_to_{req.target.db_type.lower()}"
                
                    await broadcast_progress({"type": "log", "level": "INFO", "message": f"Translating {obj.object_type}: {obj.name}", "table": obj.name, "stage": "migrate_data"}, job_id=job_id)
                    await broadcast_progress({"type": "table_progress", "step": "data", "status": "running", "table": obj.name, "object_type": obj.object_type, "rows_done": 0, "rows_total": 1, "message": f"Translating {obj.object_type} '{obj.name}'..."}, job_id=job_id)
                
                    if obj.object_type == "view":
                        res = await translation_agent.translate_view(obj, req.source.db_type, req.target.db_type, source_database=req.source.database)
                    else:
                        res = await translation_agent.translate_procedure_or_trigger(obj, req.source.db_type, req.target.db_type, source_database=req.source.database)
                    
                    # Validate target dialect
                    is_valid, validation_msg = translation_agent.validate_target_dialect(res.translated_definition, req.source.db_type, req.target.db_type)
                    if not is_valid:
                        res.translation_error = validation_msg
                        res.needs_human_review = True
                        res.compile_status = "Invalid target syntax"
                        await broadcast_progress({"type": "log", "level": "WARN", "message": f"Validation failed for {obj.name}: {validation_msg}", "table": obj.name, "stage": "migrate_data"}, job_id=job_id)
                        await broadcast_progress({"type": "table_progress", "step": "data", "status": "error", "table": obj.name, "object_type": obj.object_type, "rows_done": 0, "rows_total": 1, "message": validation_msg}, job_id=job_id)
                        continue

                    # Auto-apply objects if translated definition exists
                    if obj.object_type in ["view", "procedure", "trigger", "function", "trigger_function"] and res.translated_definition:
                        try:
                            target_raw = get_raw_conn(req.target)
                            cursor = target_raw.cursor()
                            await auto_apply_object(obj, res.translated_definition, cursor, req.target)
                            if hasattr(target_raw, "commit"):
                                target_raw.commit()
                            target_raw.close()
                            res.approved_by_user = True
                            res.needs_human_review = False
                            res.compile_status = "Compiled successfully"
                            await broadcast_progress({"type": "table_progress", "step": "data", "status": "done", "table": obj.name, "object_type": obj.object_type, "rows_done": 1, "rows_total": 1}, job_id=job_id)
                        except Exception as e:
                            first_error = str(e)
                            await broadcast_progress({"type": "log", "level": "WARN", "message": f"Auto-apply failed for {obj.name}: {first_error}. Attempting LLM fix...", "table": obj.name, "stage": "migrate_data"}, job_id=job_id)
                            
                            # Auto-retry: ask LLM to fix the compile error and re-attempt
                            retry_success = False
                            try:
                                obj_dict_for_retry = {
                                    "object_name": obj.name,
                                    "object_type": obj.object_type,
                                    "source_definition": obj.source_definition,
                                    "translated_definition": res.translated_definition,
                                }
                                fixed_res = await translation_agent.retry_translation_after_compile_error(
                                    obj_dict_for_retry, req.target.db_type, first_error, source_database=req.source.database
                                )
                                if fixed_res.translated_definition and fixed_res.translated_definition != res.translated_definition:
                                    # Validate retry dialect
                                    is_valid_retry, validation_msg_retry = translation_agent.validate_target_dialect(fixed_res.translated_definition, req.source.db_type, req.target.db_type)
                                    if not is_valid_retry:
                                        res.translation_error = f"Auto-apply failed: {first_error}. AI fix validation failed: {validation_msg_retry}"
                                    else:
                                        # Re-attempt execution with the LLM's corrected SQL
                                        try:
                                            target_raw2 = get_raw_conn(req.target)
                                            cursor2 = target_raw2.cursor()
                                            await auto_apply_object(obj, fixed_res.translated_definition, cursor2, req.target)
                                            if hasattr(target_raw2, "commit"):
                                                target_raw2.commit()
                                            target_raw2.close()
                                            # LLM fix succeeded!
                                            res.translated_definition = fixed_res.translated_definition
                                            res.translation_method = "llm_full"
                                            res.approved_by_user = True
                                            res.needs_human_review = False
                                            res.compile_status = "Compiled successfully (after AI fix)"
                                            res.translation_error = None
                                            retry_success = True
                                            await broadcast_progress({"type": "log", "level": "INFO", "message": f"LLM fix succeeded for {obj.name}", "table": obj.name, "stage": "migrate_data"}, job_id=job_id)
                                            await broadcast_progress({"type": "table_progress", "step": "data", "status": "done", "table": obj.name, "object_type": obj.object_type, "rows_done": 1, "rows_total": 1}, job_id=job_id)
                                        except Exception as retry_exec_err:
                                            # LLM fix also failed to compile
                                            res.translated_definition = fixed_res.translated_definition
                                            res.translation_error = f"Auto-apply failed: {first_error}. AI fix also failed: {str(retry_exec_err)}"
                                    
                            except Exception:
                                pass  # LLM retry itself failed (e.g. no API key)

                            if not retry_success:
                                res.translation_error = res.translation_error or f"Auto-apply failed: {first_error}"
                                res.needs_human_review = True
                                res.compile_status = "Compile error"
                                await broadcast_progress({"type": "table_progress", "step": "data", "status": "failed", "table": obj.name, "object_type": obj.object_type, "rows_done": 0, "rows_total": 1}, job_id=job_id)
                        
                    object_translations.append(res.dict())

        duration_str = f"{duration:.2f}s"
        timestamp = datetime.datetime.now().isoformat()
        
        target_tables = validation_report.get("tables", [])
        total_target_rows = sum(t.get("target_row_count", 0) for t in target_tables) if target_tables else total_inserted

        # Check if there are any unapproved translations requiring review
        pending_review_count = sum(1 for res in object_translations if res["needs_human_review"] and not res["approved_by_user"])
        if pending_review_count > 0:
            final_status = f"COMPLETED — {pending_review_count} objects awaiting review"
        else:
            final_status = "SUCCESS"

        source_sql_list = []
        for tbl in source_schema.get("tables", []):
            cols = [f"  {c.get('name')} {c.get('type')}" for c in tbl.get("columns", [])]
            if tbl.get("primary_keys"):
                cols.append(f"  PRIMARY KEY ({', '.join(tbl.get('primary_keys'))})")
            source_sql_list.append(f"CREATE TABLE {tbl.get('name')} (\n" + ",\n".join(cols) + "\n);")
        source_sql_str = "\n\n".join(source_sql_list)
        target_sql_str = "\n\n".join(ddl_result.get("ddl_statements", []))

        full_payload = {
            "id": job_id,
            "status": final_status.lower() if "awaiting review" not in final_status else final_status,
            "duration_seconds": duration,
            "tables_migrated": len(source_schema.get("tables", [])),
            "total_rows": total_target_rows,
            "validation_score": score,
            "ddl_translation_log": ddl_result.get("translation_log", []),
            "ddl_statements": ddl_result.get("ddl_statements", []),
            "source_sql": source_sql_str,
            "target_sql": target_sql_str,
            "llm_warnings": analysis_report,
            "validation_report": validation_report,
            "object_translations": object_translations,
            "_source_config": req.source.dict(),
            "_target_config": req.target.dict(),
            "timestamp": timestamp
        }

        # Save to SQLite
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE migration_jobs 
                SET status = ?, tables_migrated = ?, rows_migrated = ?, duration = ?, timestamp = ?, full_payload = ?
                WHERE id = ?
            """, (
                final_status,
                len(source_schema.get("tables", [])),
                total_target_rows,
                duration_str,
                timestamp,
                json.dumps(full_payload),
                job_id
            ))
            conn.commit()
            conn.close()
        except Exception as db_err:
            print("Failed to save migration job to SQLite:", db_err)

        # Invalidate history cache on job completion
        cache.invalidate_tag("history")
        await broadcast_progress({"step": "completion", "status": "completed", "message": "Migration completed successfully"}, job_id=job_id)

        return full_payload

    except Exception as e:
        import traceback
        traceback.print_exc()
        await broadcast_progress({"step": "error", "status": "failed", "message": str(e)}, job_id=job_id)
        
        duration = time.time() - start_time
        duration_str = f"{duration:.2f}s"
        timestamp = datetime.datetime.now().isoformat()
        
        src_type = getattr(req.source, "db_type", "") if hasattr(req, "source") and req.source else ""
        tgt_type = getattr(req.target, "db_type", "") if hasattr(req, "target") and req.target else ""
        direction_str = f"{src_type.lower()}_to_{tgt_type.lower()}" if src_type and tgt_type else ""

        failed_payload = {
            "id": job_id,
            "status": "failed",
            "error": str(e),
            "timestamp": timestamp,
            "duration_seconds": duration,
            "tables_migrated": 0,
            "total_rows": 0,
            "validation_score": 0,
            "source_type": src_type,
            "target_type": tgt_type,
            "direction": direction_str,
            "validation_report": {
                "validation_score": 0,
                "tables": [],
                "summary": {
                    "total_tables": 0,
                    "passed": 0,
                    "failed": 0,
                    "overall_score": 0
                }
            },
            "ddl_translation_log": [],
            "ddl_statements": [],
            "source_sql": "",
            "target_sql": "",
            "object_translations": [],
        }

        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE migration_jobs 
                SET status = ?, duration = ?, timestamp = ?, full_payload = ?
                WHERE id = ?
            """, (
                "FAILED",
                duration_str,
                timestamp,
                json.dumps(failed_payload),
                job_id
            ))
            conn.commit()
            conn.close()
        except Exception as db_err:
            print("Failed to save failed migration job to SQLite:", db_err)

        return failed_payload

@app.post("/migrate")
@app.post("/api/migrate")
async def migrate(req: MigrationRequest, current_user: dict = Depends(get_current_user)):
    global is_migrating, migration_start_time
    import time
    
    if is_migrating:
        if time.time() - migration_start_time > 1800:
            print("Warning: Cleared stale migration lock")
            is_migrating = False
        else:
            raise HTTPException(status_code=409, detail="A migration is already in progress. Please wait for it to complete.")
            
    is_migrating = True
    migration_start_time = time.time()
    job_id = req.id if req.id else f"mig_{int(time.time())}"
    org_id = current_user["org_id"]
    user_id = current_user.get("id")
    
    # Insert IN_PROGRESS initial record
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO migration_jobs (id, org_id, user_id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp, full_payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            org_id,
            user_id,
            req.source.db_type,
            req.target.db_type,
            "IN_PROGRESS",
            0,
            0,
            "",
            datetime.datetime.now().isoformat(),
            json.dumps({"id": job_id, "status": "in_progress", "org_id": org_id})
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Failed to log initial IN_PROGRESS state to SQLite:", e)

    # Invalidate history cache when a new job starts
    cache.invalidate_tag("history")

    try:
        result = await run_migration_pipeline(req, job_id)
        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail=result)
        return result
    finally:
        is_migrating = False
        migration_start_time = 0

@app.get("/api/migrations/history")
async def get_migration_history(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=200, description="Items per page"),
    current_user: dict = Depends(get_current_user),
):
    cache_key = cache.make_key(f"history_{current_user['org_id']}", page, page_size)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    def _query():
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Total count for pagination
        cursor.execute("SELECT COUNT(*) FROM migration_jobs WHERE org_id = ?", (current_user["org_id"],))
        total = cursor.fetchone()[0]
        # Paginated query
        offset = (page - 1) * page_size
        cursor.execute(
            "SELECT id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp "
            "FROM migration_jobs WHERE org_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (current_user["org_id"], page_size, offset),
        )
        rows = cursor.fetchall()
        conn.close()
        items = [
            {
                "id": r["id"], "source_db": r["source_db"], "target_db": r["target_db"],
                "status": r["status"], "tables_migrated": r["tables_migrated"],
                "rows_migrated": r["rows_migrated"], "duration": r["duration"],
                "timestamp": r["timestamp"],
            }
            for r in rows
        ]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    try:
        result = await asyncio.to_thread(_query)
        cache.set(cache_key, result, ttl_seconds=5, tags=["history"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/migrations/{job_id}")
async def get_migration_job(job_id: str, current_user: dict = Depends(get_current_user)):
    """Summary endpoint — returns top-level stats without heavy arrays."""
    def _query():
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT full_payload FROM migration_jobs WHERE id = ? AND org_id = ?", (job_id, current_user["org_id"]))
        row = cursor.fetchone()
        conn.close()
        return row

    try:
        row = await asyncio.to_thread(_query)
        if not row:
            raise HTTPException(status_code=404, detail="Migration job not found")
        payload = json.loads(row[0])
        # Strip heavy arrays for the summary response
        summary = {k: v for k, v in payload.items() if k not in ("object_translations", "_source_config", "_target_config")}
        # Replace validation_report with just the summary counts
        if "validation_report" in payload and isinstance(payload["validation_report"], dict):
            vr = payload["validation_report"]
            summary["validation_report"] = {
                "validation_score": vr.get("validation_score"),
                "summary": vr.get("summary"),
                "table_count": len(vr.get("tables", [])),
            }
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/migrations/{job_id}/details")
async def get_migration_job_details(job_id: str, current_user: dict = Depends(get_current_user)):
    """Full payload including object_translations and per-table validation."""
    def _query():
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT full_payload FROM migration_jobs WHERE id = ? AND org_id = ?", (job_id, current_user["org_id"]))
        row = cursor.fetchone()
        conn.close()
        return row

    try:
        row = await asyncio.to_thread(_query)
        if not row:
            raise HTTPException(status_code=404, detail="Migration job not found")
        return json.loads(row[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/migrations/{job_id}/logs")
async def get_migration_logs(
    job_id: str,
    cursor: int = Query(0, ge=0, description="Last log_id seen (cursor for pagination)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of log entries to return"),
    current_user: dict = Depends(get_current_user),
):
    """Cursor-based paginated log retrieval for a migration job."""
    def _query():
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Verify job belongs to user's org
        c.execute("SELECT 1 FROM migration_jobs WHERE id = ? AND org_id = ?", (job_id, current_user["org_id"]))
        if not c.fetchone():
            conn.close()
            return None
        c.execute(
            "SELECT log_id, timestamp, level, step, message, metadata "
            "FROM migration_logs WHERE job_id = ? AND log_id > ? ORDER BY log_id ASC LIMIT ?",
            (job_id, cursor, page_size),
        )
        rows = c.fetchall()
        # Get total count for this job
        c.execute("SELECT COUNT(*) FROM migration_logs WHERE job_id = ?", (job_id,))
        total = c.fetchone()[0]
        conn.close()
        items = [
            {
                "log_id": r["log_id"], "timestamp": r["timestamp"], "level": r["level"],
                "step": r["step"], "message": r["message"],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else None,
            }
            for r in rows
        ]
        next_cursor = items[-1]["log_id"] if items else cursor
        return {"items": items, "next_cursor": next_cursor, "total": total, "has_more": len(items) == page_size}

    try:
        res = await asyncio.to_thread(_query)
        if res is None:
            raise HTTPException(status_code=404, detail="Migration job not found")
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/migrations/{migration_id}")
async def websocket_endpoint(websocket: WebSocket, migration_id: str):
    await websocket.accept()
    active_websockets[migration_id] = websocket

    # Immediately replay past logs/stage events for this migration_id so late/reconnected clients catch up
    try:
        def _get_history():
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT metadata FROM migration_logs WHERE job_id = ? ORDER BY log_id ASC", (migration_id,))
            rows = c.fetchall()
            conn.close()
            return [json.loads(r[0]) for r in rows if r[0]]

        history_messages = await asyncio.to_thread(_get_history)
        for msg in history_messages:
            await websocket.send_json(msg)
    except Exception as e:
        print("Failed to replay history to websocket:", e)

    try:
        while True:
            await websocket.receive_text() # Keep alive
    except Exception:
        pass
    finally:
        if migration_id in active_websockets:
            del active_websockets[migration_id]

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
