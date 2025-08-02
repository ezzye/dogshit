Thanks—here are concrete answers and defaults so work can proceed without blocking. Where code-like artefacts are needed (e.g., schemas), I’ve included them so you can copy–paste.

DATA CONTRACTS

Will heuristic\_rule\_v1.json and summary\_v1.json follow JSON Schema?
Yes. Use JSON Schema (Draft 2020-12). Keep them alongside transaction\_v1.json in /schemas.

Proposed minimal schemas (MVP)

heuristic\_rule\_v1.json (used by the rules engine and auto-learning)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://bankcleanr/schemas/heuristic_rule_v1.json",
  "title": "Heuristic Rule v1",
  "type": "object",
  "required": ["id", "scope", "active", "match", "action", "provenance", "priority", "version", "confidence"],
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "scope": { "type": "string", "enum": ["global", "user"] },
    "owner_user_id": { "type": "string", "nullable": true },
    "active": { "type": "boolean", "default": true },
    "priority": { "type": "integer", "minimum": 0, "description": "Lower number = higher precedence" },
    "version": { "type": "integer", "minimum": 1 },
    "created_at": { "type": "string", "format": "date-time" },
    "updated_at": { "type": "string", "format": "date-time" },
    "provenance": { "type": "string", "enum": ["system", "llm", "user"] },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "title": { "type": "string" },
    "notes": { "type": "string" },

    "match": {
      "type": "object",
      "required": ["type", "pattern", "fields"],
      "properties": {
        "type": { "type": "string", "enum": ["exact", "contains", "regex", "signature"] },
        "pattern": { "type": "string" },
        "flags": { "type": "array", "items": { "type": "string", "enum": ["i", "m"] } },
        "fields": {
          "type": "array",
          "items": { "type": "string", "enum": ["description", "counterparty", "reference", "mcc", "merchant_signature"] },
          "minItems": 1
        }
      }
    },

    "action": {
      "type": "object",
      "required": ["category"],
      "properties": {
        "merchant_canonical": { "type": "string" },
        "label": { "type": "string" },
        "category": { "type": "string" },
        "subcategory": { "type": "string" }
      }
    },

    "examples": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "description": { "type": "string" },
          "amount": { "type": "number" },
          "date": { "type": "string", "format": "date" }
        }
      }
    }
  }
}
```

summary\_v1.json (output from analytics; the LLM report consumes this)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://bankcleanr/schemas/summary_v1.json",
  "title": "Analysis Summary v1",
  "type": "object",
  "required": ["job_id", "user_id", "period", "currency", "totals", "categories"],
  "properties": {
    "job_id": { "type": "string", "format": "uuid" },
    "user_id": { "type": "string" },
    "period": {
      "type": "object",
      "required": ["start", "end"],
      "properties": {
        "start": { "type": "string", "format": "date" },
        "end": { "type": "string", "format": "date" }
      }
    },
    "currency": { "type": "string", "default": "GBP" },
    "generated_at": { "type": "string", "format": "date-time" },

    "totals": {
      "type": "object",
      "required": ["income", "expenses", "net"],
      "properties": {
        "income": { "type": "number" },
        "expenses": { "type": "number" },
        "net": { "type": "number" }
      }
    },

    "categories": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "total", "count"],
        "properties": {
          "name": { "type": "string" },
          "total": { "type": "number" },
          "count": { "type": "integer" },
          "sample_merchants": { "type": "array", "items": { "type": "string" } }
        }
      }
    },

    "recurring": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["merchant", "cadence", "avg_amount", "count"],
        "properties": {
          "merchant": { "type": "string" },
          "cadence": { "type": "string", "enum": ["weekly", "monthly", "quarterly", "yearly"] },
          "avg_amount": { "type": "number" },
          "amount_stddev": { "type": "number" },
          "count": { "type": "integer" },
          "first_seen": { "type": "string", "format": "date" },
          "last_seen": { "type": "string", "format": "date" }
        }
      }
    },

    "highlights": {
      "type": "object",
      "properties": {
        "overspending": {
          "type": "array",
          "items": { "type": "string" }
        },
        "anomalies": {
          "type": "array",
          "items": { "type": "string" }
        }
      }
    }
  }
}
```

Should report\_v1.pdf have companion metadata for validation?
Yes. Produce a side-car JSON report\_meta\_v1.json that the pipeline validates before/after PDF generation.

