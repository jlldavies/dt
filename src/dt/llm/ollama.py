"""Ollama LLM backend."""

from __future__ import annotations

import os

import ollama as ollama_client

from dt.llm.base import LLMBackend
from dt.llm.prompt import SYSTEM_PROMPT
from dt.transform.sandbox import extract_code_block


class OllamaBackend(LLMBackend):
    """LLM backend that uses a local Ollama instance."""

    def __init__(self, model: str = "qwen2.5-coder:7b") -> None:
        self.model = model
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self._client = ollama_client.Client(host=host)

    def generate_code(self, prompt: str) -> str:
        """Generate transformation code via the Ollama API."""
        response = self._client.generate(
            model=self.model,
            system=SYSTEM_PROMPT,
            prompt=prompt,
        )
        raw_text = response["response"]
        return extract_code_block(raw_text)
