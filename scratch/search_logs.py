import os

# Search for any log files or txt files containing traceback or migration job IDs
search_dirs = [
    "c:\\Users\\Ayaz Khan\\Desktop\\Database Migration Agent",
    os.path.expanduser("~\\.gemini\\antigravity\\brain")
]

for base_dir in search_dirs:
    if not os.path.exists(base_dir):
        continue
    for root, dirs, files in os.walk(base_dir):
        # skip node_modules, venv, .git, .pytest_cache
        if any(p in root for p in ["node_modules", "venv", ".git", ".pytest_cache"]):
            continue
        for file in files:
            if file.endswith((".log", ".txt", ".jsonl")):
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    # skip huge files
                    if size > 5 * 1024 * 1024:
                        continue
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if "Traceback" in content or "mig_" in content:
                            print(f"Found file: {filepath} ({size} bytes)")
                except Exception as e:
                    pass
