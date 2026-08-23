filename = "c:/Users/Ayaz Khan/Desktop/Database Migration Agent/backend/config/migration_matrix.py"
with open(filename) as f:
    content = f.read()

# Fix existing mapped booleans
content = content.replace(
    "'BOOLEAN': {'lossy': False, 'note': '', 'type': 'NUMBER(1)'}",
    "'BOOLEAN': {'lossy': True, 'note': '', 'type': 'NUMBER(1)'}",
)

# Add BOOLEAN to mssql_to_oracle where it's missing (after BIT)
content = content.replace(
    "'BIT': {'lossy': False, 'note': '', 'type': 'NUMBER(1)'}",
    "'BIT': {'lossy': False, 'note': '', 'type': 'NUMBER(1)'},\n        'BOOLEAN': {'lossy': True, 'note': '', 'type': 'NUMBER(1)'}",
)

# Fix NUMBER lossy
content = content.replace(
    "'NUMBER': {'lossy': False, 'note': '', 'type': 'DECIMAL'}",
    "'NUMBER': {'lossy': True, 'note': '', 'type': 'DECIMAL'}",
)
content = content.replace(
    "'NUMBER': {'lossy': False, 'note': '', 'type': 'NUMERIC'}",
    "'NUMBER': {'lossy': True, 'note': '', 'type': 'NUMERIC'}",
)

# Fix DATE lossy
content = content.replace(
    "'DATE': {'lossy': False, 'note': '', 'type': 'DATETIME'}",
    "'DATE': {'lossy': True, 'note': '', 'type': 'DATETIME'}",
)
content = content.replace(
    "'DATE': {'lossy': False, 'note': '', 'type': 'TIMESTAMP'}",
    "'DATE': {'lossy': True, 'note': '', 'type': 'TIMESTAMP'}",
)
content = content.replace(
    "'DATE': {'lossy': False, 'note': '', 'type': 'DATETIME2'}",
    "'DATE': {'lossy': True, 'note': '', 'type': 'DATETIME2'}",
)

with open(filename, "w") as f:
    f.write(content)
print("Fixed matrix lossy values")
