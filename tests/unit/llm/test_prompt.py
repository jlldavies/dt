"""Tests for LLM prompt builder."""

from __future__ import annotations

import polars as pl
import pytest

from dt.llm.prompt import SYSTEM_PROMPT, build_transform_prompt, format_schema


@pytest.fixture()
def sample_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "Diana"],
            "age": [30, 25, 35, 28],
            "score": [9.5, 8.0, 7.5, 9.0],
        }
    )


class TestFormatSchema:
    """Tests for format_schema helper."""

    def test_includes_column_names(self, sample_df: pl.DataFrame) -> None:
        result = format_schema(sample_df)
        assert "name" in result
        assert "age" in result
        assert "score" in result

    def test_includes_column_types(self, sample_df: pl.DataFrame) -> None:
        result = format_schema(sample_df)
        assert "Utf8" in result or "String" in result
        assert "Int64" in result or "i64" in result
        assert "Float64" in result or "f64" in result

    def test_includes_sample_rows(self, sample_df: pl.DataFrame) -> None:
        result = format_schema(sample_df, sample_rows=2)
        # Should contain at least some data values
        assert "Alice" in result
        assert "Bob" in result

    def test_no_sample_rows(self, sample_df: pl.DataFrame) -> None:
        result = format_schema(sample_df, sample_rows=0)
        # Should still include schema info
        assert "name" in result
        # Should NOT include sample data values
        assert "Alice" not in result


class TestBuildTransformPrompt:
    """Tests for build_transform_prompt."""

    def test_contains_user_instruction(self, sample_df: pl.DataFrame) -> None:
        prompt = build_transform_prompt(sample_df, "filter rows where age > 30")
        assert "filter rows where age > 30" in prompt

    def test_contains_schema(self, sample_df: pl.DataFrame) -> None:
        prompt = build_transform_prompt(sample_df, "do something")
        assert "name" in prompt
        assert "age" in prompt
        assert "score" in prompt

    def test_requests_polars_code(self, sample_df: pl.DataFrame) -> None:
        prompt = build_transform_prompt(sample_df, "do something")
        assert "polars" in prompt.lower() or "Polars" in prompt

    def test_mentions_result(self, sample_df: pl.DataFrame) -> None:
        prompt = build_transform_prompt(sample_df, "do something")
        assert "result" in prompt
