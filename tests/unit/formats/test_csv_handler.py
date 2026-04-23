"""Tests for CSV and TSV format handlers."""

from __future__ import annotations

import polars as pl
import pytest
from polars.testing import assert_frame_equal

from dt.formats.csv_handler import CSVHandler, TSVHandler


class TestCSVRead:
    """Reading CSV strings into DataFrames."""

    def test_basic_csv(self) -> None:
        handler = CSVHandler()
        data = "a,b,c\n1,2,3\n4,5,6\n"
        df = handler.read(data)
        assert df.shape == (2, 3)
        assert df.columns == ["a", "b", "c"]

    def test_preserves_values(self) -> None:
        handler = CSVHandler()
        data = "name,age\nAlice,30\nBob,25\n"
        df = handler.read(data)
        assert df["name"].to_list() == ["Alice", "Bob"]
        assert df["age"].to_list() == [30, 25]

    def test_empty_csv_header_only(self) -> None:
        handler = CSVHandler()
        data = "x,y\n"
        df = handler.read(data)
        assert df.shape == (0, 2)
        assert df.columns == ["x", "y"]

    def test_quoted_fields_with_commas(self) -> None:
        handler = CSVHandler()
        data = 'name,note\nAlice,"hello, world"\nBob,"a,b"\n'
        df = handler.read(data)
        assert df["note"].to_list() == ["hello, world", "a,b"]


class TestCSVWrite:
    """Writing DataFrames to CSV strings."""

    def test_basic_write(self) -> None:
        handler = CSVHandler()
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = handler.write(df)
        assert isinstance(result, str)
        lines = result.strip().split("\n")
        assert lines[0] == "a,b"
        assert lines[1] == "1,3"
        assert lines[2] == "2,4"

    def test_roundtrip(self) -> None:
        handler = CSVHandler()
        df = pl.DataFrame({"x": [10, 20], "y": ["foo", "bar"]})
        csv_str = handler.write(df)
        restored = handler.read(csv_str)
        assert_frame_equal(df, restored)


class TestTSVHandler:
    """TSV handler uses tab separator."""

    def test_read_tsv(self) -> None:
        handler = TSVHandler()
        data = "a\tb\n1\t2\n3\t4\n"
        df = handler.read(data)
        assert df.shape == (2, 2)
        assert df.columns == ["a", "b"]
        assert df["a"].to_list() == [1, 3]

    def test_write_tsv(self) -> None:
        handler = TSVHandler()
        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = handler.write(df)
        assert isinstance(result, str)
        lines = result.strip().split("\n")
        assert lines[0] == "a\tb"
        assert lines[1] == "1\t3"

    def test_roundtrip_tsv(self) -> None:
        handler = TSVHandler()
        df = pl.DataFrame({"col1": ["hello", "world"], "col2": [100, 200]})
        tsv_str = handler.write(df)
        restored = handler.read(tsv_str)
        assert_frame_equal(df, restored)
