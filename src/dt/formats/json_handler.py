"""JSON and JSONL format handlers."""

from __future__ import annotations

import io
import json

import polars as pl

from dt.formats.registry import register


@register("json")
class JSONHandler:
    """Handler for JSON format (array of objects or single object)."""

    def read(self, source: str) -> pl.DataFrame:
        data = json.loads(source)
        if isinstance(data, dict):
            data = [data]
        return pl.DataFrame(data)

    def write(self, df: pl.DataFrame) -> str:
        return json.dumps(df.to_dicts(), indent=2, default=str)


@register("jsonl")
class JSONLHandler:
    """Handler for newline-delimited JSON (JSONL/NDJSON) format."""

    def read(self, source: str) -> pl.DataFrame:
        return pl.read_ndjson(io.StringIO(source))

    def write(self, df: pl.DataFrame) -> str:
        buf = io.BytesIO()
        df.write_ndjson(buf)
        return buf.getvalue().decode("utf-8")
