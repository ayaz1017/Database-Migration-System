# Universal Migration Engine

The Universal Migration Engine is an intelligent, high-performance database migration system designed to seamlessly transfer data, schema, and objects between disparate relational databases. It leverages large language models (LLMs) to automatically detect schema compatibility, recommend ideal mappings, and validate migrated structures against the source to guarantee data fidelity without compromising speed. 

It uses a dual-engine approach to maximize throughput. Schema discovery and conversion logic act as an orchestration layer, while heavy lifting data migration is deferred to specialized, native high-performance tools whenever available (such as `pgloader` for PostgreSQL via WSL). For arbitrary connections or fallback cases, it utilizes asynchronous, chunked streaming mechanisms to ensure memory efficiency even with massive datasets.

## Architecture

```text
React Frontend (Vite, TailwindCSS)
       |
       v
FastAPI Backend (Python 3.12+)
       |
       +--> Discovery Service (Schema Inspection)
       |
       +--> Execution Engines
              |
              +--> MSSQL Engine (pyodbc)
              |
              +--> MySQL Engine (keyset chunking)
              |
              +--> PostgreSQL Engine (pgloader native / WSL)
```

## Prerequisites
- Python 3.12+
- Node.js 18+
- ODBC Driver 17 for SQL Server
- WSL with pgloader installed
- MySQL 8.x running on Windows
- MSSQL Server 2022 running on Ubuntu

## 🚀 Setup Instructions

Follow these commands to get the project running locally:

### 1. Clone the repository
```bash
git clone https://github.com/ayaz1017/Database-Migration-System.git
cd Database-Migration-System
```

### 2. Backend Setup (FastAPI)
Open a terminal and set up the Python backend from the root of the project:
```bash
# Install required Python packages
pip install -r backend/requirements.txt

# Create your environment variables file
cp backend/.env.example backend/.env

# (Edit backend/.env and add your database credentials and API keys)

# Run the backend server
uvicorn backend.main:app --reload
```

### 3. Frontend Setup (React)
Open a new, separate terminal and set up the frontend:
```bash
cd frontend
npm install
npm run dev
```

The application should now be accessible in your browser (usually at `http://localhost:5173` or `http://localhost:3000`).

## Environment Variables
Ensure the following keys are populated in your `backend/.env` file:

```env
MSSQL_HOST=
MSSQL_PORT=
MSSQL_USER=
MSSQL_PASS=
MSSQL_DB=

MYSQL_HOST=
MYSQL_PORT=
MYSQL_USER=
MYSQL_PASS=
MYSQL_DB=

PG_HOST=
PG_PORT=
PG_USER=
PG_PASS=
PG_DB=

GOOGLE_API_KEY=
```

## Migration Modes
- **Full Load**: High performance bulk transfer (`pgLoader` for PostgreSQL, streaming chunked extraction for MySQL and MSSQL).
- **Incremental / CDC**: Continuous data capture via Airbyte (requires Docker).
- **Full Load + ongoing sync**: Hybrid strategy initializing via Full Load then tailing logs for real-time replication.

## Performance Benchmarks
| Migration           | Rows    | Rows/sec | Mode         |
|---------------------|---------|----------|--------------|
| MSSQL → MySQL       | 200,001 | 10,800   | streaming    |
| MSSQL → PostgreSQL  | 200,001 | 24,540   | wsl_pgloader |
| MySQL → PostgreSQL  | 200,001 | 27,397   | wsl_pgloader |

## Running Tests
To run the automated test suites, execute the following from the project root. (Note: Discovery tests require Docker Desktop running to automatically provision test containers).

```bash
pytest tests/test_migration_matrix.py -v
pytest tests/test_discovery_service.py -v
```
