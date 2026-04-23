"""Excel format handler."""

from __future__ import annotations

import io

import polars as pl

from dt.formats.registry import register


@register("excel")
class ExcelHandler:
    """Read and write Excel (.xlsx) files."""

    def read(self, source: str | bytes) -> pl.DataFrame:
        if isinstance(source, str):
            source = source.encode("latin-1")
        return pl.read_excel(io.BytesIO(source))

    def write(self, df: pl.DataFrame) -> bytes:
        buf = io.BytesIO()
        df.write_excel(buf)
        return buf.getvalue()
