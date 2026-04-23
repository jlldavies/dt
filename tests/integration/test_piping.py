"""Subprocess piping system tests – run ``dt`` as a real subprocess."""

from __future__ import annotations

import subprocess
import sys

import pytest


def run_dt(*args: str, input_data: str | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "dt", *args]
    return subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# CLI basics
# ---------------------------------------------------------------------------

class TestCLIBasics:
    def test_help(self) -> None:
        result = run_dt("--help")
        assert result.returncode == 0
        output = result.stdout.lower()
        assert "transform" in output or "dt" in output

    def test_version(self) -> None:
        result = run_dt("--version")
        assert result.returncode == 0
        assert "0.1.0" in result.stdout


# ---------------------------------------------------------------------------
# Alias subprocess
# ---------------------------------------------------------------------------

class TestAliasSubprocess:
    def test_alias_list(self) -> None:
        result = run_dt("alias", "list")
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Cache subprocess
# ---------------------------------------------------------------------------

class TestCacheSubprocess:
    def test_cache_stats(self) -> None:
        result = run_dt("cache", "stats")
        assert result.returncode == 0

    def test_cache_clear(self) -> None:
        result = run_dt("cache", "clear")
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_nonexistent_file(self) -> None:
        result = run_dt("transform", "/nonexistent.csv", "do something")
        assert result.returncode != 0

    def test_no_instruction(self) -> None:
        """Missing instruction causes transform to print help (exit 0) since
        both arguments are optional Click arguments."""
        result = run_dt("transform", "somefile.csv")
        # Click shows the help text when the instruction is omitted.
        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "transform" in result.stdout.lower()
