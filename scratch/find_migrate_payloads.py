import os
import json

brain_dir = os.path.expanduser("~\\.gemini\\antigravity\\brain")

for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file.endswith(".log"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # We want to find any trace of a traceback during /migrate
                # Let's search for "Traceback" in the file
                if "Traceback" in content:
                    # Let's print occurrences of Traceback that are related to migrate
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if "Traceback (most recent call last):" in line:
                            # Print the traceback
                            traceback_lines = []
                            for idx in range(i, min(len(lines), i + 35)):
                                traceback_lines.append(lines[idx])
                                if not lines[idx].startswith(" ") and "Traceback" not in lines[idx] and idx > i:
                                    # reached the end of traceback (the error message)
                                    break
                            tb_text = "\n".join(traceback_lines)
                            # Check if the traceback mentions object_translation_agent or views or procedures or triggers
                            # or compile check
                            if any(w in tb_text for w in ["object_translation", "translate_view", "translate_procedure", "compile", "approve_object"]):
                                print(f"==================================================")
                                print(f"Found related traceback in {filepath} at line {i}:")
                                print(f"==================================================")
                                print(tb_text)
                                print("="*50)
            except Exception as e:
                pass