Minimal report\_meta\_v1.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://bankcleanr/schemas/report_meta_v1.json",
  "title": "Report Meta v1",
  "type": "object",
  "required": ["job_id", "generated_at", "totals", "sections"],
  "properties": {
    "job_id": { "type": "string", "format": "uuid" },
    "generated_at": { "type": "string", "format": "date-time" },
    "currency": { "type": "string", "default": "GBP" },
    "totals": {
      "type": "object",
      "required": ["income", "expenses", "net", "estimated_annual_saving"],
      "properties": {
        "income": { "type": "number" },
        "expenses": { "type": "number" },
        "net": { "type": "number" },
        "estimated_annual_saving": { "type": "number" }
      }
    },
    "sections": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["heading"],
        "properties": {
          "heading": { "type": "string" },
          "link": { "type": "string", "format": "uri" }
        }
      }
    }
  }
}
```

STEP 0 – FOUNDATION

List of modules to retain vs. delete?
Retain: extractor/, backend/, frontend/, schemas/, tests/ (unit, component, features), docker files, pyproject.toml, README.md, REFACTOR\_PLAN.md, AGENTS.md.
Delete or archive: any experimental/, notebooks/, legacy/ parsers not referenced by CLI; unused scripts; deprecated adapters; old CI configs; redundant sample data. When in doubt, require one of: referenced by tests, imported by CLI/API, or documented as in-use.

Infer dead code via coverage and import graph. Use:
• Coverage with branch data to find never-hit code.
• Static import scan to flag modules with zero inbound edges.

BDD runner?
Continue with behave. It’s already in use, aligns with the current stepwise plan, and keeps cognitive load down.

STEP 1 – DESKTOP EXTRACTOR

Banks to support in MVP?
• Mandatory: Barclays PDF (sample already exists).
• Nice-to-have (quick wins): HSBC and Lloyds PDF (common UK formats).
• Out of scope for MVP: CSV flows (e.g., Monzo/Starling). We can add CSV adapters later.

PII fields to mask beyond account numbers
• Sort code, IBAN, card PAN (store only last 4), customer IDs, full name and address of the account holder, email, phone. Do NOT mask merchant names or merchant IDs.
• Keep a configurable allow-list (e.g., keep last 4 digits of IBAN/PAN).

Multi-page / multi-account PDFs?
• Yes, handle multi-page. Extract account metadata per statement and include account\_id on each transaction.
• If a single PDF contains multiple accounts, split internally by account section. The consolidated JSONL contains all transactions with account\_id for disambiguation.

Parser registry interface?
Use a small class-based API (future-proof) with optional auto-detect.

```python
class AbstractParser:
    bank = "generic"
    def can_parse(self, pdf_bytes: bytes) -> bool: ...
    def parse(self, pdf_bytes: bytes) -> list[Transaction]: ...

