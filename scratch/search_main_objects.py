with open("backend/main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "discover/objects" in line.lower() or "discover_objects" in line.lower() or "object_translations" in line.lower() or "translate_objects" in line.lower() or "objects" in line.lower():
        # print line and line number
        if "def " in line or "app." in line or "await " in line or "class " in line or "execute" in line:
            print(f"{i+1}: {line.strip()}")
