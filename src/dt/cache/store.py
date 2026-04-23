from __future__ import annotations

from pathlib import Path

import diskcache


class CodeCache:
    def __init__(self, cache_dir: str | Path | None = None):
        if cache_dir is None:
            from platformdirs import user_cache_dir

            cache_dir = Path(user_cache_dir("dt")) / "code_cache"
        self._cache = diskcache.Cache(str(cache_dir))

    def get(self, key: str) -> str | None:
        return self._cache.get(key)

    def set(self, key: str, code: str) -> None:
        self._cache.set(key, code)

    def clear(self) -> None:
        self._cache.clear()

    def stats(self) -> dict:
        return {"entries": len(self._cache), "size_bytes": self._cache.volume()}

    def close(self) -> None:
        self._cache.close()
