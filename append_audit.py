audit_code = """

def log_security_audit(event_type: str, ip_address: str, details: str):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO security_audit_log (timestamp, event_type, ip_address, details) VALUES (?, ?, ?, ?)", 
                      (datetime.datetime.now().isoformat(), event_type, ip_address, details))
        conn.commit()
        conn.close()
    except Exception:
        pass

@app.get("/api/admin/audit-log")
def get_audit_log(request: Request, limit: int = 50):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM security_audit_log ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        raise
"""

with open("backend/main.py", "a") as f:
    f.write(audit_code)
print("Audit logging added.")
