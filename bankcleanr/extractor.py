"""High level extraction helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterator

from .parsers import PARSER_REGISTRY


def extract_transactions(
    pdf_path: str, bank: str = "barclays"
) -> Iterator[Dict[str, str | None]]:
    """Yield transactions from a PDF or directory of PDFs using the configured parser."""
    try:
        parser_cls = PARSER_REGISTRY[bank]
    except KeyError as exc:
        available = ", ".join(sorted(PARSER_REGISTRY))
        raise ValueError(
            f"Unsupported bank '{bank}'. Available banks: {available}"
        ) from exc
    parser = parser_cls()
    path = Path(pdf_path)

    def _iter() -> Iterator[Dict[str, str | None]]:
        if path.is_dir():
            pdf_files = sorted(path.glob("*.pdf"))
            if not pdf_files:
                raise ValueError(f"No PDFs found in directory: {path}")
            for pdf_file in pdf_files:
                for record in parser.parse(str(pdf_file)):
                    yield record
        else:
            for record in parser.parse(str(path)):
                yield record

    return _iter()
