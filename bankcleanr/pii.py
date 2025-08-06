"""Utilities for masking personally identifiable information."""
from __future__ import annotations

import re
from typing import Iterable, Tuple

from rapidfuzz import fuzz

_SORT_CODE_RE = re.compile(r"\b\d{2}-\d{2}-\d{2}\b")
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,}\b")
_PAN_RE = re.compile(r"\b\d{12,19}\b")

_MASKED_NAME = "XX MASKED NAME XX"


def _mask_sort_code(text: str) -> str:
    return _SORT_CODE_RE.sub("XX-XX-XX", text)


def _mask_iban(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        value = match.group(0)
        if len(value) <= 8:
            return value
        return value[:4] + "X" * (len(value) - 8) + value[-4:]

    return _IBAN_RE.sub(repl, text)


def _mask_pan(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        value = match.group(0)
        return "X" * (len(value) - 4) + value[-4:]

    return _PAN_RE.sub(repl, text)


def _find_fuzzy_span(text: str, name: str, threshold: int) -> Tuple[int, int] | None:
    """Return the start/end span of the best fuzzy match or ``None``."""
    name_len = len(name)
    best_score = threshold
    best_span: Tuple[int, int] | None = None
    for start in range(len(text)):
        for end in range(start + max(1, name_len - 2), min(len(text), start + name_len + 2) + 1):
            score = fuzz.ratio(name, text[start:end])
            if score >= best_score:
                best_score = score
                best_span = (start, end)
    return best_span


def _mask_names(text: str, names: Iterable[str], threshold: int = 85) -> str:
    for name in names:
        if not name:
            continue
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        text = pattern.sub(_MASKED_NAME, text)
        lower_name = name.lower()
        while True:
            span = _find_fuzzy_span(text.lower(), lower_name, threshold)
            if span is None:
                break
            start, end = span
            text = text[:start] + _MASKED_NAME + text[end:]
    return text


def mask_pii(text: str, names: Iterable[str] | None = None) -> str:
    """Mask common PII patterns and supplied names in the given text."""
    for masker in (_mask_sort_code, _mask_iban, _mask_pan):
        text = masker(text)
    if names:
        text = _mask_names(text, names)
    return text
