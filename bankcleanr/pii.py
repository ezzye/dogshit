"""Utilities for masking personally identifiable information."""
from __future__ import annotations
import re

_SORT_CODE_RE = re.compile(r"\b\d{2}-\d{2}-\d{2}\b")
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,}\b")
_PAN_RE = re.compile(r"\b\d{12,19}\b")

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

def mask_pii(text: str) -> str:
    """Mask common PII patterns in the given text."""
    for masker in (_mask_sort_code, _mask_iban, _mask_pan):
        text = masker(text)
    return text