# registry
register_parser(AbstractParserSubclass)
select_parser(pdf_bytes) -> parser
```

PyInstaller cross-platform builds?
Yes—build Windows artefacts on Windows runners and macOS artefacts on macOS runners. Linux builds in CI are fine but not required for end-users.

STEP 2 – BACKEND SKELETON

Upload limits and MIME types?
• Max size: 100 MB per upload (JSONL compresses well; also accept gzip).
• MIME: application/x-ndjson, text/plain; accept application/gzip when Content-Encoding: gzip is present.
• Validate JSONL line-by-line against transaction\_v1.json.

Signed URLs in dev?
Implement time-limited HMAC tokens even locally (shared codepath). Default TTL 10 minutes. This avoids surprises later.

Magic-link auth and user storage?
Create a user record in SQLite. Dev mode supports a bypass header (X-Dev-User) and console “email” of the magic link. Tokens are single-use, short-lived (15 minutes).

STEP 3 – RULES ENGINE

Rule structure and match types?
Match types: exact, contains, regex, signature. Signature matches against the normalised merchant signature (see Step 4). Fields supported: description, counterparty, reference, mcc, merchant\_signature.

Precedence of global vs per-user?
Per-user rules always override global rules. Within the same scope, precedence resolves by:

1. lowest priority integer wins,
2. higher confidence wins,
3. newest version (version then updated\_at) wins.

Versioning?
Monotonic integer per rule (version) plus updated\_at timestamp. Preserve history rows (soft versioning) for auditability.

STEP 4 – LLM CLASSIFICATION SERVICE

First provider?
Start with an OpenAI-compatible adapter (fast to implement and broadly supported). Keep the adapter boundary clean so Anthropic/Gemini can be added later.

Normalised merchant signature (for caching & rules)?
• Lowercase,
• remove punctuation and diacritics,
• collapse whitespace,
• remove card suffixes (/####), reference IDs, and booking codes,
• strip leading bank prefixes (e.g., “POS ”, “CARD ”, “DD ”, “STO ”),
• trim trailing digits if they look like dynamic IDs (≥ 5 digits).
Store the derived merchant\_signature on each transaction.

Confidence thresholds and overwrites?
• Auto-learn new rule when confidence ≥ 0.85 and coverage looks general (pattern contains ≥ 6 alpha chars after normalisation).
• Validation pass may propose an improvement; auto-overwrite only when confidence ≥ 0.95 AND the new rule’s match scope is not narrower than the existing one. Always bump version and keep the prior as history.

Cost metrics and logging?
Log both per-job and per-day totals.
• Persist per-job in a costs table (job\_id, tokens\_in, tokens\_out, estimated\_cost\_gbp).
• Maintain a daily roll-up to enforce MAX\_DAILY\_COST\_GBP.
• Emit structured JSON logs; attach to job telemetry.

STEP 5 – FRONTEND MVP

Stack?
Vite + React + TypeScript, Tailwind + shadcn/ui, TanStack Query for data fetching. Keep it simple, fast, and testable.

“Suggest a correction”—where is it stored?
Send immediately to the backend (POST /feedback). Store in a feedback table with the original transaction fields and the user’s suggestion. A worker can turn accepted feedback into a per-user rule.

E2E framework?
Playwright (good parallelism and cross-browser; integrates well with CI). We’ll keep tests deterministic with seeded data.

STEP 6 – ANALYTICS AND SUMMARISATION

Categories—canonical list or derived?
Canonical list in a taxonomy file (e.g., data/taxonomy/categories.json): Income, Housing, Utilities, Groceries, Transport, Subscriptions, Entertainment, Health, Fees, Savings/Investments, Transfers/Internal. Rules map to these. The LLM may suggest categories for unknowns but we persist only once mapped to the canonical list.

Overspending highlights criteria?
MVP: flag when any of the following holds:
• Month-over-month increase ≥ 30% for a category (with ≥ 3 months of data),
• Single merchant’s monthly total exceeds its 75th percentile over the selected period,
• Recurring charge increased by ≥ 15% versus its median recurring amount.
(Thresholds are config defaults.)

Recurring detection—signals?
Merchant + periodicity, with amount variance tolerance (default ±10%). Accept cadences: weekly (6–8 days), monthly (28–31 days), quarterly (85–100 days), yearly (355–375 days).

STEP 7 – SAVINGS REPORT GENERATION

LLM output format?
Return structured JSON plus a Markdown body. We render the Markdown to HTML and then to PDF.

• Structured JSON (for validation and totals): list of “opportunities” with merchant, reason, monthly\_saving\_estimate, cancellation\_steps\[], cancellation\_link.
• Markdown body: human-friendly prose (intro, sections, bullet points).

PDF library and style?
Use WeasyPrint (HTML→PDF). Keep a simple stylesheet (A4, accessible fonts, clear headings). A future switch to ReportLab is fine if needed.

Cancellation links—source of truth?
Hybrid:
• Curated list in data/cancellations.json (we maintain/update).
• LLM may propose links; we validate domain and prefer curated entries when available.

STEP 8 – PACKAGING & ORCHESTRATION

Seed dataset location?
backend/seed/ (sample JSONL, seed rules, example users). Include Makefile targets to load.

Should make seed be idempotent?
Yes. Upserts by natural keys (e.g., rule id or title+pattern, user email).

PyInstaller artefacts—platforms?
Publish Windows and macOS artefacts for every release tag. If macOS notarisation isn’t set up yet, publish unsigned with clear instructions.

STEP 10 – COMMANDS & ENVIRONMENT

Defaults documented?
Yes—commit .env.example with safe defaults and comments.

Include FRONTEND\_URL and API\_URL?
Yes—both should be in .env.example (used by CORS, links in emails, and the frontend).

GENERAL

Multi-currency in MVP?
Primary focus is GBP. MVP reads currency from source when available and carries it through the pipeline. Rules store a currency field (nullable; default “GBP”). No FX conversion in MVP; mixed-currency datasets are allowed but totals are per-currency (we can add FX later).

Cost guardrails—shared or separate?
Separate budgets:
• Classification: MAX\_DAILY\_COST\_GBP\_CLASSIFY (default e.g., 5.00).
• Report generation: MAX\_DAILY\_COST\_GBP\_REPORT (default e.g., 2.00).
Also keep a global MAX\_DAILY\_COST\_GBP as a hard circuit breaker.

If anything above should be tweaked (thresholds, limits, or schemas), say the word and I’ll adjust quickly.
