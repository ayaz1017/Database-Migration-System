import sys
import json
sys.path.append('.')
from backend.services.discovery_service import DiscoveryService

ds = DiscoveryService()
try:
    res = ds.connect_and_discover('localhost', 1521, 'pdbadmin', 'Oracle123', 'oracle', 'ORACLEDB')
    print('TABLES DISCOVERED:', len(res.get('tables', [])))
    for t in res.get('tables', []):
        print(f"Table: {t['name']}, Rows: {t.get('row_count')}")
except Exception as e:
    print('Error:', e)
