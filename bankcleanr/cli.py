"""Command line interface for bankcleanr."""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

import jsonschema
import typer

from bankcleanr.extractor import extract_transactions
from bankcleanr.pii import mask_pii


def _load_schema() -> dict:
    """Return the transaction schema as a dictionary.

    Loading the schema at runtime avoids relying on importlib resources which can
    cache outdated copies when the package is installed in editable mode.  Using
    paths relative to this file ensures the latest schema is always used both in
    development and when packaged with PyInstaller.
    """

    if getattr(sys, "frozen", False):
        path = Path(sys._MEIPASS) / "schemas" / "transaction_v1.json"  # type: ignore[attr-defined]
    else:
        path = Path(__file__).resolve().parent / "schemas" / "transaction_v1.json"
    return json.loads(Path(path).read_text(encoding="utf-8"))


SCHEMA = _load_schema()

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
    count = 0
    with output_jsonl.open("w", encoding="utf-8") as fh:
        for item in extract_transactions(str(input_pdf), bank=bank):
            desc = item.get("description") or ""
            item["description"] = mask_pii(desc, names)
            amt_raw = item.get("amount")
            amt = float(amt_raw) if amt_raw is not None else 0.0
            if "type" not in item:
                item["type"] = "credit" if amt > 0 else "debit"
            jsonschema.validate(item, SCHEMA)
            fh.write(json.dumps(item) + "\n")
            count += 1
    if count == 0:
        typer.secho("No transactions extracted", err=True)
        raise typer.Exit(code=1)


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
    root = Path(__file__).resolve().parent
    schema = root / "schemas" / "transaction_v1.json"
    cli_path = Path(__file__).resolve()
    subprocess.run(
        [
            "pyinstaller",
            "--name",
            name,
            "--onefile",
            "--add-data",
            f"{schema}{sep}schemas",
            "--collect-submodules",
            "bankcleanr.parsers",
            "--hidden-import",
            "bankcleanr.schemas",
            str(cli_path),
        ],
        check=True,
    )


if __name__ == "__main__":  # pragma: no cover
    app()

