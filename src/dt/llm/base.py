"""Abstract base class for LLM backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMBackend(ABC):
    """Base class that all LLM backends must implement."""

    @abstractmethod
    def generate_code(self, prompt: str) -> str:
        """Generate transformation code from a natural-language prompt.

        Parameters
        ----------
        prompt:
            The fully-assembled user prompt (schema + instruction).

        Returns
        -------
        str
            The extracted Python code (without markdown fences).
        """
        ...
