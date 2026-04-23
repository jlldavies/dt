"""Format handler registry with protocol and registration decorator."""

from __future__ import annotations

from typing import Protocol

import polars as pl


class FormatHandler(Protocol):
    """Protocol that all format handlers must implement."""

    def read(self, source: str | bytes) -> pl.DataFrame: ...
    def write(self, df: pl.DataFrame) -> str | bytes: ...


_handlers: dict[str, FormatHandler] = {}


def register(fmt: str):
    """Class decorator that registers a format handler instance."""

    def decorator(cls):
        _handlers[fmt] = cls()
        return cls

    return decorator


def get_handler(fmt: str) -> FormatHandler:
    """Return the handler for a given format, or raise KeyError."""
    if fmt not in _handlers:
        supported = ", ".join(sorted(_handlers.keys()))
        raise KeyError(f"Unsupported format: {fmt!r}. Supported: {supported}")
    return _handlers[fmt]


def supported_formats() -> list[str]:
    """Return sorted list of registered format names."""
    return sorted(_handlers.keys())
