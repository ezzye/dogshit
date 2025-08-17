#!/usr/bin/env python3
"""End-to-end demo that extracts statements and sends them to the API.

This script calls :func:`bankcleanr.extractor.extract_transactions` on a
provided directory of PDF statements, uploads the resulting NDJSON to the
running FastAPI backend, triggers classification, and downloads the enriched
transactions.  It repeats the process to demonstrate how cached rules reduce
LLM usage on subsequent runs.
"""
from __future__ import annotations

import argparse
import json
import time
from typing import Iterable

import httpx

from bankcleanr.extractor import extract_transactions
from backend.auth import generate_token


def _to_ndjson(records: Iterable[dict]) -> str:
    """Return records serialised as newline-delimited JSON."""
    return "\n".join(json.dumps(r) for r in records) + "\n"


def _upload(client: httpx.Client, ndjson: str) -> int:
    resp = client.post("/upload", content=ndjson, headers={"Content-Type": "application/x-ndjson"})
    resp.raise_for_status()
    return int(resp.json()["job_id"])


def _classify(client: httpx.Client, job_id: int, user_id: int) -> None:
    resp = client.post("/classify", json={"job_id": job_id, "user_id": user_id})
    resp.raise_for_status()


def _wait_completed(client: httpx.Client, job_id: int) -> None:
    while True:
        resp = client.get(f"/status/{job_id}")
        resp.raise_for_status()
        status = resp.json().get("status")
        if status == "completed":
            return
        if status == "failed":
            raise RuntimeError("classification failed")
        time.sleep(1)


def _transactions(client: httpx.Client, job_id: int) -> list[dict]:
    resp = client.get(f"/transactions/{job_id}")
    resp.raise_for_status()
    return list(resp.json())


def _costs(client: httpx.Client, job_id: int) -> dict:
    resp = client.get(f"/costs/{job_id}")
    resp.raise_for_status()
    return resp.json()


def _run_once(client: httpx.Client, ndjson: str, user_id: int) -> tuple[list[dict], dict]:
    job_id = _upload(client, ndjson)
    _classify(client, job_id, user_id)
    _wait_completed(client, job_id)
    txs = _transactions(client, job_id)
    costs = _costs(client, job_id)
    return txs, costs


def main() -> None:
    parser = argparse.ArgumentParser(description="End-to-end extraction and classification demo")
    parser.add_argument("pdf_dir", help="Directory containing PDF statements")
    parser.add_argument("--api", default="http://localhost:8000", help="Base URL of the FastAPI service")
    parser.add_argument("--user", type=int, default=1, help="User ID to associate with uploaded data")
    args = parser.parse_args()

    records = list(extract_transactions(args.pdf_dir))
    ndjson = _to_ndjson(records)

    token = generate_token("auth")
    headers = {"X-Auth-Token": token}

    with httpx.Client(base_url=args.api, headers=headers, timeout=None) as client:
        print("First run: uploading and classifying...")
        _txs, costs_first = _run_once(client, ndjson, args.user)
        print("LLM tokens used:", costs_first["total_tokens"])

        print("Second run: re-uploading to demonstrate learning...")
        _txs2, costs_second = _run_once(client, ndjson, args.user)
        print("LLM tokens used:", costs_second["total_tokens"])

        if costs_second["total_tokens"] < costs_first["total_tokens"]:
            print("Token usage reduced on second run – learning successful.")
        else:
            print("Token usage did not decrease; ensure caching is enabled.")

        print("Fetched", len(_txs2), "classified transactions.")


if __name__ == "__main__":
    main()
