"""CSV and TSV format handlers."""

from __future__ import annotations

import io

import polars as pl

from dt.formats.registry import register


@register("csv")
class CSVHandler:
    """Read/write CSV (comma-separated) data."""

    def read(self, source: str) -> pl.DataFrame:
        return pl.read_csv(io.StringIO(source))

    def write(self, df: pl.DataFrame) -> str:
        buf = io.BytesIO()
        df.write_csv(buf)
        return buf.getvalue().decode("utf-8")


@register("tsv")
class TSVHandler:
    """Read/write TSV (tab-separated) data."""

    def read(self, source: str) -> pl.DataFrame:
        return pl.read_csv(io.StringIO(source), separator="\t")

    def write(self, df: pl.DataFrame) -> str:
        buf = io.BytesIO()
        df.write_csv(buf, separator="\t")
        return buf.getvalue().decode("utf-8")
