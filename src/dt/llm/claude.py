"""Claude (Anthropic) LLM backend."""

from __future__ import annotations

import os

import anthropic

from dt.llm.base import LLMBackend
from dt.llm.prompt import SYSTEM_PROMPT
from dt.transform.sandbox import extract_code_block


class ClaudeBackend(LLMBackend):
    """LLM backend that uses the Anthropic Messages API."""

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Please set it to use the Claude backend."
            )
        self.model = model
        self._client = anthropic.Anthropic()

    def generate_code(self, prompt: str) -> str:
        """Generate transformation code via the Claude API."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = response.content[0].text
        return extract_code_block(raw_text)
