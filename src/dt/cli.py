"""dt CLI - Natural language data transformer."""
from typing import Optional

import typer

from dt import __version__

app = typer.Typer(name="dt", help="Natural language data transformer.", no_args_is_help=True)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"dt {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", help="Show version and exit.", callback=_version_callback, is_eager=True
    ),
) -> None:
    """Natural language data transformer."""
