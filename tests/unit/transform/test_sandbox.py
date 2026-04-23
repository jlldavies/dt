"""Tests for AST-based code sandbox with security validation."""

import polars as pl
import pytest

from dt.transform.sandbox import (
    SecurityError,
    execute_transform,
    extract_code_block,
    validate_code,
)


class TestExtractCodeBlock:
    def test_extracts_from_markdown_python_block(self):
        text = """Here is the code:

```python
def transform(df):
    return df
```

That's it."""
        assert extract_code_block(text) == "def transform(df):\n    return df"

    def test_returns_plain_code_as_is(self):
        code = "def transform(df):\n    return df"
        assert extract_code_block(code) == code

    def test_handles_multiple_blocks_takes_first(self):
        text = """```python
def transform(df):
    return df.head(1)
```

```python
def transform(df):
    return df.head(2)
```"""
        assert extract_code_block(text) == "def transform(df):\n    return df.head(1)"


class TestValidateCode:
    def test_allows_polars_operations(self):
        code = '''
import polars as pl

def transform(df):
    return df.filter(pl.col("a") > 1)
'''
        assert validate_code(code) is True

    def test_rejects_import_os(self):
        code = """
import os

def transform(df):
    return df
"""
        with pytest.raises(SecurityError, match="os"):
            validate_code(code)

    def test_rejects_import_subprocess(self):
        code = """
import subprocess

def transform(df):
    return df
"""
        with pytest.raises(SecurityError, match="subprocess"):
            validate_code(code)

    def test_rejects_open(self):
        code = """
def transform(df):
    f = open("secret.txt")
    return df
"""
        with pytest.raises(SecurityError, match="open"):
            validate_code(code)

    def test_rejects_exec(self):
        code = """
def transform(df):
    exec("import os")
    return df
"""
        with pytest.raises(SecurityError, match="exec"):
            validate_code(code)

    def test_rejects_eval(self):
        code = """
def transform(df):
    eval("1+1")
    return df
"""
        with pytest.raises(SecurityError, match="eval"):
            validate_code(code)

    def test_rejects_dunder_import(self):
        code = """
def transform(df):
    __import__("os")
    return df
"""
        with pytest.raises(SecurityError, match="__import__"):
            validate_code(code)

    def test_rejects_code_without_transform_function(self):
        code = """
def process(df):
    return df
"""
        with pytest.raises(ValueError, match="transform"):
            validate_code(code)


class TestExecuteTransform:
    def test_basic_filter_transform(self):
        code = """
def transform(df):
    import polars as pl
    return df.filter(pl.col("a") > 1)
"""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = execute_transform(code, df)
        expected = pl.DataFrame({"a": [2, 3], "b": [5, 6]})
        assert result.equals(expected)

    def test_returns_dataframe(self):
        code = """
def transform(df):
    return df
"""
        df = pl.DataFrame({"x": [1]})
        result = execute_transform(code, df)
        assert isinstance(result, pl.DataFrame)

    def test_rejects_unsafe_code(self):
        code = """
import os

def transform(df):
    return df
"""
        df = pl.DataFrame({"x": [1]})
        with pytest.raises(SecurityError):
            execute_transform(code, df)

    def test_bad_transform_returns_non_dataframe(self):
        code = """
def transform(df):
    return "not a dataframe"
"""
        df = pl.DataFrame({"x": [1]})
        with pytest.raises(TypeError, match="DataFrame"):
            execute_transform(code, df)
