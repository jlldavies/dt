"""Tests for the XML format handler."""

from __future__ import annotations

import pytest
import polars as pl
from lxml import etree

from dt.formats.xml_handler import XMLHandler


@pytest.fixture
def handler() -> XMLHandler:
    return XMLHandler()


@pytest.fixture
def sample_xml_content() -> str:
    return (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<data>\n"
        "  <row>\n"
        "    <name>Alice</name>\n"
        "    <age>30</age>\n"
        "    <city>London</city>\n"
        "  </row>\n"
        "  <row>\n"
        "    <name>Bob</name>\n"
        "    <age>25</age>\n"
        "    <city>Paris</city>\n"
        "  </row>\n"
        "</data>\n"
    )


class TestXMLRead:
    """Test reading XML content into a DataFrame."""

    def test_read_basic_xml(
        self, handler: XMLHandler, sample_xml_content: str
    ) -> None:
        df = handler.read(sample_xml_content)
        assert df.shape == (2, 3)
        assert df.columns == ["name", "age", "city"]
        assert df["name"].to_list() == ["Alice", "Bob"]
        assert df["age"].to_list() == ["30", "25"]
        assert df["city"].to_list() == ["London", "Paris"]

    def test_read_simple_inline_xml(self, handler: XMLHandler) -> None:
        xml = "<data><row><x>1</x><y>2</y></row></data>"
        df = handler.read(xml)
        assert df.shape == (1, 2)
        assert df["x"].to_list() == ["1"]
        assert df["y"].to_list() == ["2"]

    def test_read_empty_root(self, handler: XMLHandler) -> None:
        xml = "<data></data>"
        df = handler.read(xml)
        assert df.shape == (0, 0)

    def test_read_single_row(self, handler: XMLHandler) -> None:
        xml = "<data><row><id>42</id></row></data>"
        df = handler.read(xml)
        assert df.shape == (1, 1)
        assert df["id"].to_list() == ["42"]


class TestXMLWrite:
    """Test writing a DataFrame to XML."""

    def test_write_produces_valid_xml(self, handler: XMLHandler) -> None:
        df = pl.DataFrame({"name": ["Alice"], "age": [30]})
        output = handler.write(df)
        # Should parse without error
        root = etree.fromstring(output.encode("utf-8"))
        assert root.tag == "data"
        rows = list(root)
        assert len(rows) == 1
        assert rows[0].tag == "row"
        fields = {child.tag: child.text for child in rows[0]}
        assert fields["name"] == "Alice"
        assert fields["age"] == "30"

    def test_write_includes_xml_declaration(self, handler: XMLHandler) -> None:
        df = pl.DataFrame({"a": [1]})
        output = handler.write(df)
        assert output.startswith("<?xml")

    def test_write_none_values(self, handler: XMLHandler) -> None:
        df = pl.DataFrame({"a": ["x", None]})
        output = handler.write(df)
        # Roundtrip through handler.read to verify None becomes ""
        df_back = handler.read(output)
        assert df_back["a"].to_list() == ["x", ""]

    def test_roundtrip(self, handler: XMLHandler) -> None:
        df = pl.DataFrame({"name": ["Alice", "Bob"], "score": ["95", "87"]})
        xml_out = handler.write(df)
        df_back = handler.read(xml_out)
        assert df_back.shape == df.shape
        assert df_back.columns == df.columns
        assert df_back["name"].to_list() == df["name"].to_list()
        assert df_back["score"].to_list() == df["score"].to_list()

    def test_write_empty_dataframe(self, handler: XMLHandler) -> None:
        df = pl.DataFrame()
        output = handler.write(df)
        root = etree.fromstring(output.encode("utf-8"))
        assert root.tag == "data"
        assert len(list(root)) == 0
