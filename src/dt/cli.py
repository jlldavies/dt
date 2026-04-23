"""dt CLI - Natural language data transformer."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
import typer
from rich.console import Console
from rich.table import Table

from dt import __version__
from dt.aliases.store import AliasStore
from dt.cache.store import CodeCache
from dt.formats import detect_format, get_handler
from dt.transform.engine import TransformEngine

# Register all format handlers so @register decorators fire
import dt.formats.csv_handler  # noqa: F401
import dt.formats.json_handler  # noqa: F401
import dt.formats.yaml_handler  # noqa: F401
import dt.formats.xml_handler  # noqa: F401
import dt.formats.excel_handler  # noqa: F401

# All status/diagnostic output goes to stderr
console = Console(stderr=True)


# ---------------------------------------------------------------------------
# Helper factories (module-level so tests can mock them)
# ---------------------------------------------------------------------------

def _get_alias_store() -> AliasStore:
    return AliasStore()


def _get_cache() -> CodeCache:
    return CodeCache()


def _get_engine(
    backend: str,
    model: str | None,
    no_cache: bool,
) -> TransformEngine:
    """Create a TransformEngine with the chosen backend."""
    if backend == "claude":
        from dt.llm.claude import ClaudeBackend

        llm = ClaudeBackend(model=model) if model else ClaudeBackend()
    elif backend == "ollama":
        from dt.llm.ollama import OllamaBackend

        llm = OllamaBackend(model=model) if model else OllamaBackend()
    else:
        console.print(f"[red]Unknown backend: {backend!r}[/red]")
        raise SystemExit(1)

    cache_store = None if no_cache else _get_cache()
    return TransformEngine(
        backend=llm,
        use_cache=not no_cache,
        cache_store=cache_store,
    )


# ---------------------------------------------------------------------------
# Click-based CLI (better control over subcommand + default arg routing)
# ---------------------------------------------------------------------------

class DefaultGroup(click.Group):
    """A Click group that routes unknown commands to a default handler.

    If the first arg is not a known subcommand, treat the whole invocation
    as the default 'transform' command.
    """

    def parse_args(self, ctx, args):
        # If args start with a known subcommand, route normally
        # Otherwise, inject 'transform' as the command name
        if args and args[0] not in self.commands and not args[0].startswith("-"):
            args = ["transform"] + args
        elif args and args[0] == "-":
            # stdin marker - route to transform
            args = ["transform"] + args
        elif not args:
            args = ["transform", "--help"]
        return super().parse_args(ctx, args)


@click.group(cls=DefaultGroup)
@click.version_option(__version__, "--version", "-V", prog_name="dt")
def app() -> None:
    """Natural language data transformer."""


@app.command()
@click.argument("source", default="-")
@click.argument("instruction", default="")
@click.option("--format", "-f", "fmt", default=None, help="Explicit input format.")
@click.option("--out", "-o", default=None, help="Output format (default: same as input).")
@click.option("--backend", "-b", default="claude", help="LLM backend: 'claude' or 'ollama'.")
@click.option("--model", "-m", default=None, help="Model name override.")
@click.option("--show-code", is_flag=True, help="Print generated code to stderr.")
@click.option("--preview", "-p", is_flag=True, help="Show only first 10 rows.")
@click.option("--no-cache", is_flag=True, help="Skip cache.")
@click.option("--no-sample", is_flag=True, help="Don't send sample rows to LLM.")
def transform(
    source: str,
    instruction: str,
    fmt: str | None,
    out: str | None,
    backend: str,
    model: str | None,
    show_code: bool,
    preview: bool,
    no_cache: bool,
    no_sample: bool,
) -> None:
    """Transform data using a natural language instruction."""
    if not instruction:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        return

    # 1. Resolve aliases
    alias_store = _get_alias_store()
    resolved = alias_store.get(instruction)
    if resolved is not None:
        instruction = resolved

    # 2. Read input
    if source == "-":
        raw = click.get_text_stream("stdin").read()
        input_fmt = fmt or detect_format(content=raw)
    else:
        path = Path(source)
        if not path.exists():
            console.print(f"[red]File not found: {source}[/red]")
            raise SystemExit(1)
        raw = path.read_text(encoding="utf-8")
        input_fmt = fmt or detect_format(filename=source, content=raw)

    if input_fmt is None:
        console.print("[red]Could not detect input format. Use --format to specify.[/red]")
        raise SystemExit(1)

    handler = get_handler(input_fmt)
    df = handler.read(raw)

    # 3. Create engine
    engine = _get_engine(backend, model, no_cache)
    if no_sample:
        engine.sample_rows = 0

    # 4. Transform
    result = engine.transform(df, instruction, return_code=show_code)

    if show_code:
        result_df, code = result
        console.print(f"[dim]# Generated code:[/dim]\n{code}")
    else:
        result_df = result

    # 5. Preview
    if preview:
        result_df = result_df.head(10)

    # 6. Write output
    out_fmt = out or input_fmt
    out_handler = get_handler(out_fmt)
    output = out_handler.write(result_df)

    # Only data goes to stdout
    if isinstance(output, bytes):
        sys.stdout.buffer.write(output)
    else:
        click.echo(output, nl=False)


# ---------------------------------------------------------------------------
# Alias subcommands
# ---------------------------------------------------------------------------

@app.group()
def alias() -> None:
    """Manage instruction aliases."""


@alias.command("save")
@click.argument("name")
@click.argument("instruction")
def alias_save(name: str, instruction: str) -> None:
    """Save an instruction alias."""
    store = _get_alias_store()
    store.save(name, instruction)
    console.print(f"Alias [bold]{name}[/bold] saved.")


@alias.command("list")
def alias_list() -> None:
    """List all saved aliases."""
    store = _get_alias_store()
    aliases = store.list_all()
    if not aliases:
        console.print("No aliases saved.")
        return
    table = Table(title="Aliases")
    table.add_column("Name", style="bold")
    table.add_column("Instruction")
    for name, instruction in sorted(aliases.items()):
        table.add_row(name, instruction)
    console.print(table)


@alias.command("delete")
@click.argument("name")
def alias_delete(name: str) -> None:
    """Delete an alias."""
    store = _get_alias_store()
    try:
        store.delete(name)
    except KeyError:
        console.print(f"[red]Alias not found: {name!r}[/red]")
        raise SystemExit(1)
    console.print(f"Alias [bold]{name}[/bold] deleted.")


# ---------------------------------------------------------------------------
# Cache subcommands
# ---------------------------------------------------------------------------

@app.group()
def cache() -> None:
    """Manage the code cache."""


@cache.command("stats")
def cache_stats() -> None:
    """Show cache statistics."""
    c = _get_cache()
    s = c.stats()
    console.print(f"Entries: {s['entries']}")
    console.print(f"Size:    {s['size_bytes']} bytes")


@cache.command("clear")
def cache_clear() -> None:
    """Clear the code cache."""
    c = _get_cache()
    c.clear()
    console.print("Cache cleared.")
