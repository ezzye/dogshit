from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Dict

from .recommendation import Recommendation

# Map transaction categories to high level types
CATEGORY_TYPES = {
    "spotify": "entertainment",
    "netflix": "entertainment",
    "amazon prime": "entertainment",
    "icloud": "cloud",
    "dropbox": "cloud",
}


def _parse_amount(amount: str) -> Decimal:
    """Return Decimal value from transaction amount string."""
    try:
        return Decimal(amount)
    except Exception:
        return Decimal("0")


def _get_attr(obj, name, default=""):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def calculate_savings(recommendations: Iterable[Recommendation]) -> Decimal:
    """Return total potential savings for recommendations marked Cancel."""
    total = Decimal("0")
    for rec in recommendations:
        action = _get_attr(rec, "action").lower()
        if action == "cancel":
            if isinstance(rec, Recommendation):
                amt_str = rec.transaction.amount
            else:
                amt_str = _get_attr(rec, "amount", "0")
            amt = _parse_amount(amt_str)
            if amt < 0:
                total += abs(amt)
    return total


def totals_by_type(recommendations: Iterable[Recommendation]) -> Dict[str, Decimal]:
    """Group transactions by high level type and total their amounts."""
    totals: Dict[str, Decimal] = {}
    for rec in recommendations:
        category = _get_attr(rec, "category", "other").lower()
        group = CATEGORY_TYPES.get(category, "other")
        if isinstance(rec, Recommendation):
            amt_str = rec.transaction.amount
        else:
            amt_str = _get_attr(rec, "amount", "0")
        amt = _parse_amount(amt_str)
        if amt < 0:
            totals[group] = totals.get(group, Decimal("0")) + abs(amt)
    return totals


def summarize_by_description(transactions: Iterable) -> Dict[str, Decimal]:
    """Group transactions by description and total their amounts."""
    totals: Dict[str, Decimal] = {}
    for tx in transactions:
        desc = _get_attr(tx, "description", "")
        amt_str = _get_attr(tx, "amount", "0")
        amt = _parse_amount(amt_str)
        totals[desc] = totals.get(desc, Decimal("0")) + abs(amt)
    return totals
