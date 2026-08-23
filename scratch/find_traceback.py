import os

search_job_ids = ["mig_1782675153517", "mig_1782672346939"]
brain_dir = os.path.expanduser("~\\.gemini\\antigravity\\brain")

for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file.endswith(".log"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for job_id in search_job_ids:
                    if job_id in content and "Traceback" in content:
                        print(f"File containing traceback for {job_id}: {filepath}")
                        # Find the traceback and print it
                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if "traceback" in line.lower() or job_id in line:
                                # Look for a traceback starting nearby
                                start = max(0, i - 5)
                                end = min(len(lines), i + 40)
                                print(f"--- Traceback Context ({file}:{i}) ---")
                                for idx in range(start, end):
                                    print(lines[idx])
                                print("=" * 60)
            except Exception as e:
                pass
