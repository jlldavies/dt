"""AST-based code sandbox with security validation for LLM-generated transforms."""

from __future__ import annotations

import ast
import re

import polars as pl


class SecurityError(Exception):
    """Raised when generated code fails security validation."""


_BLOCKED_IMPORTS: frozenset[str] = frozenset({
    "os", "subprocess", "sys", "shutil", "pathlib",
    "socket", "http", "urllib", "requests", "importlib",
})

_BLOCKED_CALLS: frozenset[str] = frozenset({
    "open", "exec", "eval", "compile", "__import__",
    "globals", "locals", "getattr", "setattr", "delattr",
    "breakpoint", "exit", "quit",
})

_CODE_BLOCK_RE = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)


def extract_code_block(text: str) -> str:
    """Extract Python code from a markdown ```python block.

    If no markdown block is found, returns *text* as-is.
    If multiple blocks exist, returns the first one.
    """
    match = _CODE_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    return text


def validate_code(code: str) -> bool:
    """Validate that *code* is safe to execute.

    Raises:
        SecurityError: If the code contains blocked imports or calls.
        ValueError: If the code does not define a ``transform`` function.
    """
    tree = ast.parse(code)

    has_transform = False

    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _BLOCKED_IMPORTS:
                    raise SecurityError(
                        f"Blocked import: '{alias.name}'"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in _BLOCKED_IMPORTS:
                    raise SecurityError(
                        f"Blocked import: '{node.module}'"
                    )

        # Check function calls
        elif isinstance(node, ast.Call):
            func = node.func
            name: str | None = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name and name in _BLOCKED_CALLS:
                raise SecurityError(f"Blocked call: '{name}'")

        # Track transform function definition
        elif isinstance(node, ast.FunctionDef) and node.name == "transform":
            has_transform = True

    if not has_transform:
        raise ValueError(
            "Code must define a 'transform' function."
        )

    return True


def execute_transform(code: str, df: pl.DataFrame) -> pl.DataFrame:
    """Execute validated transform code against a DataFrame.

    1. Validates the code via :func:`validate_code`.
    2. Executes in a restricted namespace (only ``pl`` / ``polars``).
    3. Calls ``transform(df)`` and verifies the result type.
    """
    validate_code(code)

    namespace: dict = {"pl": pl, "polars": pl}
    exec(code, namespace)  # noqa: S102 – code already validated

    result = namespace["transform"](df)

    if not isinstance(result, pl.DataFrame):
        raise TypeError(
            f"transform() must return a polars DataFrame, got {type(result).__name__}"
        )

    return result
