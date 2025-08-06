| Step | Area                       | Key Objectives | Status      | Owner | Notes / Next Actions | Target Date |
| ---- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ----- | -------------------------------------------------------------------- | ----------- |
| 0    | Foundation & Safety Net    | ✅ Reliable test harness (pytest + behave)  <br>✅ CI (lint, mypy, unit, BDD, container builds) <br>✅ Remove dead code & obsolete tests | Complete    | —     | Dead modules removed |             |
| 1    | Desktop Extractor          | • PDF parsers (Barclays required; HSBC/Lloyds optional) <br>• Mask PII (sort code, IBAN, PAN last4, etc.) <br>• Output JSONL per `transaction_v1.json` <br>• PyInstaller builds (Win/macOS) | In Progress | —     | Barclays parser & CLI extraction implemented; extend parser registry |             |
| 2    | Backend Skeleton           | • Endpoints: upload, status, download (summary/report), rules, classify <br>• SQLite persistence (SQLModel) <br>• Magic‑link auth (dev bypass) <br>• Signed URLs (time‑limited HMAC) <br>• Upload limit 100 MB; MIME `application/x-ndjson`, `text/plain`, optional gzip | In Progress | —     | Endpoints /upload, /status, /download, /rules, /classify; magic-link token auth (dev bypass); upload validation: MIME types, 100 MB limit, optional gzip |             |
| 3    | Rules Engine               | • Implement `heuristic_rule_v1.json` <br>• Merge global & per‑user rules (per‑user override) <br>• Precedence: priority → confidence → version/updated_at <br>• Versioning: monotonic integer | In Progress |       | Merge global & per-user rule sets; add tests for precedence and versioning |             |
| 4    | LLM Classification Service | • OpenAI‑compatible adapter (batching, retries, cost guardrails) <br>• Normalised merchant signature (lowercase, strip punctuation/diacritics, collapse whitespace, drop suffixes/prefixes, trim dynamic digits) <br>• Auto‑learn rules when confidence ≥ 0.85; overwrite only if ≥ 0.95 and scope not narrower | Not Started |       | Log costs per job & daily roll‑up; enforce MAX_DAILY_COST_GBP (classification & report budgets) |             |
| 5    | Frontend MVP               | • Vite + React + TS + Tailwind + shadcn/ui <br>• Views: Upload → Progress → Results (download analysis & PDF) <br>• Optional rules view + “Suggest a correction” POST /feedback <br>• E2E tests (Playwright) | Not Started |       | |             |
| 6    | Analytics & Summarisation  | • `analytics.py`: monthly totals, recurring detection (merchant + periodicity ±10% amount variance), overspending (MoM ≥ 30%, merchant 75th percentile, recurring +15%) <br>• Canonical categories in `data/taxonomy/categories.json` <br>• Output `summary_v1.json` & CSV | Not Started |       | |             |
| 7    | Savings Report Generation  | • LLM returns structured JSON + Markdown body <br>• HTML → PDF with WeasyPrint; stylesheet A4 accessible <br>• Cancellation links: curated `data/cancellations.json` + validated LLM suggestions | Not Started |       | |             |
| 8    | Packaging & Orchestration  | • `docker-compose.yml` for api, worker, redis, frontend, db, storage volume <br>• Make targets: up/down/logs/seed/test/e2e (seed idempotent) <br>• PyInstaller artefacts published for Win & macOS per release tag | Not Started |       | |             |
| 9    | Docs & Hand-off            | • Update README (quick start), MODULES.md (architecture), CHANGELOG.md <br>• PR checklist & screencasts/notes for manual checks | Not Started |       | |             |

To be read in conjunction with notes.md and REFACTOR_PLAN.md

This is the contract that needs to be fulfilled.  This contains the goal:

Deliverable: DS/dogshit MVP comprising cross-platform PyInstaller extractor binaries and a Chrome-only WCAG 2.1 AA FastAPI + SQLite web app; must include: an automatic heuristic-first/LLM-second classification loop that updates heuristics in SQLite and generates a ≤30 s, ≤5 MB WeasyPrint savings PDF from PII-masked ISO-formatted `transaction_v1.json`; hard constraint: the user secures the detailed report in exactly **three clicks**.

This is what is expected.  The knowns:

### Current **Knowns**

1. **Desktop Extractor Binaries**

    * Built with **PyInstaller** (one-file) for **macOS (Intel & Apple Silicon), Windows 10/11 x64, and Linux x86-64**.
    * Unsigned builds are acceptable for the MVP.
    * Distributed via **GitHub Releases** with published **SHA-256 checksums** (GPG signatures optional).

2. **Parsing & Masking**

    * Processes **100 PDF pages ≤ 2 minutes using ≤ 1 GB RAM** on a typical laptop.
    * Outputs PII-masked `transaction_v1.jsonl` where:

        * Dates → **ISO 8601 `YYYY-MM-DD`**
        * Amounts → **signed decimal string `"-123.45"`** (GBP, no symbol)
        * Sort code / account / IBAN / PAN → masked as `****1234`
        * User name & other personal strings → replaced with `"XX MASKED NAME XX"`
    * Masking applied **during extraction**, so no raw PII is uploaded or logged.

3. **Analysis Pipeline**

    * **First pass:** heuristic rule engine stored in **SQLite**.
    * **Second pass:** **LLM** (cost-capped at **£5/report**) refines labels, totals, and **automatically writes updated heuristics back to the same SQLite DB**—no human review loop.
    * Web layer supplies LLM with:

        * Individual labelled transactions
        * Aggregated totals per label
        * Additional context for report generation.

4. **Web Application**

    * **Backend:** **FastAPI** + SQLite.
    * **Frontend:** Chrome-only (MVP), meets **WCAG 2.1 AA** accessibility.
    * **Three-click UX constraint**

        1. **Download** the desktop parsing tool.
        2. **Upload** the JSONL & start analysis.
        3. **Download** the generated report.
    * Generates savings/financial report via **WeasyPrint**:

        * PDF produced in **≤ 30 seconds**
        * File size **≤ 5 MB**.

5. **Output Artifacts**

    * **Savings report**: PDF (and HTML view) with detailed insights, cancellations list, labelled spending breakdown.
    * **Updated heuristic rules** persisted in SQLite.

6. **Standards & Testing**

    * Python 3.12, pytest + BDD + E2E tests; TDD workflow.
    * Privacy & security guardrails (no secrets in repo, masking enforced).
    * Performance, cost, and accessibility targets as stated above.

These constitute the authoritative **“Knowns”** for the locked MVP contract.

Please ensure contract is met.  The task is not complete until all above conditions implemented.

