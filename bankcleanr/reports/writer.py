from pathlib import Path
import csv
from typing import Iterable, List
from dataclasses import asdict, is_dataclass
import yaml
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

from .disclaimers import GLOBAL_DISCLAIMER


def _load_cancellation_data() -> List[List[str]]:
    """Return cancellation instructions as a table."""
    data_path = Path(__file__).resolve().parents[1] / "data" / "cancellation.yml"
    info = yaml.safe_load(data_path.read_text())
    rows = [["Service", "URL", "Phone", "Email"]]
    for service, details in info.items():
        rows.append([
            service,
            details.get("url", ""),
            details.get("phone", ""),
            details.get("email", ""),
        ])
    return rows


def write_pdf_summary(transactions: Iterable, output: str) -> Path:
    """Write a PDF summary with transactions and cancellation info."""
    path = Path(output)
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()

    tx_rows: List[List[str]] = [["date", "description", "amount", "balance"]]
    for tx in transactions:
        if is_dataclass(tx):
            tx = asdict(tx)
        tx_rows.append([
            tx.get("date", ""),
            tx.get("description", ""),
            tx.get("amount", ""),
            tx.get("balance", ""),
        ])

    elements = [Paragraph("Transactions", styles["Heading2"])]
    table = Table(tx_rows)
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
    cancel_table = Table(_load_cancellation_data())
    cancel_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
    )
    elements.append(cancel_table)

    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(GLOBAL_DISCLAIMER, styles["Normal"]))

    doc.build(elements)
    return path


def format_terminal_summary(transactions: Iterable) -> str:
    """Return a formatted text summary suitable for terminal output."""
    lines: List[str] = ["date | description | amount | balance"]
    for tx in transactions:
        if is_dataclass(tx):
            tx = asdict(tx)
        line = " | ".join(
            [
                str(tx.get("date", "")),
                str(tx.get("description", "")),
                str(tx.get("amount", "")),
                str(tx.get("balance", "")),
            ]
        )
        lines.append(line)

    lines.append("")
    lines.append("How to cancel:")
    for row in _load_cancellation_data()[1:]:
        service, url, phone, email = row
        info = ", ".join(filter(None, [url, phone, email]))
        lines.append(f"- {service}: {info}")

    lines.append("")
    lines.append(GLOBAL_DISCLAIMER)
    return "\n".join(lines)


def write_summary(transactions: Iterable, output: str):
    """Write a summary in CSV or PDF format or return terminal text."""
    if output == "terminal":
        return format_terminal_summary(transactions)

    ext = Path(output).suffix.lower()
    if ext == ".pdf":
        return write_pdf_summary(transactions, output)

    # default to CSV
    path = Path(output)
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "description", "amount", "balance"])
        for tx in transactions:
            if is_dataclass(tx):
                tx = asdict(tx)
            writer.writerow([
                tx.get("date"),
                tx.get("description"),
                tx.get("amount"),
                tx.get("balance"),
            ])
        writer.writerow([])
        writer.writerow([GLOBAL_DISCLAIMER])
    return path
