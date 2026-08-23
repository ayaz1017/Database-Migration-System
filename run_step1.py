from backend.services.discovery_service import DiscoveryService
import os
from dotenv import load_dotenv

load_dotenv()

# We'll use localhost or get from env if not localhost. The prompt says <ubuntu-machine-ip>,
# but since they didn't specify, we'll try the one from .env first or 127.0.0.1.
# Usually if they say <ubuntu-machine-ip>, it might be WSL. We can try localhost.
host = "127.0.0.1"

service = DiscoveryService()

try:
    print(f"Attempting to connect to MSSQL at {host}...")
    schema = service.connect_and_discover(
        host=host,
        port=1433,
        username="SA",
        password="Ayaz@123",
        db_type="mssql",
        database="migrated_sql"
    )
    
    print("SUCCESS")
    print("| Table name | Columns | Row count | Has PK | Has FK | Indexes |")
    print("|------------|---------|-----------|--------|--------|---------|")
    for table in schema.get("tables", []):
        name = table.get("name", "")
        cols = len(table.get("columns", []))
        rows = table.get("row_count", 0)
        has_pk = "Yes" if len(table.get("primary_keys", [])) > 0 else "No"
        has_fk = "Yes" if len(table.get("foreign_keys", [])) > 0 else "No"
        idx = len(table.get("indexes", []))
        print(f"| {name} | {cols} | {rows} | {has_pk} | {has_fk} | {idx} |")
        
except Exception as e:
    print("FAILURE")
    print(e)
