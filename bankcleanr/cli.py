"""Command line interface for bankcleanr."""
from __future__ import annotations

import json
import subprocess
import sys
import platform
from importlib import resources
from pathlib import Path

import jsonschema
import typer

from bankcleanr.extractor import extract_transactions
from bankcleanr.pii import mask_pii

if getattr(sys, "frozen", False):
    SCHEMA_PATH = Path(sys._MEIPASS) / "schemas" / "transaction_v1.json"  # type: ignore[attr-defined]
else:
    SCHEMA_PATH = resources.files("bankcleanr.schemas").joinpath("transaction_v1.json")
SCHEMA = json.loads(SCHEMA_PATH.read_text())

app = typer.Typer()


@app.command()
def extract(
    input_pdf: Path = typer.Argument(
        ..., exists=True, file_okay=True, dir_okay=True, readable=True,
        help="Path to a PDF file or directory of PDFs",
    ),
    output_jsonl: Path = typer.Argument(..., help="Output JSONL file"),
    bank: str = typer.Option(
        "barclays",
        "--bank",
        help="Bank identifier (barclays, hsbc, lloyds, coop)",
    ),
    mask_names: str = typer.Option("", "--mask-names", help="Comma-separated names to mask"),
) -> None:
    """Extract transactions from PDFs and write JSONL."""
    if not mask_names and sys.stdin.isatty():
        mask_names = typer.prompt("Enter comma-separated names to mask", default="")
    names = [n.strip() for n in mask_names.split(",") if n.strip()]
    with output_jsonl.open("w", encoding="utf-8") as fh:
        for item in extract_transactions(str(input_pdf), bank=bank):
            desc = item.get("description") or ""
            item["description"] = mask_pii(desc, names)
            jsonschema.validate(item, SCHEMA)
            fh.write(json.dumps(item) + "\n")


# register an alias so older workflows using "parse" still function
app.command(name="parse")(extract)


@app.command()
def build() -> None:
    """Build standalone executable using PyInstaller."""
    system = platform.system().lower()
    if system == "darwin":
        system = "macos"
    machine = platform.machine().lower()
    name = f"bankcleanr-{system}-{machine}"
    sep = ";" if system.startswith("win") else ":"
    subprocess.run(
        [
            "pyinstaller",
            "--name",
            name,
            "--onefile",
            "--add-data",
            f"bankcleanr/schemas/transaction_v1.json{sep}schemas",
            "--collect-submodules",
            "bankcleanr.parsers",
            "--hidden-import",
            "bankcleanr.schemas",
            "bankcleanr/cli.py",
        ],
        check=True,
    )


if __name__ == "__main__":  # pragma: no cover
    app()

