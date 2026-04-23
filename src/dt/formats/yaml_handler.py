"""YAML format handler for reading/writing DataFrames."""

from __future__ import annotations

import polars as pl
import yaml

from dt.formats.registry import register


@register("yaml")
class YAMLHandler:
    """Read and write YAML lists of records."""

    def read(self, source: str) -> pl.DataFrame:
        data = yaml.safe_load(source)
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise ValueError(f"Expected YAML list of records, got {type(data).__name__}")
        return pl.DataFrame(data)

    def write(self, df: pl.DataFrame) -> str:
        return yaml.dump(df.to_dicts(), default_flow_style=False, sort_keys=False)
