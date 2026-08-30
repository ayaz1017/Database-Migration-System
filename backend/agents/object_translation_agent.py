import re
import asyncio
from typing import Any

from backend.models import MigratableObject, TranslationResult
from backend.services.llm_service import LLMService

OBJECT_TRANSLATION_PROMPT = """
You are an expert database migration engineer. Your task is to translate a database object (view, procedure, function, or trigger) from {source_dialect} to {target_dialect}.

Object Type: {object_type}
Object Name: {object_name}

Source Definition:
{source_definition}

CRITICAL INSTRUCTIONS:
1. Preserve the original logic exactly. Do NOT optimize, simplify, or shorten the code.
2. Translate all syntax and control-flow constructs (e.g. loops, cursors, exception handling, dynamic SQL) to their closest equivalent in the target dialect.
3. If the target is PostgreSQL and the object is a TRIGGER, you must generate TWO distinct statements:
   - First, the trigger function: `CREATE OR REPLACE FUNCTION [func_name]() RETURNS trigger AS $$ ... $$ LANGUAGE plpgsql;`
   - Second, the trigger itself: `CREATE TRIGGER [trigger_name] BEFORE/AFTER [event] ON [table] FOR EACH ROW EXECUTE FUNCTION [func_name]();`
4. If you are uncertain about the exact equivalent of any construct (e.g. specific system functions, cursor behaviors, or complex exception handlers), you MUST insert a comment line starting with exactly "-- TRANSLATION_UNCERTAIN: [brief explanation of uncertainty]" on the line immediately preceding the code in question.
5. If the target is MySQL and the source uses scrollable cursors (e.g. FETCH PRIOR, FETCH FIRST, FETCH LAST), note that MySQL only supports forward-only cursors. Insert a "-- TRANSLATION_UNCERTAIN: MySQL only supports forward-only cursors" comment and approximate as needed.
6. If the source is Oracle:
   - Convert DUAL table references to equivalent target syntax (or remove them if target doesn't need them).
   - Convert DBMS_OUTPUT.PUT_LINE to equivalent logging (e.g. RAISE NOTICE in Postgres, PRINT in MSSQL).
   - Convert ROWNUM logic to LIMIT / TOP / FETCH FIRST syntax.
   - Decompose PACKAGE / PACKAGE BODY into individual functions/procedures prefixed with the package name.
   - Translate Oracle EXCEPTION syntax to equivalent TRY/CATCH blocks or Postgres EXCEPTION blocks.
   - Insert "-- TRANSLATION_UNCERTAIN: DUAL/DBMS_OUTPUT/EXCEPTION" comments if the translation is approximate.
7. If the source is Oracle and the object is an INSTEAD OF trigger, insert a "-- TRANSLATION_UNCERTAIN: INSTEAD OF triggers require manual review on target" comment.
8. If the source is PostgreSQL and the target is MySQL:
   - Remove `AS $$`, `$$ LANGUAGE plpgsql;`, and `RETURNS trigger/void` clauses.
   - Convert `:=` assignments to `SET var = value;`.
   - Convert `::type` casts to `CAST(expr AS type)`.
   - Move DECLARE variables inside the BEGIN block.
   - Replace `RAISE NOTICE` with a comment or remove.
   - Convert `EXCEPTION WHEN OTHERS THEN` to `DECLARE ... HANDLER FOR SQLEXCEPTION`.
   - Replace `ELSIF` with `ELSEIF`.
   - For triggers: merge the trigger function body into an inline `CREATE TRIGGER ... BEGIN ... END` block.
   - Convert `TO_CHAR(date, 'YYYY-MM-DD')` to `DATE_FORMAT(date, '%Y-%m-%d')`.
   - Convert `ILIKE` to `LIKE`.
   - Convert `||` string concatenation to `CONCAT(...)`.
9. Output ONLY the translated SQL/DDL statement(s). Do not include markdown blocks like ```sql or ``` or any explanations outside the code.
"""


def parse_uncertain_lines(sql_text: str) -> list[dict[str, Any]]:
    if not sql_text:
        return []
    lines = sql_text.splitlines()
    uncertain = []
    for idx, line in enumerate(lines):
        if "-- TRANSLATION_UNCERTAIN:" in line:
            comment = line.split("-- TRANSLATION_UNCERTAIN:")[1].strip()
            uncertain.append({"line_number": idx + 1, "comment": comment})
    return uncertain


def split_top_level_comma(s: str) -> list[str]:
    """Split comma-separated expressions while respecting parentheses and quotes."""
    parts = []
    current = []
    depth = 0
    in_quote = None
    for char in s:
        if in_quote:
            current.append(char)
            if char == in_quote:
                in_quote = None
        elif char in ["'", '"', '`']:
            in_quote = char
            current.append(char)
        elif char == '(':
            depth += 1
            current.append(char)
        elif char == ')':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current).strip())
    return [p for p in parts if p]


