"""Tests for Excel format handler."""

from __future__ import annotations

import io

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from dt.formats.excel_handler import ExcelHandler


@pytest.fixture()
def sample_excel_bytes() -> bytes:
    """Create sample Excel bytes using Polars write_excel."""
    df = pl.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
    buf = io.BytesIO()
    df.write_excel(buf)
    return buf.getvalue()


class TestExcelRead:
    """Reading Excel bytes into DataFrames."""

    def test_read_from_bytes(self, sample_excel_bytes: bytes) -> None:
        handler = ExcelHandler()
        df = handler.read(sample_excel_bytes)
        assert df.shape == (2, 2)
        assert df.columns == ["name", "age"]

    def test_preserves_values(self, sample_excel_bytes: bytes) -> None:
        handler = ExcelHandler()
        df = handler.read(sample_excel_bytes)
        assert df["name"].to_list() == ["Alice", "Bob"]
        assert df["age"].to_list() == [30, 25]


class TestExcelWrite:
    """Writing DataFrames to Excel bytes."""

    def test_produces_bytes(self) -> None:
        handler = ExcelHandler()
        df = pl.DataFrame({"x": [1, 2], "y": [3, 4]})
        result = handler.write(df)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_roundtrip(self) -> None:
        handler = ExcelHandler()
        df = pl.DataFrame({"x": [10, 20], "y": ["foo", "bar"]})
        excel_bytes = handler.write(df)
        restored = handler.read(excel_bytes)
        assert_frame_equal(df, restored)
