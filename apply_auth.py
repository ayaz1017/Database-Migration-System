import re
import os

with open("backend/main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add imports at the top
imports = """from fastapi import Depends
from backend.services.auth_service import get_current_user, require_admin, require_member_or_above
from backend.routers.auth import router as auth_router
import uuid
"""
content = re.sub(
    r'(from fastapi import FastAPI.*?)\n',
    r'\1\n' + imports,
    content,
    count=1
)

# 2. Add include_router
content = re.sub(
    r'(app = FastAPI\(title="Fluxline API"\))\n',
    r'\1\napp.include_router(auth_router)\n',
    content,
    count=1
)

# 3. Update init_db
init_db_patch = """
    # Auth tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS organizations (id TEXT PRIMARY KEY, name TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, org_id TEXT NOT NULL, email TEXT UNIQUE NOT NULL, hashed_password TEXT NOT NULL, role TEXT NOT NULL, FOREIGN KEY(org_id) REFERENCES organizations(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS refresh_tokens (token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    # Check if migration_jobs needs org_id
    cursor.execute("PRAGMA table_info(migration_jobs)")
    columns = [col[1] for col in cursor.fetchall()]
    if "org_id" not in columns:
        cursor.execute("ALTER TABLE migration_jobs ADD COLUMN org_id TEXT")
        cursor.execute("UPDATE migration_jobs SET org_id = 'default_org'")
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE migration_jobs ADD COLUMN user_id TEXT")
        cursor.execute("UPDATE migration_jobs SET user_id = 'default_admin'")
        
    cursor.execute("SELECT COUNT(*) FROM organizations")
    if cursor.fetchone()[0] == 0:
        from backend.services.auth_service import get_password_hash
        hashed_pw = get_password_hash("admin")
        cursor.execute("INSERT INTO organizations (id, name) VALUES (?, ?)", ("default_org", "Default Organization"))
        cursor.execute(
            "INSERT INTO users (id, org_id, email, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
            ("default_admin", "default_org", "admin@example.com", hashed_pw, "Admin")
        )
"""

content = re.sub(
    r'(cursor.execute\("CREATE INDEX IF NOT EXISTS idx_logs_job_id ON migration_logs\(job_id, log_id\)"\))\n',
    r'\1\n' + init_db_patch + '\n',
    content
)

# 4. Modify endpoint signatures to add `current_user: dict = Depends(...)`
# We'll parse line by line
lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    
    if line.startswith('@app.') and any(path in line for path in ['/discover', '/api/discover', '/api/migrations', '/api/analytics', '/api/test-db', '/migrate', '/api/admin', '/migrations']):
        # skip health, docs, etc. and ws for now
        if 'ws/migrations' in line or '/health' in line:
            i += 1
            continue
            
        # determine which dependency
        if '/api/admin' in line:
            dep = "current_user: dict = Depends(require_admin)"
        else:
            dep = "current_user: dict = Depends(require_member_or_above)"
            
        # find the next `async def` or `def`
        j = i + 1
        while j < len(lines) and not lines[j].strip().startswith('def ') and not lines[j].strip().startswith('async def '):
            new_lines.append(lines[j])
            j += 1
            
        if j < len(lines):
            func_line = lines[j]
            # we need to inject the parameter.
            # wait, if the signature is multiline, this is tricky.
            # let's just find the closing parenthesis of the signature.
            sig_start = j
            while j < len(lines) and '):' not in lines[j] and ') ->' not in lines[j]:
                j += 1
            
            # now lines[sig_start..j] contains the signature.
            # let's replace the last `)` with `, current_user: dict = Depends(...) )`
            # wait, if it's `def func():`, the replacement would be `def func(current_user: dict = Depends(...)):`
            if j < len(lines):
                # reconstruct signature
                sig_lines = lines[sig_start:j+1]
                sig_str = '\n'.join(sig_lines)
                if '(' in sig_str:
                    # check if empty args
                    if '( ' in sig_str or '()' in sig_str.replace('\n', ''):
                        sig_str = re.sub(r'\(\s*\)', f'({dep})', sig_str)
                    else:
                        # has args, insert before the last )
                        sig_str = re.sub(r'\)(?!.*\))', f', {dep})', sig_str, flags=re.DOTALL)
                
                # replace lines in new_lines
                for line_idx, new_line in enumerate(sig_str.split('\n')):
                    if line_idx == 0:
                        new_lines.append(new_line)
                    else:
                        new_lines.append(new_line)
            i = j
    i += 1

content = '\n'.join(new_lines)

# 5. Inject org_id filter into migration_jobs queries
# SELECT ... FROM migration_jobs
# UPDATE migration_jobs ...
# INSERT INTO migration_jobs ...

# We will just write a wrapper around cursor.execute if it's too complex, or manually do it.
# Manual replacements:
content = content.replace(
    'cursor.execute("SELECT full_payload FROM migration_jobs WHERE id = ?", (job_id,))',
    'cursor.execute("SELECT full_payload FROM migration_jobs WHERE id = ? AND org_id = ?", (job_id, current_user["org_id"]))'
)

content = content.replace(
    '''cursor.execute(
            "SELECT id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp "
            "FROM migration_jobs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (page_size, offset),
        )''',
    '''cursor.execute(
            "SELECT id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp "
            "FROM migration_jobs WHERE org_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (current_user["org_id"], page_size, offset),
        )'''
)
content = content.replace(
    'cursor.execute("SELECT COUNT(*) FROM migration_jobs")',
    'cursor.execute("SELECT COUNT(*) FROM migration_jobs WHERE org_id = ?", (current_user["org_id"],))'
)
# For the inserts and updates:
content = content.replace(
    'INSERT INTO migration_jobs (id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp, full_payload)',
    'INSERT INTO migration_jobs (id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp, full_payload, org_id, user_id)'
)
# The insert values part is `VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (job_id, ...)`
content = content.replace(
    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",\n                (job_id, request.source_db, request.target_db, "IN_PROGRESS", 0, 0, "", timestamp, payload_json),\n',
    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",\n                (job_id, request.source_db, request.target_db, "IN_PROGRESS", 0, 0, "", timestamp, payload_json, current_user["org_id"], current_user["id"]),\n'
)

# And updates:
content = content.replace(
    'UPDATE migration_jobs \n                SET status = ?, tables_migrated = ?, rows_migrated = ?, duration = ? \n                WHERE id = ?',
    'UPDATE migration_jobs \n                SET status = ?, tables_migrated = ?, rows_migrated = ?, duration = ? \n                WHERE id = ? AND org_id = ?'
)
content = content.replace(
    '(status, tables_migrated, rows_migrated, duration_str, job_id)',
    '(status, tables_migrated, rows_migrated, duration_str, job_id, current_user["org_id"])'
)
# Update just status
content = content.replace(
    'UPDATE migration_jobs \n                SET status = ? \n                WHERE id = ?',
    'UPDATE migration_jobs \n                SET status = ? \n                WHERE id = ? AND org_id = ?'
)
content = content.replace(
    '("COMPLETED_WITH_ERRORS", job_id)',
    '("COMPLETED_WITH_ERRORS", job_id, current_user["org_id"])'
)
content = content.replace(
    '(status, job_id)',
    '(status, job_id, current_user["org_id"])'
)

with open("backend/main.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Applied auth to main.py")
