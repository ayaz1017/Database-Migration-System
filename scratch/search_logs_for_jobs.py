import os

search_job_ids = ["mig_1782675153517", "mig_1782672346939"]
brain_dir = os.path.expanduser("~\\.gemini\\antigravity\\brain")

if os.path.exists(brain_dir):
    for root, dirs, files in os.walk(brain_dir):
        for file in files:
            if file.endswith((".log", ".jsonl")):
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    if size > 15 * 1024 * 1024: # skip very large files
                        continue
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for job_id in search_job_ids:
                            if job_id in content:
                                print(f"Found {job_id} in {filepath}")
                                # Print lines around it
                                lines = content.splitlines()
                                for i, line in enumerate(lines):
                                    if job_id in line:
                                        start = max(0, i - 15)
                                        end = min(len(lines), i + 35)
                                        print(f"--- context from {file} lines {start}-{end} ---")
                                        for idx in range(start, end):
                                            print(f"{idx}: {lines[idx]}")
                                        print("--------------------------------------")
                except Exception as e:
                    pass
