import os

search_job_ids = ["mig_1782675153517", "mig_1782672346939"]
brain_dir = os.path.expanduser("~\\.gemini\\antigravity\\brain")

for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file.endswith(".log"):
            filepath = os.path.join(root, file)
            try:
                # Skip if it is the current conversation ID log to focus on older logs
                if "8e90b923-56e5-4da7-bfc9-2cecd1ad80f9" in filepath:
                    continue
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for job_id in search_job_ids:
                    if job_id in content:
                        print(f"FOUND {job_id} in older log file: {filepath}")
                        # Check if this file has traceback
                        if "Traceback" in content:
                            print("  Contains traceback!")
                            # Let's print the traceback lines
                            lines = content.splitlines()
                            for i, line in enumerate(lines):
                                if "Traceback (most recent call last):" in line:
                                    # Check if the traceback is near the job_id
                                    start = max(0, i - 5)
                                    end = min(len(lines), i + 40)
                                    print(f"--- Traceback from {file}:{i} ---")
                                    for idx in range(start, end):
                                        print(lines[idx])
                                    print("=" * 60)
            except Exception as e:
                pass
