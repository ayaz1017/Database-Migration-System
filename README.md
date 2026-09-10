# Universal Migration Engine

The Universal Migration Engine is an intelligent, high-performance database migration system designed to seamlessly transfer data, schemas, and complex objects (Views, Procedures, Triggers) between disparate relational databases. It leverages large language models (LLMs) to automatically detect schema compatibility, translate complex database-specific syntax (e.g., Oracle PL/SQL to MySQL), and validate migrated structures against the source to guarantee data fidelity without compromising speed. 

It uses a dual-engine approach to maximize throughput. Schema discovery and conversion logic act as an orchestration layer, while heavy-lifting data migration uses high-performance chunked streaming mechanisms to ensure memory efficiency even with massive datasets.

## Architecture

```text
React Frontend (Vite, TailwindCSS)
       |
       v
FastAPI Backend (Python 3.12+)
       |
       +--> Discovery Service (Schema Inspection & System Object Filtering)
       |
       +--> Execution Engines
              |
              +--> Oracle Engine (cx_Oracle / oracledb)
              |
              +--> MSSQL Engine (pyodbc)
              |
              +--> MySQL Engine (keyset chunking)
              |
              +--> PostgreSQL Engine
```

## Key Features
- **Heterogeneous Database Support:** Migrate between Oracle, MySQL, PostgreSQL, and SQL Server seamlessly.
- **AI-Powered Schema Translation:** Uses LLMs (OpenAI) to automatically rewrite Views, Stored Procedures, and Triggers into the target database dialect.
- **Smart Discovery & Filtering:** Automatically filters out noise like Oracle system schemas (SYS, SYSTEM, BIN$) so you only migrate user data.
- **Parallel Data Streaming:** Uses chunking and transaction management to handle millions of rows without memory exhaustion.
- **Cyclic Dependency Resolution:** Intelligently maps and disables foreign key constraints to properly insert data into self-referencing or cyclic tables.

## Prerequisites
- Python 3.10+
- Node.js 18+
- Required Database Drivers (e.g., ODBC Driver 17 for SQL Server, Oracle Instant Client if needed)

## Quick Start (Docker)

Requirements:
- Docker Desktop (8GB+ RAM allocated)
- 15GB free disk space (for Ollama model)

```bash
git clone https://github.com/ayaz1017/Database-Migration-System.git
cd Database-Migration-System

# Copy and configure environment
cp .env.example .env
# Edit .env: set JWT_SECRET_KEY and 
# DEFAULT_ADMIN_PASSWORD

# Start everything
./start.sh        # Mac/Linux
start.bat         # Windows

# Open in browser
open http://localhost:3000
```

First run takes 5-10 minutes to 
download the Ollama model (~5GB).
Subsequent starts take ~30 seconds.

## Default Login
Email: admin@fluxline.local
Password: (set in .env)

## Stop
docker-compose down

## View logs
docker-compose logs -f backend
docker-compose logs -f ollama

## Migration Modes
- **Full Load (Streaming)**: High-performance streaming chunked extraction for data syncing.
- **Structure Only**: Translate and migrate only the DDL (Tables, Views, Procedures, Triggers).
- **Auto-Fixing**: The backend agent automatically captures syntax compilation errors from the target database and re-prompts the LLM to patch the SQL automatically.

## Running Tests
To run the automated test suites, execute the following from the project root:

```bash
# Make sure your virtual environment is active!
pytest backend/tests/ -v
```
