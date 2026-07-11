"""Entry point for the civic info benchmark CLI."""

import typer
from rich.console import Console

app = typer.Typer(
    name="civic-benchmark",
    help="Benchmark LLMs on US civic representative discovery.",
)
console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Civic Info Benchmark — evaluate LLMs on US civic representative discovery."""
    if ctx.invoked_subcommand is None:
        console.print("[bold green]Civic Info Benchmark[/bold green]")
        console.print("Run [cyan]app --help[/cyan] to see available commands.")
