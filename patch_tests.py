import re

# Fix DATE lossy flag in migration_matrix.py
with open(r"backend\config\migration_matrix.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    '"DATE": {"type": "DATETIME", "lossy": False, "note": "Oracle DATE includes time. Mapped to DATETIME."}',
    '"DATE": {"type": "DATETIME", "lossy": True, "note": "Oracle DATE includes time. Mapped to DATETIME."}'
)

content = content.replace(
    '"DATE": {"type": "TIMESTAMP", "lossy": False, "note": "Oracle DATE includes time. Mapped to TIMESTAMP."}',
    '"DATE": {"type": "TIMESTAMP", "lossy": True, "note": "Oracle DATE includes time. Mapped to TIMESTAMP."}'
)

content = content.replace(
    '"DATE": {"type": "DATETIME2", "lossy": False, "note": "Oracle DATE includes time. Mapped to DATETIME2."}',
    '"DATE": {"type": "DATETIME2", "lossy": True, "note": "Oracle DATE includes time. Mapped to DATETIME2."}'
)

with open(r"backend\config\migration_matrix.py", "w", encoding="utf-8") as f:
    f.write(content)


# Append tests to test_migration_matrix.py
with open(r"tests\test_migration_matrix.py", "a", encoding="utf-8") as f:
    f.write("""

def test_oracle_to_mysql_all_types_mapped():
    datatypes = MIGRATION_MATRIX["oracle_to_mysql"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_oracle_to_postgres_all_types_mapped():
    datatypes = MIGRATION_MATRIX["oracle_to_postgres"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_oracle_to_mssql_all_types_mapped():
    datatypes = MIGRATION_MATRIX["oracle_to_mssql"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_mssql_to_oracle_all_types_mapped():
    datatypes = MIGRATION_MATRIX["mssql_to_oracle"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_mysql_to_oracle_all_types_mapped():
    datatypes = MIGRATION_MATRIX["mysql_to_oracle"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_postgres_to_oracle_all_types_mapped():
    datatypes = MIGRATION_MATRIX["postgres_to_oracle"]["datatypes"]
    for k, v in datatypes.items():
        assert v is not None
        assert "type" in v
        assert isinstance(v["type"], str)

def test_oracle_lossy_flags_present():
    # BOOLEAN -> NUMBER(1) lossy
    assert MIGRATION_MATRIX["mssql_to_oracle"]["datatypes"]["BOOLEAN"]["lossy"] is True
    assert MIGRATION_MATRIX["mysql_to_oracle"]["datatypes"]["BOOLEAN"]["lossy"] is True
    assert MIGRATION_MATRIX["postgres_to_oracle"]["datatypes"]["BOOLEAN"]["lossy"] is True
    
    # NUMBER no-precision -> DECIMAL(38,10) lossy
    assert MIGRATION_MATRIX["oracle_to_mysql"]["datatypes"]["NUMBER"]["lossy"] is True
    assert MIGRATION_MATRIX["oracle_to_postgres"]["datatypes"]["NUMBER"]["lossy"] is True
    assert MIGRATION_MATRIX["oracle_to_mssql"]["datatypes"]["NUMBER"]["lossy"] is True
    
    # DATE -> DATETIME/TIMESTAMP lossy
    assert MIGRATION_MATRIX["oracle_to_mysql"]["datatypes"]["DATE"]["lossy"] is True
    assert MIGRATION_MATRIX["oracle_to_postgres"]["datatypes"]["DATE"]["lossy"] is True
    assert MIGRATION_MATRIX["oracle_to_mssql"]["datatypes"]["DATE"]["lossy"] is True
""")

print("Tests patched successfully.")
