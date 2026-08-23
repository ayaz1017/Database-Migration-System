import re

with open(r'backend\config\migration_matrix.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'\"DATE\": \{\"type\": \"DATETIME\", \"lossy\": False', '\"DATE\": {\"type\": \"DATETIME\", \"lossy\": True', text)
text = re.sub(r'\"DATE\": \{\"type\": \"TIMESTAMP\", \"lossy\": False, \"note\": \"Oracle DATE includes time.', '\"DATE\": {\"type\": \"TIMESTAMP\", \"lossy\": True, \"note\": \"Oracle DATE includes time.', text)
text = re.sub(r'\"DATE\": \{\"type\": \"DATETIME2\", \"lossy\": False', '\"DATE\": {\"type\": \"DATETIME2\", \"lossy\": True', text)

with open(r'backend\config\migration_matrix.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed lossy flags")
