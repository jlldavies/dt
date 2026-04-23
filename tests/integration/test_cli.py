"""Integration tests for the dt CLI."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import polars as pl
import pytest
from click.testing import CliRunner

from dt.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_engine(return_df: pl.DataFrame | None = None, code_str: str = "# code"):
    """Create a mock TransformEngine that returns a fixed DataFrame."""
    if return_df is None:
        return_df = pl.DataFrame({"result": [1, 2, 3]})

    engine = MagicMock()

    def transform_side_effect(df, instruction, return_code=False):
        if return_code:
            return return_df, code_str
        return return_df

    engine.transform = MagicMock(side_effect=transform_side_effect)
    engine.sample_rows = 3
    return engine


def _make_mock_alias_store(aliases: dict[str, str] | None = None):
    """Create a mock AliasStore."""
    store = MagicMock()
    data = dict(aliases) if aliases else {}
    store.get = MagicMock(side_effect=lambda name: data.get(name))
    store.list_all = MagicMock(return_value=data)
    store.save = MagicMock()
    store.delete = MagicMock()
    return store


def _make_mock_cache(entries: int = 5, size_bytes: int = 1024):
    """Create a mock CodeCache."""
    cache = MagicMock()
    cache.stats = MagicMock(return_value={"entries": entries, "size_bytes": size_bytes})
    cache.clear = MagicMock()
    return cache


# ---------------------------------------------------------------------------
# TestHelpAndVersion
# ---------------------------------------------------------------------------

class TestHelpAndVersion:
    def test_help_shows_usage(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        output = result.output.lower()
        assert "usage" in output or "natural language" in output

    def test_version_shows_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


# ---------------------------------------------------------------------------
# TestTransformCommand
# ---------------------------------------------------------------------------

class TestTransformCommand:
    def test_transform_from_file(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n")

        engine = _make_mock_engine()

        with patch("dt.cli._get_engine", return_value=engine), \
             patch("dt.cli._get_alias_store", return_value=_make_mock_alias_store()):
            result = runner.invoke(app, [
                str(csv_file), "sort by age",
            ])

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        engine.transform.assert_called_once()

    def test_transform_from_stdin(self):
        csv_data = "name,age\nAlice,30\nBob,25\n"
        engine = _make_mock_engine()

        with patch("dt.cli._get_engine", return_value=engine), \
             patch("dt.cli._get_alias_store", return_value=_make_mock_alias_store()):
            result = runner.invoke(app, ["-", "sort by age"], input=csv_data)

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        engine.transform.assert_called_once()

    def test_out_format_flag(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age\nAlice,30\n")

        result_df = pl.DataFrame({"name": ["Alice"], "age": [30]})
        engine = _make_mock_engine(return_df=result_df)

        with patch("dt.cli._get_engine", return_value=engine), \
             patch("dt.cli._get_alias_store", return_value=_make_mock_alias_store()):
            result = runner.invoke(app, [
                str(csv_file), "keep all", "--out", "json",
            ])

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        # Output should contain JSON
        assert "[" in result.output or "{" in result.output

    def test_show_code_flag(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age\nAlice,30\n")

        result_df = pl.DataFrame({"name": ["Alice"], "age": [30]})
        engine = _make_mock_engine(return_df=result_df, code_str="df = df.sort('age')")

        with patch("dt.cli._get_engine", return_value=engine), \
             patch("dt.cli._get_alias_store", return_value=_make_mock_alias_store()):
            result = runner.invoke(app, [
                str(csv_file), "sort by age", "--show-code",
            ])

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        # Code should appear in stderr
        assert "df = df.sort" in result.stderr

    def test_preview_flag(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("x\n" + "\n".join(str(i) for i in range(20)) + "\n")

        # Return 20-row DataFrame
        result_df = pl.DataFrame({"x": list(range(20))})
        engine = _make_mock_engine(return_df=result_df)

        with patch("dt.cli._get_engine", return_value=engine), \
             patch("dt.cli._get_alias_store", return_value=_make_mock_alias_store()):
            result = runner.invoke(app, [
                str(csv_file), "keep all", "--preview",
            ])

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        # Output should have at most 11 lines (header + 10 data rows)
        lines = [line for line in result.output.strip().splitlines() if line.strip()]
        assert len(lines) <= 11


# ---------------------------------------------------------------------------
# TestAliasCommands
# ---------------------------------------------------------------------------

class TestAliasCommands:
    def test_alias_save(self):
        store = _make_mock_alias_store()
        with patch("dt.cli._get_alias_store", return_value=store):
            result = runner.invoke(app, ["alias", "save", "topten", "show first 10 rows"])

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        store.save.assert_called_once_with("topten", "show first 10 rows")

    def test_alias_list(self):
        store = _make_mock_alias_store({"topten": "show first 10 rows"})
        with patch("dt.cli._get_alias_store", return_value=store):
            result = runner.invoke(app, ["alias", "list"])

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        # Rich table output goes to stderr
        assert "topten" in result.stderr

    def test_alias_delete(self):
        store = _make_mock_alias_store()
        with patch("dt.cli._get_alias_store", return_value=store):
            result = runner.invoke(app, ["alias", "delete", "topten"])

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        store.delete.assert_called_once_with("topten")


# ---------------------------------------------------------------------------
# TestCacheCommands
# ---------------------------------------------------------------------------

class TestCacheCommands:
    def test_cache_stats(self):
        cache = _make_mock_cache(entries=42, size_bytes=8192)
        with patch("dt.cli._get_cache", return_value=cache):
            result = runner.invoke(app, ["cache", "stats"])

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        assert "42" in result.stderr
        assert "8192" in result.stderr

    def test_cache_clear(self):
        cache = _make_mock_cache()
        with patch("dt.cli._get_cache", return_value=cache):
            result = runner.invoke(app, ["cache", "clear"])

        assert result.exit_code == 0, f"stdout={result.output!r} stderr={result.stderr!r}"
        cache.clear.assert_called_once()
        assert "cleared" in result.stderr.lower()
