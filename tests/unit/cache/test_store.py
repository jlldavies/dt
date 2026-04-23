from __future__ import annotations

from dt.cache.store import CodeCache


class TestCodeCache:
    def test_get_missing_key_returns_none(self, tmp_path):
        cache = CodeCache(cache_dir=tmp_path / "cache")
        try:
            assert cache.get("nonexistent") is None
        finally:
            cache.close()

    def test_set_and_get(self, tmp_path):
        cache = CodeCache(cache_dir=tmp_path / "cache")
        try:
            cache.set("k1", "print('hello')")
            assert cache.get("k1") == "print('hello')"
        finally:
            cache.close()

    def test_overwrite_existing(self, tmp_path):
        cache = CodeCache(cache_dir=tmp_path / "cache")
        try:
            cache.set("k1", "v1")
            cache.set("k1", "v2")
            assert cache.get("k1") == "v2"
        finally:
            cache.close()

    def test_clear_empties_cache(self, tmp_path):
        cache = CodeCache(cache_dir=tmp_path / "cache")
        try:
            cache.set("a", "1")
            cache.set("b", "2")
            cache.clear()
            assert cache.get("a") is None
            assert cache.get("b") is None
            assert cache.stats()["entries"] == 0
        finally:
            cache.close()

    def test_persistent_across_instances(self, tmp_path):
        cache_dir = tmp_path / "cache"
        cache1 = CodeCache(cache_dir=cache_dir)
        try:
            cache1.set("key", "value")
        finally:
            cache1.close()

        cache2 = CodeCache(cache_dir=cache_dir)
        try:
            assert cache2.get("key") == "value"
        finally:
            cache2.close()

    def test_stats_returns_correct_counts(self, tmp_path):
        cache = CodeCache(cache_dir=tmp_path / "cache")
        try:
            assert cache.stats()["entries"] == 0
            cache.set("x", "data")
            stats = cache.stats()
            assert stats["entries"] == 1
            assert stats["size_bytes"] > 0
        finally:
            cache.close()
