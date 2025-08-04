"""Command line interface for bankcleanr."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import jsonschema
import typer

from .extractor import extract_transactions

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "transaction_v1.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text())

app = typer.Typer()


@app.command()
def extract(
    input_pdf: Path,
    output_jsonl: Path,
    bank: str = typer.Option("barclays", "--bank", help="Bank identifier"),
) -> None:
    """Extract transactions from PDF and write JSONL."""
    records = extract_transactions(str(input_pdf), bank=bank)
    with output_jsonl.open("w", encoding="utf-8") as fh:
        for item in records:
            jsonschema.validate(item, SCHEMA)
            fh.write(json.dumps(item) + "\n")


@app.command()
def build() -> None:
    """Build standalone executable using PyInstaller."""
    subprocess.run(
        [
            "pyinstaller",
            "--name",
            "bankcleanr",
            "--onefile",
            "bankcleanr/cli.py",
        ],
        check=True,
    )


if __name__ == "__main__":  # pragma: no cover
    app()

