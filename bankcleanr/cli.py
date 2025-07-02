import typer
from pathlib import Path

from .io.loader import load_transactions
from .reports.writer import (
    write_summary,
    write_pdf_summary,
    format_terminal_summary,
)
from .settings import get_settings

app = typer.Typer(help="BankCleanr CLI")

# Path to a sample statement used for demonstrations
SAMPLE_STATEMENT = (
    Path(__file__).resolve().parent.parent
    / "Redacted bank statements"
    / "22b583f5-4060-44eb-a844-945cd612353c (1).pdf"
)


@app.command()
def analyse(
    file: str = typer.Argument(str(SAMPLE_STATEMENT)),
    output: str = "summary.csv",
    pdf: str | None = typer.Option(
        None, "--pdf", help="Write an additional PDF summary to this file"
    ),
    terminal: bool = typer.Option(
        False, "--terminal", help="Display the summary in the terminal"
    ),
):
    """Analyse a statement file and write a summary."""
    typer.echo(f"Analysing {file}")
    transactions = load_transactions(file)
    write_summary(transactions, output)
    if pdf:
        write_pdf_summary(transactions, pdf)
    if terminal:
        typer.echo(format_terminal_summary(transactions))
    typer.echo("Analysis complete")


@app.command()
def config():
    """Show the loaded settings path."""
    settings = get_settings()
    typer.echo(f"Loaded settings from {settings.config_path}")


@app.command()
def gui():
    """Launch the GUI (not implemented)."""
    typer.echo("GUI not implemented yet")
