import re
"""
Schema Agent for Universal Migration Engine.
Generates DDL deterministically using the Migration Matrix.
Uses LLM only for analysis and recommendations.
"""

import json
from typing import Any, Literal

import networkx as nx
from backend.config.migration_matrix import MIGRATION_MATRIX
from backend.models import DependencyResolution, FKEdge
from backend.services.llm_service import LLMService


class SchemaAgent:
    def __init__(self, llm_service: LLMService = None):
        self.llm_service = llm_service or LLMService()

    def generate_ddl(self, source_schema: dict[str, Any], direction: str) -> dict[str, Any]:
        """
        Deterministically generate DDL using the migration matrix.
        No LLM calls are made here.
        """
        if direction not in MIGRATION_MATRIX:
            raise ValueError(f"Unsupported migration direction: {direction}")

        matrix = MIGRATION_MATRIX[direction]
        type_mapping = matrix.get("datatypes", {})

        ddl_statements = []
        skipped_objects = []
        translation_log = []

        tables = source_schema.get("tables", [])
        for table in tables:
            table_name = table.get("name")
            columns = table.get("columns", [])
            primary_keys = table.get("primary_keys", [])

            if not columns:
                continue

            column_defs = []
            for col in columns:
                col_name = col.get("name")
                col_type = col.get("type", "").upper()

                # Extract base type (e.g., VARCHAR from VARCHAR(255))
                base_type = col_type.split("(")[0].strip()

                if direction.startswith("oracle_to_") and base_type == "NUMBER":
                    precision = col.get("precision")
                    scale = col.get("scale")
                    if scale == 0:
                        if precision is None:
                            target_type = "NUMERIC"
                        elif precision <= 9:
                            target_type = "INTEGER"
                        elif precision <= 18:
                            target_type = "BIGINT"
                        else:
                            target_type = f"NUMERIC({precision}, 0)"
                    elif precision is not None and scale is not None and scale > 0:
                        target_type = f"NUMERIC({precision}, {scale})"
                    else:
                        target_type = "NUMERIC"
                        
                    # Adapt NUMERIC based on target if needed, e.g., MySQL prefers DECIMAL
                    if "mysql" in direction:
                        target_type = target_type.replace("NUMERIC", "DECIMAL")
                        
                    mapping = {"type": target_type, "lossy": False, "note": "Dynamic NUMBER mapping"}
                else:
                    # Get mapped type or default to string type if not found
                    mapping = type_mapping.get(base_type)

                if mapping:
                    target_type = mapping["type"]
                    # If target supports length and source had length, preserve it
                    if "(" in col_type and "(" not in target_type:
                        if any(
                            target_type.upper().startswith(t)
                            for t in [
                                "VARCHAR",
                                "CHAR",
                                "NVARCHAR",
                                "NCHAR",
                                "DECIMAL",
                                "NUMERIC",
                                "FLOAT",
                                "DOUBLE",
                                "TIME",
                                "DATETIME",
                                "BINARY",
                                "VARBINARY",
                            ]
                        ):
                            if base_type.upper() in ["ENUM", "SET"]:
                                target_type += "(255)"
                            else:
                                length_part = col_type[col_type.find("(") :]
                                target_type += length_part
                    elif target_type in ["VARCHAR", "CHAR", "NVARCHAR", "NCHAR"] and "(" not in target_type:
                        # MySQL requires a length for VARCHAR
                        if "MAX" in col_type.upper():
                            target_type = "TEXT"
                        else:
                            target_type += "(255)"

                    translation_log.append(
                        {
                            "column": f"{table_name}.{col_name}",
                            "from": col_type,
                            "to": target_type,
                            "lossy": mapping.get("lossy", False),
                            "note": mapping.get("note", ""),
                        }
                    )
                else:
                    target_type = "VARCHAR(255)"  # Safe fallback
                    skipped_objects.append(
                        f"Datatype {col_type} in {table_name}.{col_name} not mapped, fallback to {target_type}"
                    )
                    translation_log.append(
                        {
                            "column": f"{table_name}.{col_name}",
                            "from": col_type,
                            "to": target_type,
                            "lossy": True,
                            "note": "Unmapped datatype fallback",
                        }
                    )

                is_pk = bool(primary_keys) and (col_name in primary_keys or col_name.lower() in [str(pk).lower() for pk in primary_keys])
                nullable = "NOT NULL" if (is_pk or not col.get("nullable", True)) else "NULL"
                
                check_constraint = ""
                if direction.endswith("_to_oracle") and target_type == "NUMBER(1)" and base_type in ("BOOLEAN", "BIT", "BOOL"):
                    check_constraint = f" CHECK ({col_name} IN (0, 1))"

                col_def = f"{col_name} {target_type} {nullable}{check_constraint}"
                column_defs.append(col_def)

            if primary_keys:
                pk_str = ", ".join(primary_keys)
                column_defs.append(f"PRIMARY KEY ({pk_str})")

            is_target_oracle = direction.endswith("_to_oracle")
            safe_table_name = table_name[:30] if is_target_oracle else table_name
            
            if is_target_oracle:
                cols_str = ",\n  ".join(column_defs)
                create_stmt = f"""BEGIN
  EXECUTE IMMEDIATE 'CREATE TABLE {safe_table_name} (
  {cols_str}
  )';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;"""
                ddl_statements.append(create_stmt)
                
                for col in columns:
                    if col.get("is_auto_increment") or "auto_increment" in str(col.get("type", "")).lower() or "serial" in str(col.get("type", "")).lower():
                        col_name = col.get("name")
                        seq_name = f"{safe_table_name}_{col_name}_seq"[:30]
                        trg_name = f"{safe_table_name}_{col_name}_trg"[:30]
                        
                        seq_stmt = f"""BEGIN
  EXECUTE IMMEDIATE 'CREATE SEQUENCE {seq_name} START WITH 1 INCREMENT BY 1';
EXCEPTION
  WHEN OTHERS THEN
    IF SQLCODE != -955 THEN
      RAISE;
    END IF;
END;"""
                        trg_stmt = f"""CREATE OR REPLACE TRIGGER {trg_name}
BEFORE INSERT ON {safe_table_name}
FOR EACH ROW
BEGIN
  IF :NEW.{col_name} IS NULL THEN
    SELECT {seq_name}.NEXTVAL INTO :NEW.{col_name} FROM sys.dual;
  END IF;
END;"""
                        ddl_statements.append(seq_stmt)
                        ddl_statements.append(trg_stmt)
            else:
                create_stmt = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(column_defs) + "\n);"
                ddl_statements.append(create_stmt)

            # NOTE: Foreign keys and indexes generation should ideally follow,
            # but sticking to core CREATE TABLE for DDL generation mapping as primary feature.
            # Foreign keys can be executed separately to avoid circular dependencies.

        return {
            "ddl_statements": ddl_statements,
            "skipped_objects": skipped_objects,
            "translation_log": translation_log,
        }

    async def analyze_ddl(self, ddl_statements: list[str]) -> dict[str, Any]:
        """
        Analyze the generated DDL using the LLM for warnings, recommendations, and unsupported object explanations.
        """
        ddl_text = "\n\n".join(ddl_statements)
        prompt = (
            "Analyze this DDL for a database migration. Return ONLY valid JSON with keys: "
            "warnings (list[str]), recommendations (list[str]), unsupported_object_explanations (list[str]).\n"
            f"DDL:\n{ddl_text}"
        )

        try:
            response_text = await self.llm_service.generate_response(prompt)
        except Exception as e:
            return {
                "status": "skipped",
                "warnings": [f"LLM Schema Analysis skipped: {str(e)}"],
                "recommendations": [
                    "Configure a valid API key or resolve connectivity issues to enable AI schema analysis."
                ],
                "unsupported_object_explanations": [],
            }

        try:
            # Try to parse the response as JSON directly
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback if parsing fails
            return {
                "warnings": ["Failed to parse LLM analysis response as JSON."],
                "recommendations": [],
                "unsupported_object_explanations": [],
            }

    def resolve_table_dependencies(
        self,
        selected_tables: list[str],
        all_tables_metadata: list[dict[str, Any]],
        mode: Literal["auto_include", "strict", "drop_constraint"],
    ) -> DependencyResolution:
        # Build directed graph
        graph = nx.DiGraph()

        # We need all tables in the graph
        for tm in all_tables_metadata:
            graph.add_node(tm["name"])

        # Add edges for FKs (from_table -> references -> to_table)
        for tm in all_tables_metadata:
            from_table = tm["name"]
            
            refs = tm.get("has_foreign_keys_to")
            if not refs:
                refs = [fk["references_table"] for fk in tm.get("foreign_keys", [])]
                
            for to_table in refs:
                if to_table in graph:
                    graph.add_edge(from_table, to_table)

        # Basic sets
        self_refs = [n for n in graph.nodes if graph.has_edge(n, n)]
        selected_set = set(selected_tables)

        # Simple cycles (excluding self-loops)
        cycles = []
        for c in nx.simple_cycles(graph):
            if len(c) > 1:
                cycles.append(c)

        if mode == "strict":
            # Just do a BFS from selected tables
            reachable = set()
            for t in selected_set:
                if t in graph:
                    reachable.update(nx.descendants(graph, t))
                    reachable.add(t)
            missing = reachable - selected_set
            if missing:
                return DependencyResolution(
                    final_table_set=list(selected_tables),
                    originally_selected=list(selected_tables),
                    auto_added=[],
                    auto_added_reasons={},
                    self_referencing_tables=self_refs,
                    circular_dependency_groups=cycles,
                    blocked=True,
                    missing_dependencies=list(missing),
                    dropped_constraints=[],
                    migration_order=[],
                )
            # If no missing, proceed as drop_constraint / normal
            final_set = selected_set
            auto_added = set()
            reasons = {}

        elif mode == "auto_include":
            final_set = set()
            for t in selected_set:
                if t in graph:
                    final_set.update(nx.descendants(graph, t))
                    final_set.add(t)

            auto_added = final_set - selected_set
            reasons = {}
            # Trace paths for reasons
            # For each auto-added table, find all shortest paths from any selected table
            for added in auto_added:
                reasons[added] = []
                for start_t in selected_set:
                    if nx.has_path(graph, start_t, added):
                        for path in nx.all_shortest_paths(graph, start_t, added):
                            # path is e.g. ["orders", "customers"]
                            # convert to reason string
                            reason_str = " -> ".join(path)
                            reasons[added].append(f"Added because {reason_str}")

                # deduplicate
                reasons[added] = list(set(reasons[added]))

        elif mode == "drop_constraint":
            final_set = selected_set
            auto_added = set()
            reasons = {}

        else:
            raise ValueError(f"Invalid mode {mode}")

        # Compute dropped constraints (any edge leaving final_set to outside final_set)
        dropped_constraints = []
        for u, v in graph.edges:
            if u in final_set and v not in final_set:
                dropped_constraints.append(
                    FKEdge(
                        from_table=u,
                        to_table=v,
                        fk_column="*",  # we don't have column detail in lightweight metadata
                        is_self_referencing=(u == v),
                    )
                )

        # Filter self_refs and cycles to only include those in final_set
        final_self_refs = [t for t in self_refs if t in final_set]
        final_cycles = []
        for c in cycles:
            # if all nodes in cycle are in final_set, include it
            if all(n in final_set for n in c):
                final_cycles.append(c)

        # Calculate migration order using condensation
        subgraph = graph.subgraph(final_set).copy()
        condensed = nx.condensation(subgraph)
        migration_order = []
        # sort condensed DAG topologically (reversed because we must insert referenced tables FIRST)
        for scc in reversed(list(nx.topological_sort(condensed))):
            members = condensed.nodes[scc]["members"]
            migration_order.extend(members)
        # Calculate migration generations for parallel execution
        migration_generations = []
        for generation in reversed(list(nx.topological_generations(condensed))):
            gen_members = []
            for scc in generation:
                gen_members.extend(condensed.nodes[scc]["members"])
            migration_generations.append(gen_members)

        return DependencyResolution(
            final_table_set=list(final_set),
            originally_selected=list(selected_tables),
            auto_added=list(auto_added),
            auto_added_reasons=reasons,
            self_referencing_tables=final_self_refs,
            circular_dependency_groups=final_cycles,
            blocked=False,
            missing_dependencies=[],
            dropped_constraints=dropped_constraints,
            migration_order=migration_order,
            migration_generations=migration_generations,
        )
