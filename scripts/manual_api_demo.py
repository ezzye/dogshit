#!/usr/bin/env python
"""Demonstrate the API workflow using signed URLs."""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests

from backend.signing import generate_signed_url

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")


def main() -> None:
    sample = [
        {"date": "2024-01-01", "description": "coffee", "amount": -3.5, "type": "debit"},
        {"date": "2024-01-02", "description": "salary", "amount": 1000, "type": "credit"},
    ]
    ndjson = "\n".join(json.dumps(line) for line in sample)
    resp = requests.post(
        f"{BASE_URL}/upload",
        data=ndjson,
        headers={"Content-Type": "application/x-ndjson"},
    )
    resp.raise_for_status()
    job_id = resp.json()["job_id"]

    resp = requests.post(f"{BASE_URL}/classify", json={"job_id": job_id})
    resp.raise_for_status()

    summary_url = generate_signed_url(f"/download/{job_id}/summary")
    summary = requests.get(f"{BASE_URL}{summary_url}")
    summary.raise_for_status()
    print("Summary:", summary.text)

    report_meta = requests.get(f"{BASE_URL}/report/{job_id}")
    report_meta.raise_for_status()
    report_url = report_meta.json()["url"]
    report = requests.get(f"{BASE_URL}{report_url}")
    report.raise_for_status()
    Path("report.pdf").write_bytes(report.content)
    print("Report saved to report.pdf")


if __name__ == "__main__":
    main()
