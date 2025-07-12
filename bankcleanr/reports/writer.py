from pathlib import Path
import csv
from typing import Iterable, List
from dataclasses import asdict, is_dataclass
import yaml

from bankcleanr.analytics import calculate_savings, totals_by_type
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from .disclaimers import GLOBAL_DISCLAIMER


def _load_cancellation_data(categories: Iterable[str] | None = None) -> List[List[str]]:
    """Return cancellation instructions as a table filtered by ``categories``."""
    data_path = Path(__file__).resolve().parents[1] / "data" / "cancellation.yml"
    info = yaml.safe_load(data_path.read_text()) or {}
    rows = [["Service", "URL", "Phone", "Email"]]

    wanted = None
    if categories:
        wanted = {c.lower() for c in categories}

    for service, details in info.items():
        if wanted is not None and service.lower() not in wanted:
            continue
        rows.append([
            service,
            details.get("url", ""),
            details.get("phone", ""),
            details.get("email", ""),
        ])
    return rows


def _unpack_rec(tx):
    """Return transaction dict and optional recommendation data."""
    if hasattr(tx, "transaction") and hasattr(tx, "action"):
        rec = tx
        t = rec.transaction
        if is_dataclass(t):
            t = asdict(t)
        info = rec.info or {}
        return (
            {
                "date": t.get("date", ""),
                "description": t.get("description", ""),
                "amount": t.get("amount", ""),
                "balance": t.get("balance", ""),
            },
            rec.category,
            rec.action,
            info.get("url", ""),
            info.get("email", ""),
            info.get("phone", ""),
        )
    else:
        if is_dataclass(tx):
            tx = asdict(tx)
        return (
            {
                "date": tx.get("date", ""),
                "description": tx.get("description", ""),
                "amount": tx.get("amount", ""),
                "balance": tx.get("balance", ""),
            },
            "",
            "",
            "",
            "",
            "",
        )


def write_pdf_summary(transactions: Iterable, output: str, categories: Iterable[str] | None = None) -> Path:
    """Write a PDF summary with transactions and cancellation info."""
    path = Path(output)
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()

    tx_rows: List[List[str]] = [
        [
            "date",
            "description",
            "amount",
            "balance",
            "category",
            "action",
            "url",
            "email",
            "phone",
        ]
    ]
    gathered_cats: set[str] = set()
    for tx in transactions:
        t, cat, act, url, email, phone = _unpack_rec(tx)
        if categories is None and cat:
            gathered_cats.add(cat)
        tx_rows.append([
            t["date"],
            Paragraph(str(t["description"]), styles["Normal"]),
            t["amount"],
            t["balance"],
            cat,
            act,
            url,
            email,
            phone,
        ])
    if categories is None:
        categories = sorted(gathered_cats)

    elements = [Paragraph("Transactions", styles["Heading2"])]

    col_widths = [
        doc.width * 0.1,  # date
        doc.width * 0.35,  # description
        doc.width * 0.08,  # amount
        doc.width * 0.08,  # balance
        doc.width * 0.1,  # category
        doc.width * 0.06,  # action
        doc.width * 0.1,  # url
        doc.width * 0.1,  # email
        doc.width * 0.13,  # phone
    ]

    table = Table(tx_rows, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    # Cancellation appendix
    elements.append(Paragraph("How to cancel", styles["Heading2"]))
    cancel_table = Table(_load_cancellation_data(categories))
    cancel_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    elements.append(cancel_table)

    # Summary figures
    savings = calculate_savings(transactions)
    totals = totals_by_type(transactions)
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(
        Paragraph(f"Potential savings if cancelled: {savings:.2f}", styles["Normal"])
    )
    if totals:
        elements.append(Paragraph("Totals by type:", styles["Heading3"]))
        for name, total in totals.items():
            elements.append(Paragraph(f"- {name}: {total:.2f}", styles["Normal"]))

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(GLOBAL_DISCLAIMER, styles["Normal"]))

    doc.build(elements)
    return path


def format_terminal_summary(transactions: Iterable, categories: Iterable[str] | None = None) -> str:
    """Return a formatted text summary suitable for terminal output."""
    lines: List[str] = [
        "date | description | amount | balance | category | action | url | email | phone"
    ]

    gathered_cats: set[str] = set()
    for tx in transactions:
        t, cat, act, url, email, phone = _unpack_rec(tx)
        if categories is None and cat:
            gathered_cats.add(cat)
        line = " | ".join(
            [
                str(t["date"]),
                str(t["description"]),
                str(t["amount"]),
                str(t["balance"]),
                cat,
                act,
                url,
                email,
                phone,
            ]
        )
        lines.append(line)

    if categories is None:
        categories = sorted(gathered_cats)

    lines.append("")
    lines.append("How to cancel:")
    for row in _load_cancellation_data(categories)[1:]:
        service, url, phone, email = row
        info = ", ".join(filter(None, [url, phone, email]))
        lines.append(f"- {service}: {info}")

    savings = calculate_savings(transactions)
    totals = totals_by_type(transactions)

    lines.append("")
    lines.append(f"Potential savings if cancelled: {savings:.2f}")
    if totals:
        lines.append("Totals by type:")
        for name, total in totals.items():
            lines.append(f"- {name}: {total:.2f}")

    lines.append("")
    lines.append(GLOBAL_DISCLAIMER)
    return "\n".join(lines)


def write_summary(transactions: Iterable, output: str):
    """Write a summary in CSV or PDF format or return terminal text."""
    txs = list(transactions)
    cats = [c for _, c, _, _, _, _ in map(_unpack_rec, txs) if c]

    if output == "terminal":
        return format_terminal_summary(txs, cats)

    ext = Path(output).suffix.lower()
    if ext == ".pdf":
        return write_pdf_summary(txs, output, cats)

    # default to CSV
    path = Path(output)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date",
            "description",
            "amount",
            "balance",
            "category",
            "action",
            "url",
            "email",
            "phone",
        ])
        for tx in txs:
            t, cat, act, url, email, phone = _unpack_rec(tx)
            writer.writerow([
                t["date"],
                t["description"],
                t["amount"],
                t["balance"],
                cat,
                act,
                url,
                email,
                phone,
            ])
        writer.writerow([])
        writer.writerow([GLOBAL_DISCLAIMER])
    return path
