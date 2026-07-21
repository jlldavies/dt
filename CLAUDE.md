# dt

Last reviewed: 2026-07-21

Natural-language data transformer CLI. Pipe structured data in, describe the transform in
plain English, get results out. `dt` auto-detects the input format, sends only the schema
plus a small sample to an LLM, has the LLM generate Polars code, validates that code with
AST analysis before running it, and writes the result in the chosen format. Installs as the
`dt` command (package name `dt-cli`).

## Commands

Development install with test tooling (from repo root):

```bash
pip install -e ".[dev]"
```

Run the CLI (once installed):

```bash
dt sales.csv "group by region, sum revenue, sort descending"
cat data.json | dt - "filter where status is active" --out csv
```

Run the CLI without installing, straight from source:

```bash
python -m dt data.csv "keep all rows" --out json
```

Run the test suite:

```bash
pytest                              # everything
pytest tests/unit                   # unit tests only
pytest tests/integration            # integration tests only
pytest --cov=dt --cov-report=term-missing   # with coverage
```

## Architecture

Pipeline stages live in `src/dt/`, wired together by the CLI:

- `cli.py` is the Typer app (entry point `dt = "dt.cli:app"`). It parses arguments, resolves
  aliases, checks the cache, drives the transform, and formats output. All status and
  diagnostic text goes to stderr so stdout stays pipe-clean.
- `formats/` reads and writes the supported formats. `detect.py` auto-detects format from
  extension and content; `registry.py` holds a decorator-based handler registry that each
  `*_handler.py` registers into (the CLI imports the handler modules so their `@register`
  decorators fire). Supported: CSV, TSV, JSON, JSONL, YAML, XML, Excel.
- `llm/` generates transformation code. `base.py` defines the backend interface,
  `prompt.py` builds the prompt from schema plus sample rows, and `claude.py` / `ollama.py`
  are the two backends.
- `transform/` runs the generated code. `sandbox.py` does AST validation (blocking dangerous
  imports and calls) and `engine.py` orchestrates generate-validate-execute over Polars.
- `cache/` caches generated code by instruction plus schema hash (diskcache). `aliases/`
  stores reusable named transforms as JSON.

## Key Files

- `pyproject.toml` - package metadata, dependencies, dev extra, the `dt` script entry point,
  and pytest/coverage config.
- `src/dt/cli.py` - the Typer CLI; the top-level command wiring.
- `src/dt/__main__.py` - enables `python -m dt`.
- `src/dt/formats/detect.py` and `src/dt/formats/registry.py` - format detection and the
  handler registry; individual handlers are the `*_handler.py` files alongside them.
- `src/dt/llm/prompt.py` - builds the LLM prompt (schema plus sample rows).
- `src/dt/transform/sandbox.py` - AST safety validation before any generated code runs.
- `src/dt/transform/engine.py` - the generate-validate-execute transform engine.
- `src/dt/cache/store.py` - `CodeCache`; `src/dt/aliases/store.py` - `AliasStore`.
- `tests/` - `unit/` mirrors the `src/dt/` package layout, `integration/` covers the CLI,
  piping, and format round-trips; `tests/fixtures/` holds one sample file per format.
- `.github/workflows/ci.yml` - the CI matrix and test/coverage steps.

## Conventions

- Src-layout package (`src/dt/`) built with hatchling; every module opens with
  `from __future__ import annotations` and uses type hints.
- stdout is reserved for data output; all human-facing messages go to stderr (the CLI's
  `Console(stderr=True)`), so `dt` stays safe in pipes.
- New formats are added as a `*_handler.py` registered via the `formats/registry.py`
  decorator, then imported in `cli.py` so the decorator runs.
- New LLM backends implement the `llm/base.py` interface.
- Store classes (`CodeCache`, `AliasStore`) accept an explicit path/dir argument so tests can
  point them at temp locations instead of the real user directories.

## Environment

- Python 3.11 or newer (`requires-python = ">=3.11"`).
- `ANTHROPIC_API_KEY` is required for the default Claude backend; the Claude backend raises if
  it is unset. API keys are read from the environment only and never stored by the tool.
- The Ollama backend needs no API key; it talks to `OLLAMA_HOST` (default
  `http://localhost:11434`) and a locally pulled model.
- Aliases persist to `platformdirs` user-config dir (`.../dt/aliases.json`); the code cache
  persists to the `platformdirs` user-cache dir (`.../dt/code_cache`). Both live outside the
  repo.
- Runtime dependencies (typer, rich, polars, pyyaml, lxml, openpyxl, fastexcel, anthropic,
  ollama, diskcache, platformdirs) install via `pip install -e .`.

## Testing

- Pytest is the runner; config is in `pyproject.toml` (`testpaths = ["tests"]`, per-test
  timeout, `-v --tb=short`).
- `tests/unit/` mirrors the package (formats, llm, cache, aliases, transform);
  `tests/integration/` exercises the CLI end to end (`test_cli.py`, `test_piping.py`,
  `test_format_roundtrip.py`) against `tests/fixtures/`.
- Coverage is enforced: `[tool.coverage.report]` sets `fail_under = 90`, so
  `pytest --cov=dt` fails below that threshold.
- CI runs the unit and integration suites separately, then a coverage run, across a matrix of
  Ubuntu/Windows/macOS and Python 3.11-3.13, with `PYTHONUTF8=1` set.

## Gotchas

- The Claude backend fails fast when `ANTHROPIC_API_KEY` is missing; use `--backend ollama`
  for a fully local, key-free run.
- Format handlers only exist once their module is imported, because registration is decorator
  driven; a new handler that is never imported in `cli.py` will silently not register.
- `sandbox.py` blocks dangerous imports and calls (os, subprocess, sys, open, exec, eval, and
  more) before running generated code; loosening that list re-opens the arbitrary-code-
  execution surface the design specifically closes.
- CI pins `PYTHONUTF8=1` and runs on Windows too; avoid code or tests that assume a UTF-8
  locale or POSIX-only paths.
- A `.claude/` directory (including any leftover agent worktrees) is gitignored - do not
  reference or commit anything under it.
