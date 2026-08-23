import os

brain_dir = os.path.expanduser("~\\.gemini\\antigravity\\brain")

found = False
for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file.endswith(".log"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if "object_translation_agent" in content or "translate_view" in content or "translate_procedure_or_trigger" in content:
                    if "Traceback" in content:
                        print(f"FOUND TRACEBACK in file: {filepath}")
                        found = True
                        # print context around the traceback
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if "Traceback (most recent call last):" in line:
                                print(f"--- Traceback at line {i} ---")
                                for idx in range(max(0, i - 2), min(len(lines), i + 40)):
                                    print(lines[idx])
                                print("=" * 60)
            except Exception as e:
                pass

if not found:
    print("NO TRACEBACKS FOUND matching object_translation_agent / translate_view / translate_procedure_or_trigger.")
