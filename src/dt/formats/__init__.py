"""Format handler registry and auto-detection."""

from dt.formats.detect import detect_format
from dt.formats.registry import get_handler, register, supported_formats

__all__ = ["detect_format", "get_handler", "register", "supported_formats"]
