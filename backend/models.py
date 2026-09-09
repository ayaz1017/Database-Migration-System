from typing import Any, Literal

from pydantic import BaseModel, field_validator


class FKEdge(BaseModel):
    from_table: str
    to_table: str
    fk_column: str = ""
    is_self_referencing: bool = False


class DependencyResolution(BaseModel):
    final_table_set: list[str]
    originally_selected: list[str]
    auto_added: list[str]
    auto_added_reasons: dict[str, list[str]]
    self_referencing_tables: list[str]
    circular_dependency_groups: list[list[str]]
    blocked: bool
    missing_dependencies: list[str]
    dropped_constraints: list[FKEdge]
    migration_order: list[str]
    migration_generations: list[list[str]] = []


class TableGroupResult(BaseModel):
    success: bool
    group_name: str
    error_step: str | None = None
    error_message: str | None = None
    rolled_back: bool = False
    violations: list[dict] = []


class MigratableObject(BaseModel):
    object_type: Literal["view", "procedure", "function", "trigger", "trigger_function"]
    name: str
    schema_name: str | None = None
    source_definition: str = ""  # raw original SQL/PLSQL text
    depends_on_tables: list[str] = []  # parsed/best-effort table references
    depends_on_objects: list[str] = []  # other procs/views it calls, if detectable
    complexity_estimate: Literal["low", "medium", "high"] = "medium"
    # Trigger-specific metadata (populated from information_schema)
    trigger_table: str | None = None
    trigger_timing: str | None = None  # BEFORE or AFTER
    trigger_event: str | None = None   # INSERT, UPDATE, DELETE, or combinations

    @field_validator("object_type", mode="before")
    @classmethod
    def normalize_object_type(cls, v: str) -> str:
        if v == "trigger_function":
            return "function"
        return v


class ObjectMigrationResult(BaseModel):
    name: str
    object_type: str
    status: Literal["applied", "apply_failed", "translation_failed", "applied_with_warnings"]
    translated_definition: str | None = None
    error_detail: str | None = None
    uncertain_lines: list[dict[str, Any]] = []
    duration_ms: int = 0


class TranslationResult(BaseModel):
    object_name: str = ""
    object_type: str = ""
    translated_definition: str | None = None
    translation_method: Literal["rules_only", "llm_assisted", "llm_full"] = "llm_full"
    confidence: Literal["high", "medium", "low"] = "medium"
    needs_human_review: bool = True
    approved_by_user: bool = False
    compile_status: str | None = None
    uncertain_lines: list[dict[str, Any]] = []
    translation_error: str | None = None


from pydantic import field_validator
import re

ORACLE_SYSTEM_PREFIXES = (
    'AQ$', 'LOGMNR$', 'LOGSTDBY$',
    'MVIEW$', 'REPL_', 'GG_', 'BIN$',
    'DR$', 'SYS_'
)

class MigrationOptions(BaseModel):
    selected_tables: list[str] = []
    migrate_all_tables: bool = True
    fk_dependency_mode: Literal["auto_include", "strict", "drop_constraint"] = "auto_include"

    migrate_views: bool = True
    migrate_procedures: bool = True
    migrate_triggers: bool = True
    selected_views: list[str] = []
    selected_procedures: list[str] = []
    selected_triggers: list[str] = []
    auto_approve_objects: bool = True

    @field_validator('selected_tables', 'selected_views', 'selected_procedures', 'selected_triggers', mode='before')
    @classmethod
    def validate_identifiers(cls, v: list[str] | None) -> list[str]:
        if v is None:
            return []
        for name in v:
            # SQL identifier validation
            if not re.match(r'^[a-zA-Z0-9_#][a-zA-Z0-9_$#.]*$', name):
                raise ValueError(f"Invalid SQL identifier: {name}")
                
            # System object validation
            upper = name.upper()
            for prefix in ORACLE_SYSTEM_PREFIXES:
                if upper.startswith(prefix) or '$' in upper:
                    raise ValueError(
                        f"'{name}' appears to be an Oracle system object and cannot be migrated. "
                        f"Deselect system objects in the Object Picker."
                    )
        return v

    migrate_data: bool = True
    apply_masking: bool = False
    cdc_mode: bool = False
    chunk_size: int = 5000
    validate_after: bool = True
    auto_fix: bool = True

from typing import Optional

class DriftChange(BaseModel):
    change_type: Literal[
        "table_added", "table_removed",
        "column_added", "column_removed", 
        "column_type_changed",
        "column_nullable_changed",
        "column_default_changed",
        "index_added", "index_removed",
        "index_changed",
        "constraint_added", "constraint_removed"
    ]
    table_name: str
    object_name: str    # column/index/constraint name
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    severity: Literal["low", "medium", "high"]
    description: str

class DriftResult(BaseModel):
    drift_detected: bool
    overall_severity: Literal["none", "low", "medium", "high"]
    changes: list[DriftChange]
    tables_added: list[str]
    tables_removed: list[str]
    schema_version_changed: bool
    summary: str

class DriftCheckRequest(BaseModel):
    source_password: str
