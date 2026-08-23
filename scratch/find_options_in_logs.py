import os

brain_dir = os.path.expanduser("~\\.gemini\\antigravity\\brain")

for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file.endswith((".log", ".jsonl")):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Check if it contains keywords related to migrating views/procedures/triggers
                # and contains some job ID
                if any(k in content for k in ["migrate_views", "migrate_procedures", "migrate_triggers"]):
                    print(f"File matches: {filepath}")
                    # Let's search for lines containing these keywords
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if any(k in line for k in ["migrate_views", "migrate_procedures", "migrate_triggers", "selected_views"]):
                            print(f"  {i}: {line[:300]}")
            except Exception as e:
                pass
