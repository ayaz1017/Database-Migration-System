with open("backend/main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "migration_jobs" in line or "insert" in line.lower() and "job" in line.lower():
        print(f"{i+1}: {line.strip()}")
