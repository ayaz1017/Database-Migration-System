import pytest
from backend.agents.schema_agent import SchemaAgent

def test_oracle_number_mapping():
    agent = SchemaAgent()

    # 1. NUMBER with no scale/precision should map to NUMERIC
    col = {"name": "c1", "type": "NUMBER"}
    schema = {"tables": [{"name": "t1", "columns": [col]}]}
    res = agent.generate_ddl(schema, "oracle_to_postgres")
    assert "NUMERIC" in res["ddl_statements"][0]

    # 2. NUMBER(9, 0) should map to INTEGER
    col = {"name": "c2", "type": "NUMBER", "precision": 9, "scale": 0}
    schema = {"tables": [{"name": "t2", "columns": [col]}]}
    res = agent.generate_ddl(schema, "oracle_to_postgres")
    assert "INTEGER" in res["ddl_statements"][0]

    # 3. NUMBER(15, 0) should map to BIGINT
    col = {"name": "c3", "type": "NUMBER", "precision": 15, "scale": 0}
    schema = {"tables": [{"name": "t3", "columns": [col]}]}
    res = agent.generate_ddl(schema, "oracle_to_postgres")
    assert "BIGINT" in res["ddl_statements"][0]

    # 4. NUMBER(20, 0) should map to NUMERIC(20, 0)
    col = {"name": "c4", "type": "NUMBER", "precision": 20, "scale": 0}
    schema = {"tables": [{"name": "t4", "columns": [col]}]}
    res = agent.generate_ddl(schema, "oracle_to_postgres")
    assert "NUMERIC(20, 0)" in res["ddl_statements"][0]

    # 5. NUMBER(10, 2) should map to NUMERIC(10, 2)
    col = {"name": "c5", "type": "NUMBER", "precision": 10, "scale": 2}
    schema = {"tables": [{"name": "t5", "columns": [col]}]}
    res = agent.generate_ddl(schema, "oracle_to_postgres")
    assert "NUMERIC(10, 2)" in res["ddl_statements"][0]

def test_oracle_mysql_mapping():
    agent = SchemaAgent()

    # NUMBER(10,2) to MySQL should map to DECIMAL(10, 2)
    col = {"name": "c1", "type": "NUMBER", "precision": 10, "scale": 2}
    schema = {"tables": [{"name": "t1", "columns": [col]}]}
    res = agent.generate_ddl(schema, "oracle_to_mysql")
    assert "DECIMAL(10, 2)" in res["ddl_statements"][0]
