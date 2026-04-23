"""Tests for the Ollama LLM backend."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestOllamaBackendGenerateCode:
    """OllamaBackend.generate_code must call ollama and return code."""

    @patch("dt.llm.ollama.ollama_client")
    def test_generate_code_returns_string(self, mock_ollama_mod):
        from dt.llm.ollama import OllamaBackend

        mock_client = MagicMock()
        mock_ollama_mod.Client.return_value = mock_client

        mock_client.generate.return_value = {
            "response": "```python\ndef transform(df):\n    result = df\n    return result\n```"
        }

        backend = OllamaBackend()
        result = backend.generate_code("select all rows")

        assert isinstance(result, str)
        assert "def transform" in result

    @patch("dt.llm.ollama.ollama_client")
    def test_uses_specified_model(self, mock_ollama_mod):
        from dt.llm.ollama import OllamaBackend

        mock_client = MagicMock()
        mock_ollama_mod.Client.return_value = mock_client

        mock_client.generate.return_value = {
            "response": "```python\ndef transform(df):\n    result = df\n    return result\n```"
        }

        backend = OllamaBackend(model="custom-model:latest")
        backend.generate_code("select all rows")

        call_kwargs = mock_client.generate.call_args
        model_arg = call_kwargs.kwargs.get("model") or call_kwargs[1].get("model")
        if model_arg is None:
            # Might be a positional arg
            model_arg = call_kwargs[0][0] if call_kwargs[0] else None
        assert model_arg == "custom-model:latest"
