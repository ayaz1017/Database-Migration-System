import os

# Search backend files for 'views', 'procedures', 'triggers'
for root, dirs, files in os.walk("backend"):
    if "venv" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Check for views/procedures/triggers
                if "discover_views" in content or "discover_procedures" in content or "discover_triggers" in content or \
                   "views" in content.lower() or "procedures" in content.lower() or "triggers" in content.lower():
                    print(f"File: {filepath}")
                    # Print lines with views/procedures/triggers
                    for line in content.splitlines():
                        if "def " in line and ("view" in line.lower() or "proc" in line.lower() or "trigger" in line.lower() or "object" in line.lower()):
                            print(f"  {line}")
