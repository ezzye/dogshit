"""High level extraction helpers."""
from __future__ import annotations

from typing import Dict, List

from .parsers import PARSER_REGISTRY


def extract_transactions(
    pdf_path: str, bank: str = "barclays"
) -> List[Dict[str, str | None]]:
    """Extract transactions from a PDF statement using the configured parser."""
    try:
        parser_cls = PARSER_REGISTRY[bank]
    except KeyError as exc:
        available = ", ".join(sorted(PARSER_REGISTRY))
        raise ValueError(
            f"Unsupported bank '{bank}'. Available banks: {available}"
        ) from exc
    parser = parser_cls()
    return parser.parse(pdf_path)
