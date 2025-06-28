import typer

from .io.loader import load_transactions
from .reports.writer import write_summary
from .settings import get_settings

app = typer.Typer(help="BankCleanr CLI")


@app.command()
def analyse(file: str, output: str = "summary.csv"):
    """Analyse a statement file and write a summary."""
    typer.echo(f"Analysing {file}")
    transactions = load_transactions(file)
    write_summary(transactions, output)
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
