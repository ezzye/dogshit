# Module Overview

This document outlines the major components of the project.

## Backend

- FastAPI service located in `backend/`.
- Exposes endpoints for uploads, classification, rules, and report generation.
- Uses SQLite via SQLModel for persistence and HMAC-signed URLs for access control.
- Integrates with language models through the pluggable adapter in `backend/llm_adapter.py`.

## Frontend

- Vite + React + TypeScript + Tailwind located in `frontend/`.
- Presents the upload → progress → results flow and optional rules editor.
- Communicates with the API and provides Playwright end-to-end tests.

## Extractor

- CLI in `bankcleanr/` parses PDF statements with a registry of bank-specific parsers.
- Masks PII and writes `transaction_v1.jsonl` files for analysis.
- Packaged into standalone binaries via `poetry run bankcleanr build` using PyInstaller.
