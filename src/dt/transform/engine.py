"""Transform engine orchestrating LLM code generation, validation, and execution."""

from __future__ import annotations

import hashlib
import json

import polars as pl

from dt.llm.base import LLMBackend
from dt.llm.prompt import build_transform_prompt
from dt.transform.sandbox import execute_transform


class TransformEngine:
    """Orchestrates LLM-based DataFrame transformations.

    Pipeline: instruction -> prompt -> LLM -> validate -> execute -> result
    """

    def __init__(
        self,
        backend: LLMBackend,
        use_cache: bool = True,
        cache_store=None,
        sample_rows: int = 3,
    ):
        self.backend = backend
        self.use_cache = use_cache
        self.cache_store = cache_store
        self.sample_rows = sample_rows

    def _schema_hash(self, df: pl.DataFrame) -> str:
        """Create a short hash of the DataFrame schema for cache keying."""
        schema_info = {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}
        blob = json.dumps(schema_info, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def _cache_key(self, instruction: str, schema_hash: str) -> str:
        """Build a deterministic cache key from instruction + schema hash."""
        blob = json.dumps(
            {"instruction": instruction, "schema": schema_hash}, sort_keys=True
        )
        return hashlib.sha256(blob.encode()).hexdigest()

    def transform(
        self,
        df: pl.DataFrame,
        instruction: str,
        return_code: bool = False,
    ) -> pl.DataFrame | tuple[pl.DataFrame, str]:
        """Transform a DataFrame using a natural-language instruction.

        Parameters
        ----------
        df:
            The source DataFrame.
        instruction:
            Plain-English description of the desired transformation.
        return_code:
            If *True*, return ``(result_df, generated_code)`` instead of
            just the result DataFrame.

        Returns
        -------
        pl.DataFrame or tuple[pl.DataFrame, str]
        """
        schema_hash = self._schema_hash(df)
        cache_key = self._cache_key(instruction, schema_hash)

        # Check cache
        code = None
        if self.use_cache and self.cache_store:
            code = self.cache_store.get(cache_key)

        # Generate code if not cached
        if code is None:
            prompt = build_transform_prompt(
                df, instruction, sample_rows=self.sample_rows
            )
            code = self.backend.generate_code(prompt)
            if self.use_cache and self.cache_store:
                self.cache_store.set(cache_key, code)

        # Validate and execute
        result = execute_transform(code, df)

        if return_code:
            return result, code
        return result
