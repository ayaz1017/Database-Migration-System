import sys

with open("backend/main.py", "r") as f:
    code = f.read()

# 1. CORS & SecurityHeaders & SlowAPI setup
setup_code = """app = FastAPI(title="Fluxline API")

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
import logging
import uuid
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    logger.error(f"Unhandled Exception (ID: {error_id}) at {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error_id": error_id}
    )"""

code = code.split('app = FastAPI(title="Universal Migration Engine")')[0] + setup_code + code.split('allow_headers=["*"],\n)')[1]


# 2. Pydantic validation
pydantic_code = """from pydantic import BaseModel, Field
import re

class ConnectionConfig(BaseModel):
    db_type: str = Field(pattern="^(mssql|mysql|postgres|oracle)$")
    host: str = Field(pattern="^[a-zA-Z0-9.-]+$")
    port: int = Field(ge=1, le=65535)
    username: str = Field(pattern="^[a-zA-Z0-9_.-]+$")
    password: str = Field(max_length=500)
    database: str = Field(pattern="^[a-zA-Z0-9_.-]+$")"""

import re
code = re.sub(r'class ConnectionConfig\(BaseModel\):.*?database: str', pydantic_code, code, flags=re.DOTALL)


resolve_req = """from pydantic import field_validator

class ResolveDependenciesRequest(BaseModel):
    config: ConnectionConfig
    selected_tables: list[str]
    fk_dependency_mode: Literal["auto_include", "strict", "drop_constraint"] = "auto_include"
    
    @field_validator('selected_tables', mode='before')
    @classmethod
    def validate_identifiers(cls, v: list[str]) -> list[str]:
        for item in v:
            if not re.match(r"^[a-zA-Z0-9_.-]+$", item):
                raise ValueError(f"Invalid SQL identifier: {item}")
        return v"""

code = re.sub(r'class ResolveDependenciesRequest\(BaseModel\):.*?fk_dependency_mode: Literal\["auto_include", "strict", "drop_constraint"\] = "auto_include"', resolve_req, code, flags=re.DOTALL)


# 3. Scrub WebSocket
code = code.replace(
    'await ws.send_text(json.dumps(message))', 
    'from backend.utils import scrub_credentials\n            safe_msg = scrub_credentials(message)\n            await ws.send_text(json.dumps(safe_msg))'
)
code = code.replace(
    'await ws.send_json(message)',
    'from backend.utils import scrub_credentials\n            safe_msg = scrub_credentials(message)\n            await ws.send_json(safe_msg)'
)

# 4. Scrub sqlite save
code = code.replace(
    'json.dumps(full_payload),\n                        job_id,',
    'json.dumps(scrub_credentials(full_payload)),\n                        job_id,'
)
# Ensure scrub_credentials is imported near get_db
code = code.replace('def get_db(row_factory=False):', 'from backend.utils import scrub_credentials\ndef get_db(row_factory=False):')


# 5. Rate Limits
code = code.replace('@app.get("/api/test-db")\ndef test_db_connection(', '@app.get("/api/test-db")\n@limiter.limit("20/minute")\ndef test_db_connection(\n    request: Request,')
code = code.replace('@app.post("/migrate")\nasync def migrate(req: MigrationRequest):', '@app.post("/migrate")\n@limiter.limit("5/minute")\nasync def migrate(request: Request, req: MigrationRequest):')


# 6. Remove detail=str(e)
code = code.replace('raise HTTPException(status_code=500, detail=str(e))', 'raise')
code = code.replace('raise HTTPException(status_code=400, detail=str(e))', 'raise')


with open("backend/main.py", "w") as f:
    f.write(code)
print("Patched main.py successfully.")
