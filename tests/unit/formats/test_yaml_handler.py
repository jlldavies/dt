"""Tests for YAML format handler."""

from __future__ import annotations

import polars as pl
import pytest
import yaml

from dt.formats.yaml_handler import YAMLHandler


@pytest.fixture
def handler() -> YAMLHandler:
    return YAMLHandler()


class TestYAMLRead:
    """Read YAML strings into DataFrames."""

    def test_list_of_dicts(self, handler: YAMLHandler) -> None:
        source = "- name: Alice\n  age: 30\n- name: Bob\n  age: 25\n"
        df = handler.read(source)
        assert df.shape == (2, 2)
        assert df["name"].to_list() == ["Alice", "Bob"]
        assert df["age"].to_list() == [30, 25]

    def test_with_document_start_marker(self, handler: YAMLHandler) -> None:
        source = "---\n- city: London\n  pop: 9000000\n- city: Paris\n  pop: 2100000\n"
        df = handler.read(source)
        assert df.shape == (2, 2)
        assert df["city"].to_list() == ["London", "Paris"]

    def test_single_dict_becomes_one_row(self, handler: YAMLHandler) -> None:
        source = "name: Alice\nage: 30\n"
        df = handler.read(source)
        assert df.shape == (1, 2)
        assert df["name"].to_list() == ["Alice"]

    def test_rejects_non_record_yaml(self, handler: YAMLHandler) -> None:
        source = "just a string"
        with pytest.raises(ValueError, match="Expected YAML list of records"):
            handler.read(source)


class TestYAMLWrite:
    """Write DataFrames to YAML strings."""

    def test_valid_yaml_output(self, handler: YAMLHandler) -> None:
        df = pl.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        result = handler.write(df)
        parsed = yaml.safe_load(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["name"] == "Alice"
        assert parsed[1]["age"] == 25

    def test_roundtrip(self, handler: YAMLHandler) -> None:
        df_original = pl.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})
        yaml_str = handler.write(df_original)
        df_roundtrip = handler.read(yaml_str)
        assert df_roundtrip.equals(df_original)
