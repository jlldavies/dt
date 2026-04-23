"""Tests for the TransformEngine orchestration layer."""

from __future__ import annotations

from unittest.mock import MagicMock

import polars as pl
import pytest

from dt.transform.engine import TransformEngine
from dt.transform.sandbox import SecurityError


SAFE_CODE = 'def transform(df):\n    return df.filter(pl.col("age") > 25)'


@pytest.fixture
def mock_backend():
    backend = MagicMock()
    backend.generate_code.return_value = SAFE_CODE
    return backend


@pytest.fixture
def engine(mock_backend):
    return TransformEngine(backend=mock_backend, use_cache=False)


@pytest.fixture
def sample_df():
    return pl.DataFrame({"name": ["Alice", "Bob", "Charlie"], "age": [30, 20, 35]})


class TestTransformCallsBackend:
    def test_transform_calls_backend_generate_code(self, engine, mock_backend, sample_df):
        engine.transform(sample_df, "filter age > 25")
        mock_backend.generate_code.assert_called_once()

    def test_transform_passes_instruction_in_prompt(self, engine, mock_backend, sample_df):
        engine.transform(sample_df, "filter age > 25")
        prompt_arg = mock_backend.generate_code.call_args[0][0]
        assert "filter age > 25" in prompt_arg

    def test_transform_passes_schema_in_prompt(self, engine, mock_backend, sample_df):
        engine.transform(sample_df, "filter age > 25")
        prompt_arg = mock_backend.generate_code.call_args[0][0]
        assert "name" in prompt_arg
        assert "age" in prompt_arg


class TestTransformReturnsDataFrame:
    def test_returns_dataframe(self, engine, sample_df):
        result = engine.transform(sample_df, "filter age > 25")
        assert isinstance(result, pl.DataFrame)

    def test_applies_filter_correctly(self, engine, sample_df):
        result = engine.transform(sample_df, "filter age > 25")
        assert result.shape[0] == 2
        assert "Bob" not in result["name"].to_list()
        assert "Alice" in result["name"].to_list()
        assert "Charlie" in result["name"].to_list()


class TestReturnCode:
    def test_return_code_true_returns_tuple(self, engine, sample_df):
        result = engine.transform(sample_df, "filter age > 25", return_code=True)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_return_code_true_contains_df_and_code(self, engine, sample_df):
        result_df, code = engine.transform(sample_df, "filter age > 25", return_code=True)
        assert isinstance(result_df, pl.DataFrame)
        assert isinstance(code, str)
        assert "transform" in code


class TestSecurityRejection:
    def test_rejects_unsafe_generated_code(self, sample_df):
        backend = MagicMock()
        backend.generate_code.return_value = "import os\ndef transform(df):\n    return df"
        engine = TransformEngine(backend=backend, use_cache=False)
        with pytest.raises(SecurityError):
            engine.transform(sample_df, "do something")


class TestCaching:
    def test_cache_hit_skips_backend_call(self, mock_backend, sample_df):
        cache = MagicMock()
        cache.get.return_value = SAFE_CODE
        engine = TransformEngine(backend=mock_backend, use_cache=True, cache_store=cache)

        engine.transform(sample_df, "filter age > 25")
        mock_backend.generate_code.assert_not_called()

    def test_cache_miss_calls_backend_and_stores(self, mock_backend, sample_df):
        cache = MagicMock()
        cache.get.return_value = None
        engine = TransformEngine(backend=mock_backend, use_cache=True, cache_store=cache)

        engine.transform(sample_df, "filter age > 25")
        mock_backend.generate_code.assert_called_once()
        cache.set.assert_called_once()
        # Verify the stored code is what the backend returned
        stored_code = cache.set.call_args[0][1]
        assert stored_code == SAFE_CODE
