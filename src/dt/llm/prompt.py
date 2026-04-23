"""LLM prompt construction for data-transformation code generation."""

from __future__ import annotations

import polars as pl

SYSTEM_PROMPT = """\
You are a data transformation assistant. You generate Python code \
using the Polars library to transform DataFrames.

Rules:
1. Write ONLY a Python function called `transform` that takes a single \
argument `df` (a polars.DataFrame) and returns a polars.DataFrame.
2. Use only the `polars` library (imported as `pl`). No other imports.
3. Do NOT use `print()`, `open()`, `exec()`, `eval()`, `import os`, \
`import subprocess`, or any I/O.
4. Return the transformed DataFrame as the variable `result`.
5. Wrap your code in ```python ... ``` markers.

Example output:
```python
def transform(df: pl.DataFrame) -> pl.DataFrame:
    result = df.filter(pl.col("age") > 30)
    return result
```"""


def format_schema(df: pl.DataFrame, sample_rows: int = 3) -> str:
    """Format DataFrame schema and sample rows for the LLM prompt.

    Parameters
    ----------
    df:
        The source DataFrame.
    sample_rows:
        Number of sample rows to include. Pass 0 to omit samples.

    Returns
    -------
    str
        A human-readable description of the schema (and optionally sample data).
    """
    columns = df.columns
    dtypes = df.dtypes

    lines: list[str] = ["Columns:"]
    for col, dtype in zip(columns, dtypes):
        lines.append(f"  - {col}: {dtype}")

    if sample_rows > 0:
        sample = df.head(sample_rows)
        lines.append("")
        lines.append(f"Sample data ({sample_rows} rows):")
        lines.append(str(sample))

    return "\n".join(lines)


def build_transform_prompt(
    df: pl.DataFrame,
    instruction: str,
    sample_rows: int = 3,
) -> str:
    """Build the full user prompt for the LLM.

    Combines the schema description with the user's natural-language
    instruction so the model can generate a Polars transformation.

    Parameters
    ----------
    df:
        The source DataFrame.
    instruction:
        The user's transformation request in plain English.
    sample_rows:
        Number of sample rows to include in the schema section.

    Returns
    -------
    str
        The assembled prompt string (does **not** include the system prompt).
    """
    schema = format_schema(df, sample_rows=sample_rows)
    return (
        f"Given the following Polars DataFrame:\n\n"
        f"{schema}\n\n"
        f"User request: {instruction}\n\n"
        f"Generate a `transform` function that uses Polars and stores "
        f"the final DataFrame in `result`."
    )
