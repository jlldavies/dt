"""Auto-detect data format from filename extension or content sniffing."""

from __future__ import annotations

import csv
import io
import os
import re

_EXTENSION_MAP: dict[str, str] = {
    ".csv": "csv",
    ".tsv": "tsv",
    ".json": "json",
    ".jsonl": "jsonl",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".xlsx": "xlsx",
    ".xls": "xls",
}


def detect_format(
    *,
    filename: str | None = None,
    content: str | None = None,
) -> str | None:
    """Detect data format from filename extension or content sniffing.

    If both filename and content are provided, filename takes precedence
    when the extension is recognised. Returns None if the format cannot
    be determined.
    """
    if filename is not None:
        fmt = _detect_from_extension(filename)
        if fmt is not None:
            return fmt

    if content is not None:
        return _detect_from_content(content)

    return None


def _detect_from_extension(filename: str) -> str | None:
    _, ext = os.path.splitext(filename)
    return _EXTENSION_MAP.get(ext.lower())


def _detect_from_content(content: str) -> str | None:
    stripped = content.strip()
    if not stripped:
        return None

    lines = [l for l in stripped.splitlines() if l.strip()]

    # JSONL: multiple lines each starting with { (check before JSON)
    if len(lines) >= 2 and all(l.strip().startswith("{") for l in lines):
        return "jsonl"

    # JSON object or array
    if stripped.startswith(("{", "[")):
        return "json"

    # XML
    if stripped.startswith("<?xml") or re.match(r"<[a-zA-Z]", stripped):
        return "xml"

    # YAML with document start marker
    if stripped.startswith("---"):
        return "yaml"

    # TSV: tabs in first line
    first_line = lines[0] if lines else ""
    if "\t" in first_line:
        return "tsv"

    # CSV: try csv.Sniffer
    try:
        dialect = csv.Sniffer().sniff(stripped)
        if dialect.delimiter == ",":
            return "csv"
    except csv.Error:
        pass

    # YAML without document start: key: value patterns
    yaml_pattern = re.compile(r"^[a-zA-Z_]\w*\s*:.*$")
    if len(lines) >= 2 and all(yaml_pattern.match(l.strip()) for l in lines):
        return "yaml"

    return None
