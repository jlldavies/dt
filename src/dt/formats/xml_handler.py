"""XML format handler for reading and writing DataFrames."""

from __future__ import annotations

from lxml import etree
import polars as pl

from dt.formats.registry import register


@register("xml")
class XMLHandler:
    """Reads/writes tabular data as XML with <data>/<row>/<field> structure."""

    def read(self, source: str) -> pl.DataFrame:
        root = etree.fromstring(source.encode("utf-8"))
        rows = []
        for row_elem in root:
            row = {}
            for field in row_elem:
                row[field.tag] = field.text if field.text is not None else ""
            rows.append(row)
        if not rows:
            return pl.DataFrame()
        return pl.DataFrame(rows)

    def write(self, df: pl.DataFrame) -> str:
        root = etree.Element("data")
        for row_dict in df.to_dicts():
            row_elem = etree.SubElement(root, "row")
            for key, value in row_dict.items():
                field = etree.SubElement(row_elem, str(key))
                field.text = str(value) if value is not None else ""
        return etree.tostring(
            root, pretty_print=True, xml_declaration=True, encoding="UTF-8"
        ).decode("utf-8")
