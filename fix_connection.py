import re
import os

files_to_fix = [
    "backend/connectors/mssql.py",
    "backend/execution/mssql_execution_engine.py",
    "backend/main.py",
    "backend/services/discovery_service.py"
]

pattern = re.compile(r'(DRIVER=\{\{ODBC Driver 17 for SQL Server\}\}[^"]*)(")')

for filepath in files_to_fix:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = pattern.sub(r'\1;TrustServerCertificate=yes;\2', content)
        
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Fixed {filepath}")
        else:
            print(f"No changes needed in {filepath}")
    else:
        print(f"File not found: {filepath}")
