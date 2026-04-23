"""Tests for JSON and JSONL format handlers."""

from __future__ import annotations

import json

import polars as pl
import pytest

from dt.formats.json_handler import JSONHandler, JSONLHandler


# ---------------------------------------------------------------------------
# JSON – read
# ---------------------------------------------------------------------------

class TestJSONRead:
    def setup_method(self):
        self.handler = JSONHandler()

    def test_read_array_of_objects(self):
        src = json.dumps([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
        df = self.handler.read(src)
        assert df.shape == (2, 2)
        assert df["a"].to_list() == [1, 3]
        assert df["b"].to_list() == [2, 4]

    def test_read_single_object(self):
        src = json.dumps({"x": "hello", "y": 42})
        df = self.handler.read(src)
        assert df.shape == (1, 2)
        assert df["x"].to_list() == ["hello"]
        assert df["y"].to_list() == [42]

    def test_read_nested_json(self):
        src = json.dumps([{"a": 1, "nested": {"k": "v"}}])
        df = self.handler.read(src)
        assert df.shape == (1, 2)
        assert df["a"].to_list() == [1]
        # nested value preserved as a struct or dict-like column
        nested_val = df["nested"].to_list()[0]
        assert nested_val == {"k": "v"}


# ---------------------------------------------------------------------------
# JSON – write
# ---------------------------------------------------------------------------

class TestJSONWrite:
    def setup_method(self):
        self.handler = JSONHandler()

    def test_write_produces_valid_json(self):
        df = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        result = self.handler.write(df)
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0] == {"a": 1, "b": "x"}

    def test_roundtrip(self):
        original = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        df = self.handler.read(json.dumps(original))
        output = self.handler.write(df)
        assert json.loads(output) == original


# ---------------------------------------------------------------------------
# JSONL – read
# ---------------------------------------------------------------------------

class TestJSONLRead:
    def setup_method(self):
        self.handler = JSONLHandler()

    def test_read_jsonl_lines(self):
        lines = '{"a":1,"b":2}\n{"a":3,"b":4}\n'
        df = self.handler.read(lines)
        assert df.shape == (2, 2)
        assert df["a"].to_list() == [1, 3]
        assert df["b"].to_list() == [2, 4]


# ---------------------------------------------------------------------------
# JSONL – write
# ---------------------------------------------------------------------------

class TestJSONLWrite:
    def setup_method(self):
        self.handler = JSONLHandler()

    def test_write_jsonl(self):
        df = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        result = self.handler.write(df)
        lines = [l for l in result.strip().split("\n") if l]
        assert len(lines) == 2

    def test_write_produces_valid_lines(self):
        df = pl.DataFrame({"a": [10, 20], "b": ["foo", "bar"]})
        result = self.handler.write(df)
        for line in result.strip().split("\n"):
            parsed = json.loads(line)
            assert "a" in parsed
            assert "b" in parsed
