"""Tests for the Claude LLM backend."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestClaudeBackendRequiresApiKey:
    """ClaudeBackend must raise RuntimeError when ANTHROPIC_API_KEY is missing."""

    def test_requires_api_key(self):
        from dt.llm.claude import ClaudeBackend

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                ClaudeBackend()


class TestClaudeBackendGenerateCode:
    """ClaudeBackend.generate_code must call the Anthropic API and return code."""

    @patch("dt.llm.claude.anthropic")
    def test_generate_code_returns_string(self, mock_anthropic_mod):
        from dt.llm.claude import ClaudeBackend

        # Set up the mock client and response
        mock_client = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text="```python\ndef transform(df):\n    result = df\n    return result\n```")
        ]
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            backend = ClaudeBackend()
            result = backend.generate_code("select all rows")

        assert isinstance(result, str)
        assert "def transform" in result

    @patch("dt.llm.claude.anthropic")
    def test_uses_specified_model(self, mock_anthropic_mod):
        from dt.llm.claude import ClaudeBackend

        mock_client = MagicMock()
        mock_anthropic_mod.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text="```python\ndef transform(df):\n    result = df\n    return result\n```")
        ]
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            backend = ClaudeBackend(model="claude-test-model")
            backend.generate_code("select all rows")

        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs.get("model") == "claude-test-model" or call_kwargs[1].get("model") == "claude-test-model"
