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
                    if size > 15 * 1024 * 1024:
                        continue
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                    for job_id in search_job_ids:
                        if job_id in content:
                            print(f"==================================================")
                            print(f"Found {job_id} in file: {filepath}")
                            print(f"==================================================")
                            lines = content.splitlines()
                            
                            # Find all occurrences and print context around them, especially Traceback
                            found_indices = [i for i, line in enumerate(lines) if job_id in line]
                            for idx in found_indices:
                                print(f"--- Occurrence at line {idx} ---")
                                # Scan forward to find if there is a traceback
                                start = max(0, idx - 10)
                                # Let's scan forward 60 lines to see if a traceback or error is printed
                                end = min(len(lines), idx + 60)
                                # Print lines
                                for i in range(start, end):
                                    print(f"{i}: {lines[i]}")
                                print("-" * 50)
                except Exception as e:
                    pass
