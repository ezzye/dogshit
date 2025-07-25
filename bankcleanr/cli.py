import typer
import logging
import os
from pathlib import Path
import csv
import json

from .io.loader import load_from_path
from typing import Optional, Mapping
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

LOG_LEVEL_ENV = "BANKCLEANR_LOG_LEVEL"

# Default directory for CLI outputs
DEFAULT_OUTDIR = Path("results")


@app.callback()
def main(log_level: str = typer.Option(None, help="Set log verbosity (e.g. DEBUG)")):
    level = (log_level or os.getenv(LOG_LEVEL_ENV, "WARNING")).upper()
    logging.basicConfig(level=getattr(logging, level, logging.WARNING))

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
    typer.echo("Reading statements...")
    transactions = load_from_path(path, verbose=verbose)
    typer.echo(f"Loaded {len(transactions)} transactions")

    settings = get_settings()
    if settings.api_key:
        # use heuristics with LLM fallback when API key is available
        typer.echo(f"Classifying with {settings.llm_provider} LLM...")
        recs = recommendation.recommend_transactions(
            transactions, provider=settings.llm_provider
        )
    else:
        # fall back to heuristics only
        typer.echo("Classifying using heuristics...")
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

    typer.echo("Writing results...")
    outdir_path = Path(outdir) if outdir else DEFAULT_OUTDIR
    outdir_path.mkdir(parents=True, exist_ok=True)

    output_path = outdir_path / Path(output).name
    write_summary(recs, str(output_path))

    if pdf:
        pdf_path = outdir_path / Path(pdf).name
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
def parse(
    path: str = typer.Argument(
        str(SAMPLE_STATEMENT),
        help="Path to a PDF file or directory containing PDF files",
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Write parsed transactions to this CSV file"
    ),
    jsonl: Optional[str] = typer.Option(
        None, "--jsonl", help="Write parsed transactions to this JSON Lines file"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show each file as it is processed",
    ),
):
    """Parse statements and return transactions without recommendations."""
    transactions = load_from_path(path, verbose=verbose)

    rows = [
        (
            tx["date"] if isinstance(tx, Mapping) else tx.date,
            tx["description"] if isinstance(tx, Mapping) else tx.description,
            tx["amount"] if isinstance(tx, Mapping) else tx.amount,
            tx.get("balance", "") if isinstance(tx, Mapping) else tx.balance,
        )
        for tx in transactions
    ]

    if jsonl:
        from .io.jsonl import write_jsonl
        write_jsonl(transactions, jsonl)
        typer.echo(jsonl)
    elif output:
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "description", "amount", "balance"])
            writer.writerows(rows)
        typer.echo(output)
    else:
        print(json.dumps([
            {
                "date": r[0],
                "description": r[1],
                "amount": r[2],
                "balance": r[3],
            }
            for r in rows
        ], indent=2))


@app.command()
def config():
    """Show the loaded settings path."""
    settings = get_settings()
    typer.echo(f"Loaded settings from {settings.config_path}")


@app.command()
def gui():
    """Launch the graphical interface (currently a stub)."""
    typer.echo("GUI not implemented yet")
