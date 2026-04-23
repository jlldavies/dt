from __future__ import annotations

import json
from pathlib import Path


class AliasStore:
    def __init__(self, path: str | Path | None = None):
        if path is None:
            from platformdirs import user_config_dir

            path = Path(user_config_dir("dt")) / "aliases.json"
        self._path = Path(path)
        self._aliases: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            self._aliases = json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._aliases, indent=2, sort_keys=True), encoding="utf-8"
        )

    def get(self, name: str) -> str | None:
        return self._aliases.get(name)

    def save(self, name: str, instruction: str) -> None:
        self._aliases[name] = instruction
        self._save()

    def delete(self, name: str) -> None:
        if name not in self._aliases:
            raise KeyError(f"Alias not found: {name!r}")
        del self._aliases[name]
        self._save()

    def list_all(self) -> dict[str, str]:
        return dict(self._aliases)
