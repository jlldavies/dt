"""Tests for format auto-detection from filename and content."""

from __future__ import annotations

import pytest

from dt.formats.detect import detect_format


class TestDetectFromExtension:
    """Detect format from file extension."""

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("data.csv", "csv"),
            ("data.CSV", "csv"),
            ("data.tsv", "tsv"),
            ("data.json", "json"),
            ("data.jsonl", "jsonl"),
            ("data.yaml", "yaml"),
            ("data.yml", "yaml"),
            ("data.xml", "xml"),
            ("data.xlsx", "excel"),
            ("data.xls", "excel"),
        ],
    )
    def test_known_extensions(self, filename: str, expected: str) -> None:
        assert detect_format(filename=filename) == expected

    def test_unknown_extension_returns_none(self) -> None:
        assert detect_format(filename="data.parquet") is None

    def test_no_extension_returns_none(self) -> None:
        assert detect_format(filename="Makefile") is None

    def test_path_with_directories(self) -> None:
        assert detect_format(filename="/some/path/to/data.csv") == "csv"


class TestDetectFromContent:
    """Detect format by sniffing content."""

    def test_json_object(self) -> None:
        assert detect_format(content='{"key": "value"}') == "json"

    def test_json_array(self) -> None:
        assert detect_format(content='[{"a": 1}, {"a": 2}]') == "json"

    def test_json_with_leading_whitespace(self) -> None:
        assert detect_format(content='  {"key": "value"}') == "json"

    def test_xml_with_declaration(self) -> None:
        content = '<?xml version="1.0"?><root><item>1</item></root>'
        assert detect_format(content=content) == "xml"

    def test_xml_without_declaration(self) -> None:
        content = "<root><item>1</item></root>"
        assert detect_format(content=content) == "xml"

    def test_yaml_with_document_start(self) -> None:
        content = "---\nname: Alice\nage: 30\n"
        assert detect_format(content=content) == "yaml"

    def test_yaml_without_document_start(self) -> None:
        content = "name: Alice\nage: 30\ncity: London\n"
        assert detect_format(content=content) == "yaml"

    def test_csv_content(self) -> None:
        content = "name,age,city\nAlice,30,London\nBob,25,Paris\n"
        assert detect_format(content=content) == "csv"

    def test_tsv_content(self) -> None:
        content = "name\tage\tcity\nAlice\t30\tLondon\nBob\t25\tParis\n"
        assert detect_format(content=content) == "tsv"

    def test_jsonl_content(self) -> None:
        content = '{"name": "Alice"}\n{"name": "Bob"}\n{"name": "Charlie"}\n'
        assert detect_format(content=content) == "jsonl"

    def test_empty_content_returns_none(self) -> None:
        assert detect_format(content="") is None

    def test_whitespace_only_returns_none(self) -> None:
        assert detect_format(content="   \n  \n  ") is None

    def test_no_args_returns_none(self) -> None:
        assert detect_format() is None

    def test_filename_takes_precedence_over_content(self) -> None:
        # Content looks like JSON, but filename says CSV
        assert detect_format(filename="data.csv", content='{"key": "val"}') == "csv"
