"""Analytics utilities for spending summaries.

This module computes monthly totals, detects recurring
charges, highlights overspending patterns and generates
summary outputs validated against the summary_v1 schema.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any, Dict, Iterable, List, Optional

import jsonschema

BASE_DIR = Path(__file__).resolve().parent.parent
CATEGORIES_PATH = BASE_DIR / "data" / "taxonomy" / "categories.json"
SCHEMA_PATH = BASE_DIR / "schemas" / "summary_v1.json"


def load_categories(path: Path = CATEGORIES_PATH) -> List[str]:
    """Load canonical category list from JSON file."""
    with path.open() as f:
        return json.load(f)


def validate_rule_categories(
    rules: Iterable[Dict[str, Any] | Any], categories: Optional[List[str]] = None
) -> None:
    """Ensure rules use categories from the sanctioned taxonomy."""
    categories_set = set(categories or load_categories())

    def _cat(rule: Any) -> str | None:
        if isinstance(rule, dict):
            return rule.get("action", {}).get("category")
        return getattr(rule.action, "category", None)

    unknown = {c for r in rules if (c := _cat(r)) and c not in categories_set}
    if unknown:
        raise ValueError(f"Unknown categories: {sorted(unknown)}")


def compute_monthly_totals(transactions: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate transaction amounts per YYYY-MM."""
    totals: Dict[str, float] = defaultdict(float)
    for tx in transactions:
        month = tx["date"][:7]
        totals[month] += float(tx["amount"])
    return dict(totals)


def _determine_cadence(days: int) -> Optional[str]:
    if 6 <= days <= 8:
        return "weekly"
    if 28 <= days <= 31:
        return "monthly"
    if 85 <= days <= 100:
        return "quarterly"
    if 355 <= days <= 375:
        return "yearly"
    return None


def detect_recurring(
    transactions: Iterable[Dict[str, Any]], amount_tolerance: float = 0.1
) -> List[Dict[str, Any]]:
    """Identify recurring transactions grouped by merchant.

    A recurring series requires at least three transactions with a
    recognised cadence and amounts within ``amount_tolerance`` of the
    average amount.
    """

    by_merchant: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for tx in transactions:
        by_merchant[tx["merchant_signature"]].append(tx)

    recurring: List[Dict[str, Any]] = []
    for merchant, txs in by_merchant.items():
        txs.sort(key=lambda t: t["date"])
        if len(txs) < 3:
            continue

        intervals = [
            (datetime.fromisoformat(txs[i]["date"]) - datetime.fromisoformat(txs[i - 1]["date"]))
            .days
            for i in range(1, len(txs))
        ]
        cadence = _determine_cadence(round(mean(intervals)))
        if not cadence:
            continue

        amounts = [abs(float(t["amount"])) for t in txs]
        avg_amount = mean(amounts)
        if any(abs(a - avg_amount) > amount_tolerance * abs(avg_amount) for a in amounts):
            continue

        recurring.append(
            {
                "merchant": merchant,
                "cadence": cadence,
                "avg_amount": avg_amount,
                "median_amount": median(amounts),
                "amount_stddev": pstdev(amounts) if len(amounts) > 1 else 0.0,
                "count": len(txs),
                "first_seen": txs[0]["date"],
                "last_seen": txs[-1]["date"],
                "last_amount": amounts[-1],
            }
        )

    return recurring


def _percentile(data: List[float], pct: float) -> float:
    if not data:
        return 0.0
    data_sorted = sorted(data)
    k = (len(data_sorted) - 1) * pct / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data_sorted[int(k)]
    return data_sorted[f] + (data_sorted[c] - data_sorted[f]) * (k - f)


def detect_overspending(
    transactions: Iterable[Dict[str, Any]], recurring: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    """Flag overspending based on three heuristics."""
    highlights: List[str] = []

    # 1. Category month-over-month increase ≥ 30%
    cat_month: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for tx in transactions:
        cat = tx.get("category")
        if not cat:
            continue
        month = tx["date"][:7]
        cat_month[cat][month] += abs(float(tx["amount"]))

    for cat, months in cat_month.items():
        items = sorted(months.items())
        if len(items) >= 3:
            for i in range(1, len(items)):
                prev_total = items[i - 1][1]
                curr_total = items[i][1]
                if prev_total != 0 and curr_total >= 1.3 * prev_total:
                    pct = (curr_total - prev_total) / abs(prev_total) * 100
                    highlights.append(
                        f"Category {cat} up {pct:.0f}% in {items[i][0]}"
                    )
                    break

    # 2. Merchant monthly total exceeds 75th percentile
    merch_month: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for tx in transactions:
        merchant = tx["merchant_signature"]
        month = tx["date"][:7]
        merch_month[merchant][month] += abs(float(tx["amount"]))

    for merchant, months in merch_month.items():
        totals = list(months.values())
        if len(totals) >= 3:
            p75 = _percentile(totals, 75)
            for month, total in months.items():
                if total > p75:
                    highlights.append(
                        f"Merchant {merchant} spent {total:.2f} in {month} exceeding 75th percentile"
                    )
                    break

    # 3. Recurring charge increased by ≥15% vs median
    if recurring:
        for rec in recurring:
            if rec["last_amount"] > 1.15 * rec["median_amount"]:
                pct = (rec["last_amount"] / rec["median_amount"] - 1) * 100
                highlights.append(
                    f"Recurring {rec['merchant']} increased {pct:.0f}%"
                )

    return highlights


def generate_summary(
    transactions: List[Dict[str, Any]],
    job_id: str,
    user_id: str,
    period: Dict[str, str],
    currency: str = "GBP",
    output_dir: Path | None = None,
) -> Dict[str, Any]:
    """Generate summary_v1 JSON and CSV outputs for the given transactions."""
    output_dir = output_dir or Path.cwd()

    categories = load_categories()

    income = sum(float(t["amount"]) for t in transactions if float(t["amount"]) > 0)
    expenses = sum(float(t["amount"]) for t in transactions if float(t["amount"]) < 0)
    totals = {"income": income, "expenses": expenses, "net": income + expenses}

    # category breakdown
    cat_totals: Dict[str, Dict[str, Any]] = {
        c: {"total": 0.0, "count": 0, "merchants": set()} for c in categories
    }
    for tx in transactions:
        cat = tx.get("category")
        if cat in cat_totals:
            amt = float(tx["amount"])
            cat_totals[cat]["total"] += amt
            cat_totals[cat]["count"] += 1
            cat_totals[cat]["merchants"].add(tx["merchant_signature"])

    categories_out = [
        {
            "name": name,
            "total": data["total"],
            "count": data["count"],
            "sample_merchants": sorted(list(data["merchants"]))[:3],
        }
        for name, data in cat_totals.items()
        if data["count"] > 0
    ]

    recurring = detect_recurring(transactions)
    overspending = detect_overspending(transactions, recurring)

    summary: Dict[str, Any] = {
        "job_id": job_id,
        "user_id": user_id,
        "period": period,
        "currency": currency,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "totals": totals,
        "categories": categories_out,
        "recurring": [
            {
                k: v
                for k, v in r.items()
                if k not in {"median_amount", "last_amount"}
            }
            for r in recurring
        ],
        "highlights": {"overspending": overspending, "anomalies": []},
    }

    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    jsonschema.validate(summary, schema)

    # write files
    (output_dir / "summary_v1.json").write_text(json.dumps(summary, indent=2))

    with (output_dir / "summary.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "total", "count"])
        for cat in categories_out:
            writer.writerow([cat["name"], cat["total"], cat["count"]])

    return summary
