"""PDF statement parsers."""
from __future__ import annotations

import importlib
import pkgutil
import re
from typing import Dict, Iterable, Type

import pdfplumber

PARSER_REGISTRY: Dict[str, Type] = {}


def _load_parsers() -> Dict[str, Type]:
    registry: Dict[str, Type] = {}
    package = __name__
    for _, module_name, _ in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{package}.{module_name}")
        parser_cls = getattr(module, "Parser", None)
        if parser_cls is None:
            continue
        name = getattr(module, "BANK", module_name)
        registry[name] = parser_cls
        globals()[parser_cls.__name__] = parser_cls
    return registry


PARSER_REGISTRY = _load_parsers()


_DETECT_PATTERNS: Dict[str, Iterable[re.Pattern[str]]] = {
    "hsbc": [re.compile(r"hsbc", re.I)],
    "lloyds": [re.compile(r"lloyds", re.I)],
    "coop": [re.compile(r"co-?operative", re.I), re.compile(r"co-?op", re.I)],
    "barclays": [re.compile(r"barclays", re.I)],
}


def detect_bank(pdf_path: str) -> str:
    """Return the bank identifier for ``pdf_path``.

    Inspect the full text of the PDF and look for bank specific keywords.
    Currently recognises HSBC, Lloyds, Co-op and Barclays statements.
    """

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    for bank, patterns in _DETECT_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text):
                return bank
    raise ValueError("Unable to detect bank for PDF")


__all__ = [cls.__name__ for cls in PARSER_REGISTRY.values()] + ["PARSER_REGISTRY", "detect_bank"]
