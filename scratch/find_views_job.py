import os
import json

brain_dir = os.path.expanduser("~\\.gemini\\antigravity\\brain")

# Let's find transcript.jsonl files
for root, dirs, files in os.walk(brain_dir):
    for file in files:
        if file.endswith("transcript.jsonl"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    for line in f:
                        if "/migrate" in line and "options" in line:
                            # Let's inspect the migrate call
                            data = json.loads(line)
                            # Look at tool_calls or content
                            # We want to check if the user request or model call has migrate options
                            content = data.get("content", "")
                            if "migrate_views" in content or "migrate_procedures" in content or "migrate_triggers" in content:
                                print(f"Found options in transcript: {filepath}")
                                print(content[:500])
                                print("-" * 40)
            except Exception as e:
                pass
