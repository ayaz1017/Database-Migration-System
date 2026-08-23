"""
Transformation Layer for Universal Migration Engine.
"""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class TransformationContext:
    source_db: str
    target_db: str
    table_name: str
    column_name: str
    value: Any


class TransformationRule(ABC):
    @abstractmethod
    def apply(self, ctx: TransformationContext) -> Any:
        pass

    @abstractmethod
    def describe(self) -> str:
        pass


class ColumnRenameRule(TransformationRule):
    def __init__(self, old_name: str, new_name: str):
        self.old_name = old_name
        self.new_name = new_name

    def apply(self, ctx: TransformationContext) -> Any:
        # Renaming typically handled at DDL and mapping layer,
        # but if applied to value context, it passes value through
        return ctx.value

    def describe(self) -> str:
        return f"Rename column '{self.old_name}' to '{self.new_name}'"


class DatatypeOverrideRule(TransformationRule):
    def __init__(self, column: str, target_type: str):
        self.column = column
        self.target_type = target_type

    def apply(self, ctx: TransformationContext) -> Any:
        # Datatype casting usually handled at DB layer, but logic could be added here
        return ctx.value

    def describe(self) -> str:
        return f"Override datatype for column '{self.column}' to '{self.target_type}'"


class DataMaskingRule(TransformationRule):
    def __init__(self, column: str, strategy: str):
        self.column = column
        if strategy not in ["nullify", "hash", "redact"]:
            raise ValueError(f"Unknown masking strategy: {strategy}")
        self.strategy = strategy

    def apply(self, ctx: TransformationContext) -> Any:
        if ctx.column_name != self.column or ctx.value is None:
            return ctx.value

        if self.strategy == "nullify":
            return None
        elif self.strategy == "hash":
            return hashlib.sha256(str(ctx.value).encode()).hexdigest()
        elif self.strategy == "redact":
            return "REDACTED"

        return ctx.value

    def describe(self) -> str:
        return f"Mask column '{self.column}' using strategy '{self.strategy}'"


class CustomSQLExpressionRule(TransformationRule):
    def __init__(self, column: str, expression: str):
        self.column = column
        self.expression = expression

    def apply(self, ctx: TransformationContext) -> Any:
        if ctx.column_name != self.column or ctx.value is None:
            return ctx.value

        # Simplistic local evaluation for illustration
        # E.g., if expression is "UPPER({value})"
        if "UPPER(" in self.expression.upper():
            return str(ctx.value).upper()

        return ctx.value

    def describe(self) -> str:
        return f"Apply custom SQL expression '{self.expression}' on column '{self.column}'"
