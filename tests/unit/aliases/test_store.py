from __future__ import annotations

import pytest

from dt.aliases.store import AliasStore


class TestAliasStore:
    def test_get_missing_returns_none(self, tmp_path):
        store = AliasStore(path=tmp_path / "aliases.json")
        assert store.get("nonexistent") is None

    def test_save_and_get(self, tmp_path):
        store = AliasStore(path=tmp_path / "aliases.json")
        store.save("greet", "Say hello politely")
        assert store.get("greet") == "Say hello politely"

    def test_list_all(self, tmp_path):
        store = AliasStore(path=tmp_path / "aliases.json")
        store.save("a", "do A")
        store.save("b", "do B")
        assert store.list_all() == {"a": "do A", "b": "do B"}

    def test_delete(self, tmp_path):
        store = AliasStore(path=tmp_path / "aliases.json")
        store.save("tmp", "temporary")
        store.delete("tmp")
        assert store.get("tmp") is None

    def test_delete_nonexistent_raises_key_error(self, tmp_path):
        store = AliasStore(path=tmp_path / "aliases.json")
        with pytest.raises(KeyError, match="Alias not found"):
            store.delete("ghost")

    def test_persistent_across_instances(self, tmp_path):
        path = tmp_path / "aliases.json"
        store1 = AliasStore(path=path)
        store1.save("key", "value")

        store2 = AliasStore(path=path)
        assert store2.get("key") == "value"

    def test_overwrite_existing(self, tmp_path):
        store = AliasStore(path=tmp_path / "aliases.json")
        store.save("x", "old")
        store.save("x", "new")
        assert store.get("x") == "new"
