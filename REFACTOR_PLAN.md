```markdown
# file: REFACTOR_PLAN.md
# Bankcleanr — Guided Refactor & Feature-Growth Plan
*A step-by-step playbook for an AI coding agent (e.g. Codex) to transform the current “bankcleanr” prototype into a polished two-part product for everyday consumers.*

---

## 0  |  Purpose of this Document
*   **Audience** – an automated coding agent following the conventions in `AGENTS.md` (write tests first, incremental uploads).
*   **Scope** – covers **both** the desktop **Extractor** (offline, redacts statements) **and** the hosted **Web App** (heuristic editor ➜ LLM labelling ➜ analytics ➜ report download).
*   **Outcome** – the only planning file needed alongside `README.md` and `AGENTS.md`.

Keep each numbered section self-contained so the agent can work through it in order, committing after every green test run.

---

## 1  |  Foundation – Clean Up & Safety Net
1. **Boot the test harness**  
   * Ensure `pytest`, `behave`, `coverage` already run via `make test`.  
   * **TASK**: Fix any red/red-X tests; stub failing externals so the suite goes green again.
2. **Add continuous integration** (if missing)  
   * GitHub Actions workflow: `make lint`, `make test`, artefact upload.
3. **Snapshot current behaviour**  
   * Freeze a minimal “golden path” BDD feature (CLI → parse sample PDF → CSV summary).  
   * This guards against regressions during refactor.

---

## 2  |  Desktop Extractor (Stage 1 of the Consumer Flow)
Goal | *Parse, mask & export a lightweight file for upload.*

| Sub-step | Increment | Key Acceptance Tests |
|---|---|---|
| 2-A | **Robust PDF parsing**<br>Finish `io/pdf/generic.py`; add bank-specific overrides. | *Given* a sample Barclays PDF,<br>*When* I run `bankcleanr parse file.pdf`,<br>*Then* 20 ± 2 transactions are returned. |
| 2-B | **Redaction**<br>Implement `transaction.mask_sensitive_fields()`. | Account numbers replaced with `****1234`. |
| 2-C | **Portable export**<br>Write masked data to **JSONL** (one txn / line). | File validates against `schemas/transaction_v1.json`. |
| 2-D | **Packaging for non-tech users**<br>PyInstaller “one-file” builds for Win/macOS (see `component_overview.md`). | Running the `.exe` shows a GUI/CMD prompt and produces the JSONL. |

*Commit after each cell in the table passes.*

---

## 3  |  Backend Skeleton (Stage 2 & 3)
Goal | *Receive upload, store per-user heuristics, enrich unlabeled rows via LLM.*

1. **Spin up FastAPI** (`backend/`) with `/upload`, `/heuristics`, `/classify`, `/summary` routes.  
2. **Persistence layer** – start with SQLite + SQLModel; one DB per env.  
3. **Auth** – email + magic-link (Passkey ready).  
4. **Containerise** (`Dockerfile`, `docker-compose.yml`).  
5. **Tests** – component tests hit the real HTTP API with `httpx.AsyncClient`.

---

## 4  |  Heuristic Editor UI (Stage 2)
Goal | *Let users review & tweak the rule table in-browser.*

1. **React + TypeScript SPA** inside `/frontend`.  
2. Table grid (shadcn/ui DataTable) with CRUD ops, CSV import/export.  
3. Auto-save to `/heuristics` API; optimistic updates.  
4. Cypress E2E: “User uploads JSONL → edits a rule → saves → sees confirmation”.

---

## 5  |  LLM Classification Service (Stage 3)
Goal | *Merge user rules, global rules & LLM suggestions.*

| Task | Detail |
|------|--------|
| 5-A | **Prompt template** – lives in `rules/prompts.py`; parameterise `{{txn.description}}`, `{{user_heuristics}}`, `{{global_heuristics}}`. |
| 5-B | **Adapter refactor** – unify `llm/*` classes under `AbstractAdapter.classify_transactions(batch)`. |
| 5-C | **Retry & cost guardrails** – exponential back-off, max £/day env var. |
| 5-D | **Auto-learning** – when LLM returns a *new* rule, enqueue it for human review in the UI. |
| 5-E | **Unit tests** – mock LLM, assert JSON schema of response. |

---

## 6  |  Analytics & Summarisation (Stage 4)
1. **`analytics.py` enhancements** – new functions: `monthly_totals`, `recurring_flags`.  
2. **Summary builder** – produce a `Summary` object (transactions + charts meta).  
3. **Tests** – snapshot comparison of a synthetic dataset.

---

## 7  |  Savings Report Generator (Stage 5)
1. **Prompt** – feed the summary + cancellation map into LLM (small context-optimised call).  
2. **Post-processing** – ensure bullets: *who to contact*, *saving/month*, *cancellation channel*.  
3. **PDF export** – `reports/writer.py` gains `write_full_report(summary, pdf_path)`.  
4. **BDD feature** – “Given mocked LLM returns X, PDF contains ‘Total annual saving £###’”.

---

## 8  |  Frontend Download Flow (Stage 6)
1. **Progress indicator** while backend crunches.  
2. **Download button** with signed URL (10 min expiry).  
3. **Accessibility pass** – keyboard nav + aria-labels.  
4. Playwright E2E to assert file download & checksum.

---

## 9  |  Production Hardening
*   **Observability** – OpenTelemetry traces; console exporter in dev, OTLP in prod.  
*   **Rate-limit & quota** – per-user daily token cap.  
*   **Data retention** – auto-purge PII after N days (env configurable).  
*   **Signed builds** – follow `component_overview.md` for macOS notarisation & Windows EV cert.

---

## 10  |  Documentation & Hand-off
1. **Update `README.md`** with new CLI & web usage examples.  
2. **Architecture diagram** – regenerate Mermaid in `MODULES.md`.  
3. **Changelog** – keep `CHANGELOG.md` per Semantic Versioning.  
4. **Success checklist** (include in PR template):  
```

✅ builds & runs
✅ all tests pass
✅ docs / comments present

```

---

## Appendix A | Folder Layout After Refactor
```

bankcleanr/
cli.py
gui/                     ← optional local GUI
extractor/               ← redaction logic
backend/
app.py                   ← FastAPI
frontend/
src/
tests/
unit/
component/
features/
docker-compose.yml
pyproject.toml
README.md
AGENTS.md
REFACTOR\_PLAN.md   ← this file

```

---

## Appendix B | “Definition of Done” per Stage
1. **Green pipeline** – CI on main.  
2. **Binary release** – GitHub Release with artefact + SHA-256.  
3. **E2E demo** – screencast link in PR description.  
4. **Security scan** – `pip-audit` passes, no critical CVEs.

---

*Work through each numbered stage, committing only when all tests (unit + BDD + E2E) pass and coverage ≥ 90 %.*
```
