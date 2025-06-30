The repository already outlines how the full workflow should operate. The component_overview.md file describes a detailed pipeline:

2. Statement parsing
   • `pdfplumber` attempts structured table extraction first (fast, no cloud).
   • If confidence < 0.8, fall back to regex line parsing; if all else fails, route through `ocr_fallback.py` (Tesseract).
   • Every transaction becomes a dataclass: date, description, amount, balance↲.

3. Local heuristics
   • Regex-based classifier tags obvious subscriptions (Spotify, iCloud) without an LLM call to save tokens.

4. LLM classification
   • Unmatched items are sent to `llm/<provider>.py`, which wraps that vendor’s SDK behind the same interface.
   • Adapters built with LangChain’s integration layer so switching providers is a one-liner.
   • Async batch requests; rate-limit warm-ups handled by `tenacity` retry.

5. Recommendation engine
   • Combines regex + LLM labels → “Keep”, “Cancel”, “Investigate”.
   • If “Cancel”, cross-reference a YAML knowledge-base of merchant cancellation paths (URL, phone, template email).

6. Output
   • `reports/writer.py` builds:
   – CSV for spreadsheet people
   – PDF summary with a “How to cancel” appendix
   – Terminal summary (if CLI)
   • Each report appends the global disclaimer from `disclaimers.py`.

The disclaimer text is provided in bankcleanr/reports/disclaimers.py:

GLOBAL_DISCLAIMER = (
"This tool automates the categorisation of your personal bank transactions.\n"
"It is not regulated financial advice. Results may be incomplete or inaccurate.\n"
"All processing occurs on this computer; only transaction descriptions are sent to the language-model provider you choose.\n"
"Use at your own risk. Always verify recommendations with the original supplier or your bank before cancelling any service."
)

To run the CLI tool, the README shows:

poetry run bankcleanr config
poetry run bankcleanr analyse path/to/statement.pdf

Currently, the parsing logic in bankcleanr/io/pdf/generic.py is just a placeholder:

def parse_pdf(path: str):
"""Placeholder PDF parser."""
# Real implementation would use pdfplumber here
return []

Likewise, the LLM adapters return "unknown" for every transaction because they’re stubs:

class OpenAIAdapter(AbstractAdapter):
"""Stub adapter for OpenAI API."""

    def classify_transactions(self, transactions):
        return ["unknown" for _ in transactions]

## Next steps
Implement PDF parsing
Fill out parse_pdf using a library such as pdfplumber to extract transaction rows (date, description, amount, balance). If accuracy is low, add the regex and OCR fallbacks outlined in the component overview.

Normalise transactions
Convert parsed rows into a standard dataclass or dictionary format so they can be processed uniformly.

Local heuristics
Expand rules/regex.py with known subscription keywords (e.g., Spotify, Netflix) to quickly tag obvious recurring charges without hitting the LLM.

LLM classification
Implement the adapter in llm/openai.py (or another provider). Use Jinja templates from rules/prompts.py to build classification prompts. Batch transactions and handle retries to stay within rate limits.

Recommendation engine
Combine regex results and LLM output to determine which merchants might be cancellable. Cross-reference with a cancellation knowledge base.

Generate reports
Use reports/writer.py to output a CSV summary (and possibly a PDF version) that includes cancellation instructions and the standard disclaimer text.

Manual review
Even after LLM classification, advise users to verify each recommendation. The repository’s disclaimer explicitly states the tool is not regulated financial advice and results may be incomplete or inaccurate.

By completing these steps, the project can parse your example bank statements, classify recurring charges, and produce a cancellation checklist while keeping the analysis local except for optional LLM calls.


