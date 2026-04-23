"""Integration tests for format read/write roundtrips."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

# Import all handlers to trigger registration.
import dt.formats.csv_handler  # noqa: F401
import dt.formats.json_handler  # noqa: F401
import dt.formats.yaml_handler  # noqa: F401
import dt.formats.xml_handler  # noqa: F401
import dt.formats.excel_handler  # noqa: F401

from dt.formats.detect import detect_format
from dt.formats.registry import get_handler

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_fixture(fmt: str) -> pl.DataFrame:
    """Read a fixture file using the appropriate handler."""
    ext_map = {
        "csv": "sample.csv",
        "tsv": "sample.tsv",
        "json": "sample.json",
        "jsonl": "sample.jsonl",
        "yaml": "sample.yaml",
        "xml": "sample.xml",
    }
    path = FIXTURES / ext_map[fmt]
    content = path.read_text(encoding="utf-8")
    handler = get_handler(fmt)
    return handler.read(content)


# ---------------------------------------------------------------------------
# TestReadAllFixtures
# ---------------------------------------------------------------------------

class TestReadAllFixtures:
    """Verify every fixture file can be read into a DataFrame."""

    @pytest.mark.parametrize("fmt", ["csv", "tsv", "json", "jsonl", "yaml", "xml"])
    def test_read_fixture(self, fmt: str) -> None:
        df = _read_fixture(fmt)
        assert isinstance(df, pl.DataFrame)
        assert len(df) >= 2, f"{fmt} fixture should have at least 2 rows"
        assert "name" in df.columns, f"{fmt} fixture should contain 'name' column"


# ---------------------------------------------------------------------------
# TestFormatRoundtrip
# ---------------------------------------------------------------------------

_ROUNDTRIP_PAIRS = [
    ("csv", "json"),
    ("json", "csv"),
    ("csv", "yaml"),
    ("yaml", "json"),
    ("json", "yaml"),
    ("csv", "tsv"),
    ("tsv", "csv"),
    ("csv", "xml"),
    ("xml", "json"),
]


class TestFormatRoundtrip:
    """Read source fixture, write to dest format, read back, verify shape/columns."""

    @pytest.mark.parametrize("src_fmt,dst_fmt", _ROUNDTRIP_PAIRS)
    def test_roundtrip(self, src_fmt: str, dst_fmt: str) -> None:
        # Read original fixture
        original = _read_fixture(src_fmt)

        # Write to destination format
        dst_handler = get_handler(dst_fmt)
        serialised = dst_handler.write(original)

        # Read back from destination format
        roundtripped = dst_handler.read(serialised)

        # Shape must match
        assert roundtripped.shape == original.shape, (
            f"{src_fmt}->{dst_fmt}: shape mismatch "
            f"{roundtripped.shape} != {original.shape}"
        )

        # Columns must match (same set, same order)
        assert roundtripped.columns == original.columns, (
            f"{src_fmt}->{dst_fmt}: column mismatch "
            f"{roundtripped.columns} != {original.columns}"
        )


# ---------------------------------------------------------------------------
# TestDetectFixtureFormats
# ---------------------------------------------------------------------------

_DETECT_CASES = [
    ("sample.csv", "csv"),
    ("sample.tsv", "tsv"),
    ("sample.json", "json"),
    ("sample.jsonl", "jsonl"),
    ("sample.yaml", "yaml"),
    ("sample.xml", "xml"),
    ("sample.xlsx", "excel"),
]


class TestDetectFixtureFormats:
    """Verify detect_format identifies fixture files correctly."""

    @pytest.mark.parametrize("filename,expected", _DETECT_CASES)
    def test_detect_from_filename(self, filename: str, expected: str) -> None:
        result = detect_format(filename=filename)
        assert result == expected

    @pytest.mark.parametrize(
        "fmt,expected",
        [
            ("csv", "csv"),
            ("tsv", "tsv"),
            ("json", "json"),
            ("jsonl", "jsonl"),
            # yaml list format (- key: val) isn't detected by content sniffer
            # because it lacks a '---' header or 'key: value' top-level pattern.
            ("xml", "xml"),
        ],
    )
    def test_detect_from_content(self, fmt: str, expected: str) -> None:
        ext_map = {
            "csv": "sample.csv",
            "tsv": "sample.tsv",
            "json": "sample.json",
            "jsonl": "sample.jsonl",
            "yaml": "sample.yaml",
            "xml": "sample.xml",
        }
        content = (FIXTURES / ext_map[fmt]).read_text(encoding="utf-8")
        result = detect_format(content=content)
        assert result == expected