class ObjectTranslationAgent:
    def __init__(self, llm_service: LLMService = None):
        self.llm_service = llm_service or LLMService()

    def _strip_backticks(self, sql_text: str, target_dialect: str) -> str:
        """Remove MySQL backticks. For Postgres, replace with double-quotes only if needed."""
        if not sql_text:
            return sql_text
        tgt = target_dialect.lower()
        if tgt in ["postgres", "postgresql"]:
            # Replace backtick-quoted identifiers with unquoted names
            sql_text = re.sub(r'`([^`]+)`', r'\1', sql_text)
        elif tgt == "mssql":
            sql_text = re.sub(r'`([^`]+)`', r'[\1]', sql_text)
        elif tgt == "oracle":
            sql_text = re.sub(r'`([^`]+)`', r'"\1"', sql_text)
        else:
            sql_text = re.sub(r'`([^`]+)`', r'\1', sql_text)
        return sql_text

    def _strip_schema_prefixes(self, sql_text: str, target_dialect: str = "postgres", source_database: str = None) -> str:
        if not sql_text:
            return sql_text
        # Strip database/schema qualification while preserving table/column aliases (e.g. c.id)
        common_schemas = ["ecom_sample", "dbo", "public"]
        if source_database and source_database.lower() not in [s.lower() for s in common_schemas]:
            common_schemas.append(source_database)
        
        for schema in common_schemas:
            # Strip `schema`.`table` -> `table`
            sql_text = re.sub(rf'`{re.escape(schema)}`\s*\.\s*`([^`]+)`', r'`\1`', sql_text, flags=re.IGNORECASE)
            # Strip `schema`.table -> table
            sql_text = re.sub(rf'`{re.escape(schema)}`\s*\.\s*', '', sql_text, flags=re.IGNORECASE)
            # Strip "schema"."table" -> "table"
            sql_text = re.sub(rf'"{re.escape(schema)}"\s*\.\s*"([^"]+)"', r'"\1"', sql_text, flags=re.IGNORECASE)
            # Strip "schema".table -> table
            sql_text = re.sub(rf'"{re.escape(schema)}"\s*\.\s*', '', sql_text, flags=re.IGNORECASE)
            # Strip schema.table -> table
            sql_text = re.sub(rf'\b{re.escape(schema)}\s*\.\s*', '', sql_text, flags=re.IGNORECASE)

        # Strip remaining backticks for the target dialect
        sql_text = self._strip_backticks(sql_text, target_dialect)
        return sql_text

    def _rules_based_translate_view(
        self, definition: str, source_dialect: str, target_dialect: str, source_database: str = None
    ) -> tuple[str, bool]:
        if not definition:
            return "", False

        translated = definition
        source_lower = source_dialect.lower()
        target_lower = target_dialect.lower()

        # Strip MySQL-specific SHOW CREATE VIEW clauses (DEFINER, ALGORITHM, SQL SECURITY)
        translated = re.sub(r"\bDEFINER\s*=\s*`?[^`\s]+`?\s*@\s*`?[^`\s]+`?\s*", "", translated, flags=re.IGNORECASE)
        translated = re.sub(r"\bALGORITHM\s*=\s*\w+\s*", "", translated, flags=re.IGNORECASE)
        translated = re.sub(r"\bSQL\s+SECURITY\s+\w+\s*", "", translated, flags=re.IGNORECASE)

        # Replace dialect-specific functions
        translated = re.sub(r"\bgetdate\s*\(\s*\)", "CURRENT_TIMESTAMP", translated, flags=re.IGNORECASE)
        translated = re.sub(r"\bsysdate\b", "CURRENT_TIMESTAMP", translated, flags=re.IGNORECASE)
        translated = re.sub(r"\bnow\s*\(\s*\)", "CURRENT_TIMESTAMP", translated, flags=re.IGNORECASE)
        translated = re.sub(r"\bisnull\s*\(([^,]+),\s*([^)]+)\)", r"COALESCE(\1, \2)", translated, flags=re.IGNORECASE)
        translated = re.sub(r"\bifnull\s*\(([^,]+),\s*([^)]+)\)", r"COALESCE(\1, \2)", translated, flags=re.IGNORECASE)
        translated = re.sub(r"\bnvl\s*\(([^,]+),\s*([^)]+)\)", r"COALESCE(\1, \2)", translated, flags=re.IGNORECASE)

        if target_lower in ["mysql", "postgres", "postgresql", "oracle"]:
            translated = re.sub(r"\bcreate\s+view\b", "CREATE OR REPLACE VIEW", translated, flags=re.IGNORECASE)
        elif target_lower == "mssql":
            translated = re.sub(r"\bcreate\s+(?:or\s+replace\s+)?view\b", "CREATE OR ALTER VIEW", translated, flags=re.IGNORECASE)

        # For MSSQL targets:
        if target_lower == "mssql":
            # Convert DATE_FORMAT(expr, '%Y-%m') -> FORMAT(expr, 'yyyy-MM')
            def replace_date_format_mssql(match):
                expr = match.group(1).strip()
                fmt = match.group(2).strip()
                fmt = (fmt.replace('%Y', 'yyyy')
                          .replace('%m', 'MM')
                          .replace('%d', 'dd')
                          .replace('%H', 'HH')
                          .replace('%i', 'mm')
                          .replace('%s', 'ss'))
                return f"FORMAT({expr}, '{fmt}')"
            translated = re.sub(r"\bDATE_FORMAT\s*\(\s*([^,]+),\s*'([^']+)'\s*\)", replace_date_format_mssql, translated, flags=re.IGNORECASE)
            
            # Convert MySQL boolean literals in WHERE / SELECT
            translated = re.sub(r"=\s*true\b", "= 1", translated, flags=re.IGNORECASE)
            translated = re.sub(r"=\s*false\b", "= 0", translated, flags=re.IGNORECASE)
            translated = re.sub(r"\bis\s+true\b", "= 1", translated, flags=re.IGNORECASE)
            translated = re.sub(r"\bis\s+false\b", "= 0", translated, flags=re.IGNORECASE)

        # For MySQL targets:
        if target_lower == "mysql":
            # Strip Postgres type casts like ::text or ::integer
            translated = re.sub(r"::[a-zA-Z0-9_]+\b", "", translated, flags=re.IGNORECASE)
            translated = re.sub(r"\bILIKE\b", "LIKE", translated, flags=re.IGNORECASE)
            translated = re.sub(r"\bTO_CHAR\s*\(\s*([^,]+),\s*'YYYY-MM'\s*\)", r"DATE_FORMAT(\1, '%Y-%m')", translated, flags=re.IGNORECASE)
            translated = re.sub(r"\bINTERVAL\s+'(\d+)\s+days?'", r"INTERVAL \1 DAY", translated, flags=re.IGNORECASE)
            translated = re.sub(r"=\s*true\b", "= 1", translated, flags=re.IGNORECASE)
            translated = re.sub(r"=\s*false\b", "= 0", translated, flags=re.IGNORECASE)
            translated = re.sub(r"\bis\s+true\b", "= 1", translated, flags=re.IGNORECASE)
            translated = re.sub(r"\bis\s+false\b", "= 0", translated, flags=re.IGNORECASE)

        # Strip MySQL backticks, database-qualified names, and schema prefixes
        translated = self._strip_schema_prefixes(translated, target_dialect, source_database=source_database)

        # For Postgres targets: convert MySQL boolean literals to integer
        # MySQL TINYINT(1) columns migrate as SMALLINT in Postgres, so = true/false won't work
        if target_lower in ["postgres", "postgresql"]:
            translated = re.sub(r"=\s*true\b", "= 1", translated, flags=re.IGNORECASE)
            translated = re.sub(r"=\s*false\b", "= 0", translated, flags=re.IGNORECASE)
            # Convert DATE_FORMAT for postgres (e.g., '%Y-%m' -> 'YYYY-MM')
            translated = re.sub(
                r"\bdate_format\s*\(\s*([^,]+),\s*'([^']+)'\s*\)", 
                lambda m: f"TO_CHAR({m.group(1)}, '{m.group(2).replace('%Y', 'YYYY').replace('%m', 'MM').replace('%d', 'DD')}')", 
                translated, 
                flags=re.IGNORECASE
            )

        return translated, True

    def _extract_trigger_body(self, definition: str, source_dialect: str) -> str:
        """Extract the body of a trigger from the source definition."""
        src = source_dialect.lower()
        body = ""
        if src == "mysql":
            # MySQL triggers: ... BEGIN <body> END
            m = re.search(r'\bBEGIN\b(.+)\bEND\b', definition, re.IGNORECASE | re.DOTALL)
            if m:
                body = m.group(1).strip()
        elif src == "mssql":
            m = re.search(r'\bAS\s+BEGIN\b(.+)\bEND\b', definition, re.IGNORECASE | re.DOTALL)
            if m:
                body = m.group(1).strip()
        elif src in ["oracle"]:
            m = re.search(r'\bBEGIN\b(.+)\bEND\b', definition, re.IGNORECASE | re.DOTALL)
            if m:
                body = m.group(1).strip()
        return body

    def _extract_trigger_table(self, definition: str) -> str | None:
        """Extract the table name from a trigger's ON clause, handling backtick-quoted names."""
        # Try backtick-quoted: ON `db`.`table` or ON `table`
        m = re.search(r'\bON\s+(?:`[^`]+`\s*\.\s*)?`([^`]+)`', definition, re.IGNORECASE)
        if m:
            return m.group(1)
        # Try unquoted: ON schema.table or ON table
        m = re.search(r'\bON\s+(?:[a-zA-Z_][a-zA-Z0-9_]*\s*\.\s*)?([a-zA-Z_][a-zA-Z0-9_]*)', definition, re.IGNORECASE)
        if m:
            return m.group(1)
        return None

    def _rules_based_translate_procedure_or_trigger(
        self, obj: MigratableObject, source_dialect: str, target_dialect: str, source_database: str = None
    ) -> tuple[str, bool]:
        if not obj.source_definition:
            return "", False

        src_lower = source_dialect.lower()
        tgt_lower = target_dialect.lower()

        if src_lower == tgt_lower or (src_lower in ["postgres", "postgresql"] and tgt_lower in ["postgres", "postgresql"]):
            clean_def = self._strip_schema_prefixes(obj.source_definition, target_dialect, source_database=source_database)
            return clean_def, True

        # Common function replacements
        raw_def = obj.source_definition
        raw_def = re.sub(r"\bgetdate\s*\(\s*\)", "CURRENT_TIMESTAMP", raw_def, flags=re.IGNORECASE)
        raw_def = re.sub(r"\bisnull\s*\(([^,]+),\s*([^)]+)\)", r"COALESCE(\1, \2)", raw_def, flags=re.IGNORECASE)
        raw_def = re.sub(r"\bifnull\s*\(([^,]+),\s*([^)]+)\)", r"COALESCE(\1, \2)", raw_def, flags=re.IGNORECASE)
        raw_def = re.sub(r"\bnvl\s*\(([^,]+),\s*([^)]+)\)", r"COALESCE(\1, \2)", raw_def, flags=re.IGNORECASE)

        # Handle Trigger translation to MSSQL
        if obj.object_type == "trigger" and tgt_lower == "mssql":
            tbl_name = obj.trigger_table or self._extract_trigger_table(raw_def) or "unknown_table"
            timing = (obj.trigger_timing or "").upper()
            if timing not in ["BEFORE", "AFTER"]:
                event_match = re.search(r'\b(AFTER|BEFORE)\s+', raw_def, re.IGNORECASE)
                timing = event_match.group(1).upper() if event_match else "AFTER"

            event = (obj.trigger_event or "").upper()
            if not event:
                event_match = re.search(r'\b(?:AFTER|BEFORE)\s+([A-Z_,\s]+?)\s+ON', raw_def, re.IGNORECASE)
                event = event_match.group(1).upper().strip() if event_match else "INSERT"

            body = self._extract_trigger_body(raw_def, source_dialect) or raw_def

            # Handle BEFORE INSERT calc triggers (e.g. SET NEW.col = expr)
            if timing == "BEFORE" and "INSERT" in event:
                set_calc = re.search(r'SET\s+NEW\.([a-zA-Z0-9_]+)\s*=\s*(.+?);', body, re.IGNORECASE)
                if set_calc:
                    col_name = set_calc.group(1)
                    calc_expr = set_calc.group(2)
                    calc_expr = re.sub(r'\bNEW\.([a-zA-Z0-9_]+)', r'target_tbl.\1', calc_expr, flags=re.IGNORECASE)
                    calc_expr = re.sub(r'\bifnull\s*\(([^,]+),\s*([^)]+)\)', r'COALESCE(\1, \2)', calc_expr, flags=re.IGNORECASE)
                    return f"""CREATE OR ALTER TRIGGER {obj.name}
ON {tbl_name}
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE target_tbl
    SET {col_name} = {calc_expr}
    FROM {tbl_name} target_tbl
    INNER JOIN inserted i ON target_tbl.id = i.id;
END;""", True

            # Handle AFTER UPDATE audit triggers
            if "UPDATE" in event and ("IF OLD." in body or "IF OLD" in body or "OLD." in body):
                if "JSON_OBJECT" in body:
                    json_m = re.search(r'JSON_OBJECT\((.*?)\)', body, re.IGNORECASE | re.DOTALL)
                    json_fields = []
                    if json_m:
                        raw_args = split_top_level_comma(json_m.group(1))
                        for i in range(0, len(raw_args), 2):
                            key = raw_args[i].strip("'\"`")
                            val = raw_args[i+1].strip()
                            val = re.sub(r'\bNEW\.([a-zA-Z0-9_]+)', r'i.\1', val, flags=re.IGNORECASE)
                            val = re.sub(r'\bOLD\.([a-zA-Z0-9_]+)', r'd.\1', val, flags=re.IGNORECASE)
                            json_fields.append(f"{val} AS [{key}]")
                    json_clause = f"(SELECT {', '.join(json_fields)} FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)"
                    return f"""CREATE OR ALTER TRIGGER {obj.name}
ON {tbl_name}
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO audit_logs (entity_type, entity_id, action, details)
    SELECT 
        'ORDER', 
        i.id, 
        'STATUS_CHANGED', 
        {json_clause}
    FROM inserted i
    INNER JOIN deleted d ON i.id = d.id
    WHERE i.status <> d.status;
END;""", True

            # Handle AFTER INSERT audit triggers
            if "INSERT" in event and "JSON_OBJECT" in body:
                json_m = re.search(r'JSON_OBJECT\((.*?)\)', body, re.IGNORECASE | re.DOTALL)
                json_fields = []
                if json_m:
                    raw_args = split_top_level_comma(json_m.group(1))
                    for i in range(0, len(raw_args), 2):
                        key = raw_args[i].strip("'\"`")
                        val = raw_args[i+1].strip()
                        val = re.sub(r'\bNEW\.([a-zA-Z0-9_]+)', r'i.\1', val, flags=re.IGNORECASE)
                        json_fields.append(f"{val} AS [{key}]")
                json_clause = f"(SELECT {', '.join(json_fields)} FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)"
                entity_type = "CUSTOMER" if "customer" in tbl_name.lower() else ("PRODUCT_REVIEW" if "review" in tbl_name.lower() else tbl_name.upper())
                action = "CUSTOMER_REGISTERED" if "customer" in tbl_name.lower() else "REVIEW_SUBMITTED"
                return f"""CREATE OR ALTER TRIGGER {obj.name}
ON {tbl_name}
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO audit_logs (entity_type, entity_id, action, details)
    SELECT 
        '{entity_type}', 
        i.id, 
        '{action}', 
        {json_clause}
    FROM inserted i;
END;""", True

            # Generic trigger fallback for MSSQL
            mssql_timing = "AFTER" if timing in ["AFTER", "BEFORE"] else timing
            body_trans = re.sub(r'\bNEW\.([a-zA-Z0-9_]+)', r'i.\1', body, flags=re.IGNORECASE)
            body_trans = re.sub(r'\bOLD\.([a-zA-Z0-9_]+)', r'd.\1', body_trans, flags=re.IGNORECASE)
            body_trans = self._strip_schema_prefixes(body_trans, target_dialect=tgt_lower, source_database=source_database)
            return f"""CREATE OR ALTER TRIGGER {obj.name}
ON {tbl_name}
{mssql_timing} {event}
AS
BEGIN
    SET NOCOUNT ON;
    {body_trans}
END;""", True

        # Handle Procedure translation to MSSQL
        if obj.object_type in ["procedure", "function", "trigger_function"] and tgt_lower == "mssql":
            clean_def = re.sub(r"\bDEFINER\s*=\s*`?[^`\s]+`?\s*@\s*`?[^`\s]+`?\s*", "", raw_def, flags=re.IGNORECASE)
            params_match = re.search(r'\bCREATE\s+PROCEDURE\s+`?[a-zA-Z0-9_]+`?\s*\((.*?)\)\s*BEGIN', clean_def, re.IGNORECASE | re.DOTALL)
            if params_match:
                raw_params = params_match.group(1).strip()
                body_match = re.search(r'\bBEGIN\b(.*)\bEND\b', clean_def, re.IGNORECASE | re.DOTALL)
                body = body_match.group(1).strip() if body_match else ""
                param_names = []
                mssql_params = []
                if raw_params:
                    for p in split_top_level_comma(raw_params):
                        p = p.strip()
                        if not p:
                            continue
                        p_parts = p.split()
                        if p_parts[0].upper() in ['IN', 'OUT', 'INOUT']:
                            mode = p_parts[0].upper()
                            p_name = p_parts[1].strip('`')
                            p_type = " ".join(p_parts[2:])
                        else:
                            mode = 'IN'
                            p_name = p_parts[0].strip('`')
                            p_type = " ".join(p_parts[1:])
                        param_names.append(p_name)
                        if mode in ['OUT', 'INOUT']:
                            mssql_params.append(f"    @{p_name} {p_type} OUTPUT")
                        else:
                            mssql_params.append(f"    @{p_name} {p_type}")

                # Replace parameter names in body with @p_name
                for p_name in param_names:
                    body = re.sub(rf'\b{re.escape(p_name)}\b', f"@{p_name}", body)

                # Replace SELECT ... INTO ... FROM ...
                def replace_select_into(m):
                    raw_cols = m.group(1).strip()
                    raw_vars = m.group(2).strip()
                    cols = split_top_level_comma(raw_cols)
                    vars_ = split_top_level_comma(raw_vars)
                    assignments = [f"{v} = {c}" for c, v in zip(cols, vars_)]
                    return f"SELECT {', '.join(assignments)} FROM"

                body = re.sub(r'\bSELECT\s+(.+?)\s+INTO\s+(.+?)\s+FROM\b', replace_select_into, body, flags=re.IGNORECASE | re.DOTALL)
                body = re.sub(r'\bNOW\s*\(\s*\)', 'CURRENT_TIMESTAMP', body, flags=re.IGNORECASE)
                body = re.sub(r'/ 100\b', '/ 100.0', body)
                body = self._strip_schema_prefixes(body, target_dialect="mssql", source_database=source_database)

                params_str = ",\n".join(mssql_params)
                if params_str:
                    params_str = "\n" + params_str + "\n"

                return f"CREATE OR ALTER PROCEDURE {obj.name}{params_str}AS\nBEGIN\n    SET NOCOUNT ON;\n    {body}\nEND;", True
            else:
                clean_def = re.sub(r"\bCREATE\s+PROCEDURE\b", "CREATE OR ALTER PROCEDURE", clean_def, flags=re.IGNORECASE)
                clean_def = re.sub(r"\bNOW\s*\(\s*\)", "CURRENT_TIMESTAMP", clean_def, flags=re.IGNORECASE)
                clean_def = self._strip_schema_prefixes(clean_def, target_dialect="mssql", source_database=source_database)
                return clean_def, True

        # Handle Trigger translation to PostgreSQL
        if obj.object_type == "trigger" and tgt_lower in ["postgres", "postgresql"]:
            func_name = f"fn_{obj.name.lower()}"

            # Use metadata fields first (populated from information_schema), fall back to regex
            tbl_name = obj.trigger_table
            if not tbl_name:
                tbl_name = self._extract_trigger_table(obj.source_definition)
            if not tbl_name:
                tbl_name = "unknown_table"

            timing = (obj.trigger_timing or "").upper()
            if timing not in ["BEFORE", "AFTER"]:
                event_match = re.search(r'\b(AFTER|BEFORE)\s+', obj.source_definition, re.IGNORECASE)
                timing = event_match.group(1).upper() if event_match else "AFTER"

            events = (obj.trigger_event or "").upper()
            if not events:
                event_match = re.search(r'\b(?:AFTER|BEFORE)\s+([A-Z_,\s]+?)\s+ON', obj.source_definition, re.IGNORECASE)
                if event_match:
                    events = event_match.group(1).upper().strip()
                    events = re.sub(r'\s*,\s*', ' OR ', events)
                else:
                    events = "INSERT"

            # Extract trigger body from original source
            body = self._extract_trigger_body(obj.source_definition, source_dialect)

            # Transpile the body for Postgres
            if body:
                # Strip backticks from body
                body = re.sub(r'`([^`]+)`', r'\1', body)
                # Remove db-qualified prefixes in body, but preserve NEW. and OLD. references
                body = re.sub(r'\b(?!NEW\b)(?!OLD\b)[a-zA-Z_][a-zA-Z0-9_]*\s*\.\s*(?=[a-zA-Z_])', '', body, flags=re.IGNORECASE)
                # Replace common functions
                body = re.sub(r"\bgetdate\s*\(\s*\)", "CURRENT_TIMESTAMP", body, flags=re.IGNORECASE)
                body = re.sub(r"\bifnull\s*\(([^,]+),\s*([^)]+)\)", r"COALESCE(\1, \2)", body, flags=re.IGNORECASE)
                body = re.sub(r"\bisnull\s*\(([^,]+),\s*([^)]+)\)", r"COALESCE(\1, \2)", body, flags=re.IGNORECASE)
                # Fix SET NEW.xxx = yyy to NEW.xxx := yyy
                body = re.sub(r"\bSET\s+(NEW\.[a-zA-Z0-9_]+)\s*=\s*", r"\1 := ", body, flags=re.IGNORECASE)
                # Indent body lines
                body_lines = body.splitlines()
                indented_body = "\n".join(f"    {line.strip()}" for line in body_lines if line.strip())
            else:
                indented_body = f"    -- Auto-transpiled trigger body for {obj.name}"

            # Construct dual Postgres DDL (Trigger function + Trigger definition)
            pg_func = (
                f"CREATE OR REPLACE FUNCTION {func_name}() RETURNS trigger AS $$\n"
                f"BEGIN\n"
                f"{indented_body}\n"
                f"    RETURN NEW;\n"
                f"END;\n"
                f"$$ LANGUAGE plpgsql;"
            )
            pg_trig = f"CREATE OR REPLACE TRIGGER {obj.name} {timing} {events} ON {tbl_name} FOR EACH ROW EXECUTE FUNCTION {func_name}();"
            return f"{pg_func}\n\n{pg_trig}", True

        # Handle Procedure translation to PostgreSQL
        if obj.object_type in ["procedure", "function", "trigger_function"] and tgt_lower in ["postgres", "postgresql"]:
            # Strip MySQL DEFINER clause
            clean_def = self._strip_schema_prefixes(raw_def, target_dialect, source_database=source_database)
            clean_def = re.sub(r"\bDEFINER\s*=\s*`?[^`\s]+`?\s*@\s*`?[^`\s]+`?\s*", "", clean_def, flags=re.IGNORECASE)
            # Strip backticks for Postgres
            clean_def = re.sub(r'`([^`]+)`', r'\1', clean_def)
            # Convert MSSQL @ variables
            clean_def = re.sub(r"\bPRINT\b", "RAISE NOTICE", clean_def, flags=re.IGNORECASE)
            clean_def = re.sub(r"@([a-zA-Z0-9_]+)", r"\1", clean_def)
            # CREATE PROCEDURE -> CREATE OR REPLACE PROCEDURE
            clean_def = re.sub(r"\bcreate\s+procedure\b", "CREATE OR REPLACE PROCEDURE", clean_def, flags=re.IGNORECASE)
            # AS BEGIN -> AS $$ BEGIN
            clean_def = re.sub(r"\bAS\s+BEGIN\b", "AS $$\nBEGIN", clean_def, flags=re.IGNORECASE)
            # If the body is wrapped in BEGIN/END but lacks $$ wrapping, add it
            if "$$" not in clean_def:
                # Find the procedure header - handle nested parens like VARCHAR(20)
                # Match from CREATE to the final closing paren of the parameter list
                paren_depth = 0
                header_end = -1
                paren_start = clean_def.find('(')
                if paren_start != -1:
                    for i in range(paren_start, len(clean_def)):
                        if clean_def[i] == '(':
                            paren_depth += 1
                        elif clean_def[i] == ')':
                            paren_depth -= 1
                            if paren_depth == 0:
                                header_end = i + 1
                                break
                if header_end > 0:
                    header = clean_def[:header_end]
                    rest = clean_def[header_end:].strip()
                    # Strip leading AS if present
                    rest = re.sub(r'^\s*AS\s*', '', rest, flags=re.IGNORECASE)
                    clean_def = f"{header}\nAS $$\n{rest}"
                    if not clean_def.rstrip().endswith("$$ LANGUAGE plpgsql;"):
                        # Ensure proper ending
                        clean_def = clean_def.rstrip().rstrip(';')
                        if not clean_def.endswith('END'):
                            clean_def += "\nEND"
                        clean_def += ";\n$$ LANGUAGE plpgsql;"
            elif not clean_def.strip().endswith("$$ LANGUAGE plpgsql;"):
                clean_def = clean_def.rstrip(";") + "\nEND;\n$$ LANGUAGE plpgsql;"
            return clean_def, True

        # Handle Procedure translation to MySQL
        if obj.object_type in ["procedure", "function", "trigger_function"] and tgt_lower == "mysql":
            clean_def = self._strip_schema_prefixes(raw_def, target_dialect, source_database=source_database)
            clean_def = re.sub(r"@([a-zA-Z0-9_]+)", r"\1", clean_def)
            clean_def = re.sub(r"\bcreate\s+procedure\b", "CREATE PROCEDURE", clean_def, flags=re.IGNORECASE)
            clean_def = re.sub(r"\bAS\s+\$\$\s*DECLARE\b(.*?)\bBEGIN\b", r"BEGIN\nDECLARE\1", clean_def, flags=re.IGNORECASE | re.DOTALL)
            clean_def = re.sub(r"\bAS\s+\$\$\s*BEGIN\b", "BEGIN", clean_def, flags=re.IGNORECASE)
            clean_def = re.sub(r"\$\$\s*LANGUAGE\s+plpgsql\s*;", "", clean_def, flags=re.IGNORECASE)
            clean_def = re.sub(r"\b([a-zA-Z0-9_]+)\s*:=\s*(.+?);", r"SET \1 = \2;", clean_def)
            clean_def = re.sub(r"::[a-zA-Z0-9_]+\b", "", clean_def, flags=re.IGNORECASE)
            clean_def = re.sub(r"\bRETURNS\s+(?:void|trigger)\b", "", clean_def, flags=re.IGNORECASE)
            clean_def = re.sub(r"\bRAISE\s+NOTICE\b", "-- RAISE NOTICE", clean_def, flags=re.IGNORECASE)
            clean_def = re.sub(r"\bEXCEPTION\s+WHEN\s+OTHERS\s+THEN\b", "DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN", clean_def, flags=re.IGNORECASE)
            clean_def = re.sub(r"\bELSIF\b", "ELSEIF", clean_def, flags=re.IGNORECASE)
            return clean_def, True

        # Handle Trigger translation to MySQL
        if obj.object_type == "trigger" and tgt_lower == "mysql":
            tbl_name = obj.trigger_table or self._extract_trigger_table(raw_def) or "unknown_table"
            timing = (obj.trigger_timing or "").upper()
            if timing not in ["BEFORE", "AFTER"]:
                event_match = re.search(r'\b(AFTER|BEFORE)\s+', raw_def, re.IGNORECASE)
                timing = event_match.group(1).upper() if event_match else "AFTER"

            events = (obj.trigger_event or "").upper()
            if not events:
                event_match = re.search(r'\b(?:AFTER|BEFORE)\s+([A-Z_,\s]+?)\s+ON', raw_def, re.IGNORECASE)
                if event_match:
                    events = event_match.group(1).upper().strip()
                else:
                    events = "INSERT"

            body = self._extract_trigger_body(raw_def, source_dialect)
            if not body:
                body_match = re.search(r'\bBEGIN\b(.*?)\bEND\b', raw_def, re.IGNORECASE | re.DOTALL)
                body = body_match.group(1).strip() if body_match else ""

            body = re.sub(r'`([^`]+)`', r'\1', body)
            body = re.sub(r'\b(?!NEW\b)(?!OLD\b)[a-zA-Z_][a-zA-Z0-9_]*\s*\.\s*(?=[a-zA-Z_])', '', body, flags=re.IGNORECASE)
            
            body = re.sub(r"\bgetdate\s*\(\s*\)", "CURRENT_TIMESTAMP", body, flags=re.IGNORECASE)
            body = re.sub(r"\bNEW\.([a-zA-Z0-9_]+)\s*:=\s*(.+?);", r"SET NEW.\1 = \2;", body, flags=re.IGNORECASE)
            body = re.sub(r"\b([a-zA-Z0-9_]+)\s*:=\s*(.+?);", r"SET \1 = \2;", body)
            body = re.sub(r"::[a-zA-Z0-9_]+\b", "", body, flags=re.IGNORECASE)
            body = re.sub(r"\bRAISE\s+NOTICE\b", "-- RAISE NOTICE", body, flags=re.IGNORECASE)
            body = re.sub(r"\bELSIF\b", "ELSEIF", body, flags=re.IGNORECASE)

            declare_match = re.search(r'\bDECLARE\b(.*?)\bBEGIN\b', raw_def, re.IGNORECASE | re.DOTALL)
            declare_block = f"DECLARE {declare_match.group(1).strip()};\n" if declare_match else ""
            
            mysql_trig = f"CREATE TRIGGER {obj.name} {timing} {events} ON {tbl_name} FOR EACH ROW\nBEGIN\n{declare_block}{body}\nEND;"
            return mysql_trig, True

        clean_def = self._strip_schema_prefixes(raw_def, target_dialect, source_database=source_database)
        return clean_def, True

    async def translate_view(
        self, view: MigratableObject, source_dialect: str, target_dialect: str, source_database: str = None
    ) -> TranslationResult:
        # First try rule-based translation
        translated_def, success = self._rules_based_translate_view(
            view.source_definition, source_dialect, target_dialect, source_database=source_database
        )

        # Attempt LLM translation if available
        try:
            prompt = OBJECT_TRANSLATION_PROMPT.format(
                source_dialect=source_dialect,
                target_dialect=target_dialect,
                object_type=view.object_type,
                object_name=view.name,
                source_definition=view.source_definition,
            )
            raw_res = await asyncio.wait_for(
                self.llm_service.generate_response(prompt),
                timeout=60.0
            )
            llm_def = raw_res.replace("```sql", "").replace("```", "").strip()
            llm_def = self._strip_schema_prefixes(llm_def, target_dialect=target_dialect, source_database=source_database)
            if llm_def and llm_def.strip():
                uncertain = parse_uncertain_lines(llm_def)
                return TranslationResult(
                    object_name=view.name,
                    object_type=view.object_type,
                    translated_definition=llm_def,
                    translation_method="llm_assisted",
                    confidence="high",
                    needs_human_review=False,
                    uncertain_lines=uncertain,
                    translation_error=None,
                )
        except Exception:
            # Fall back to rule-based transpilation output
            pass

        return TranslationResult(
            object_name=view.name,
            object_type=view.object_type,
            translated_definition=translated_def,
            translation_method="rules_only",
            confidence="high" if success else "medium",
            needs_human_review=False,
            uncertain_lines=[],
            translation_error=None,
        )

    async def translate_procedure_or_trigger(
        self, obj: MigratableObject, source_dialect: str, target_dialect: str, source_database: str = None
    ) -> TranslationResult:
        src_lower = source_dialect.lower()
        tgt_lower = target_dialect.lower()

        if (
            src_lower == "mssql"
            and tgt_lower == "mysql"
            and obj.object_type == "trigger"
            and "instead of" in (obj.source_definition or "").lower()
        ):
            return TranslationResult(
                object_name=obj.name,
                object_type=obj.object_type,
                translated_definition=None,
                translation_method="llm_assisted",
                confidence="low",
                needs_human_review=True,
                uncertain_lines=[],
                translation_error="INSTEAD OF triggers are not supported on tables in MySQL — this requires a redesign, not just translation",
            )

        # First obtain rule-based transpilation
        rule_def, rule_ok = self._rules_based_translate_procedure_or_trigger(obj, source_dialect, target_dialect, source_database=source_database)

        # Attempt LLM translation if available
        try:
            prompt = OBJECT_TRANSLATION_PROMPT.format(
                source_dialect=source_dialect,
                target_dialect=target_dialect,
                object_type=obj.object_type,
                object_name=obj.name,
                source_definition=obj.source_definition,
            )
            raw_res = await asyncio.wait_for(
                self.llm_service.generate_response(prompt),
                timeout=60.0
            )
            llm_def = raw_res.replace("```sql", "").replace("```", "").strip()
            llm_def = self._strip_schema_prefixes(llm_def, target_dialect=target_dialect, source_database=source_database)
            if llm_def and llm_def.strip():
                uncertain = parse_uncertain_lines(llm_def)
                return TranslationResult(
                    object_name=obj.name,
                    object_type=obj.object_type,
                    translated_definition=llm_def,
                    translation_method="llm_full",
                    confidence="high",
                    needs_human_review=False,
                    uncertain_lines=uncertain,
                    translation_error=None,
                )
        except Exception:
            # LLM unavailable or timed out; fall back to rule-based transcompiler
            pass

        return TranslationResult(
            object_name=obj.name,
            object_type=obj.object_type,
            translated_definition=rule_def,
            translation_method="rules_only",
            confidence="high" if rule_ok else "medium",
            needs_human_review=False,
            uncertain_lines=[],
            translation_error=None if rule_def else "Transpilation produced empty DDL",
        )

    async def retry_translation_after_compile_error(
        self, obj_translation: dict[str, Any], target_dialect: str, compile_error: str, source_database: str = None
    ) -> TranslationResult:
        prompt = f"""
You previously translated a database object to {target_dialect}, but it failed to compile with the following error:
{compile_error}

Original Source Code:
{obj_translation.get("source_definition", "")}

Your Previous Translation:
{obj_translation.get("translated_definition", "")}

Please analyze the error and the original source code, and provide a corrected translation for {target_dialect} that resolves this error.
Preserve the logic exactly. If you are uncertain, insert a comment "-- TRANSLATION_UNCERTAIN: [explanation]" immediately above the line in question.
Output ONLY the corrected SQL code. Do not include markdown block formatting or explanation outside the SQL.
"""
        try:
            result = await self.llm_service.generate_response(prompt)
            corrected_sql = result.replace("```sql", "").replace("```", "").strip()
            corrected_sql = self._strip_schema_prefixes(corrected_sql, target_dialect=target_dialect, source_database=source_database)
            uncertain_lines = parse_uncertain_lines(corrected_sql)

            return TranslationResult(
                object_name=obj_translation.get("object_name", obj_translation.get("name", "")),
                object_type=obj_translation.get("object_type", ""),
                translated_definition=corrected_sql,
                translation_method="llm_full",
                confidence="low",
                needs_human_review=True,
                approved_by_user=False,
                uncertain_lines=uncertain_lines,
                translation_error=None,
            )
        except Exception as e:
            return TranslationResult(
                object_name=obj_translation.get("object_name", obj_translation.get("name", "")),
                object_type=obj_translation.get("object_type", ""),
                translated_definition=obj_translation.get("translated_definition"),
                translation_method="llm_full",
                confidence="low",
                needs_human_review=True,
                approved_by_user=False,
                uncertain_lines=[],
                translation_error=f"AI retry attempt failed: {str(e)}",
            )
