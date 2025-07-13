import typer
from pathlib import Path

from .io.loader import load_from_path
from typing import Optional
from .reports.writer import (
    write_summary,
    write_pdf_summary,
    format_terminal_summary,
)
from . import recommendation
from .rules import heuristics
from .analytics import calculate_savings, totals_by_type
from .settings import get_settings
from .reports.disclaimers import GLOBAL_DISCLAIMER

app = typer.Typer(help="BankCleanr CLI")

# Path to a sample statement used for demonstrations
SAMPLE_STATEMENT = (
    Path(__file__).resolve().parent.parent
    / "Redacted bank statements"
    / "22b583f5-4060-44eb-a844-945cd612353c (1).pdf"
)


@app.command()
def analyse(
    path: str = typer.Argument(
        str(SAMPLE_STATEMENT),
        help="Path to a PDF file or directory containing PDF files",
    ),
    output: str = "summary.csv",
    pdf: Optional[str] = typer.Option(
        None, "--pdf", help="Write an additional PDF summary to this file"
    ),
    outdir: Optional[str] = typer.Option(
        None,
        "--outdir",
        help="Directory to write summary.csv and PDF outputs",
    ),
    terminal: bool = typer.Option(
        False, "--terminal", help="Display the summary in the terminal"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show each file as it is processed",
    ),
):
    """Analyse a statement file or directory and write a summary."""
    typer.echo(f"Analysing {path}")
    transactions = load_from_path(path, verbose=verbose)

    settings = get_settings()
    if settings.api_key:
        # use heuristics with LLM fallback when API key is available
        recs = recommendation.recommend_transactions(
            transactions, provider=settings.llm_provider
        )
    else:
        # fall back to heuristics only
        labels = heuristics.classify_transactions(transactions)
        kb = recommendation.load_knowledge_base()
        recs: list[recommendation.Recommendation] = []
        for tx, label in zip(transactions, labels):
            if label in kb:
                action = "Cancel"
                info = kb[label]
            else:
                action = "Keep"
                info = None
            recs.append(recommendation.Recommendation(tx, label, action, info))

    outdir_path: Path | None = None
    if outdir:
        outdir_path = Path(outdir)
        outdir_path.mkdir(parents=True, exist_ok=True)

    output_path = Path(output)
    if outdir_path:
        output_path = outdir_path / output_path.name
    write_summary(recs, str(output_path))

    if pdf:
        pdf_path = Path(pdf)
        if outdir_path:
            pdf_path = outdir_path / pdf_path.name
        write_pdf_summary(recs, str(pdf_path))
    if terminal:
        typer.echo(format_terminal_summary(recs))

    savings = calculate_savings(recs)
    totals = totals_by_type(recs)
    typer.echo(f"Potential savings if cancelled: {savings:.2f}")
    if totals:
        typer.echo("Totals by type:")
        for name, total in totals.items():
            typer.echo(f"- {name}: {total:.2f}")
    typer.echo("Analysis complete")
    if not terminal:
        typer.echo(GLOBAL_DISCLAIMER)


@app.command()
def config():
    """Show the loaded settings path."""
    settings = get_settings()
    typer.echo(f"Loaded settings from {settings.config_path}")


@app.command()
def gui():
    """Launch the GUI (not implemented)."""
    typer.echo("GUI not implemented yet")
