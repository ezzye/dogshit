You can give people a single download that “just runs” without them having to install Python or any libraries, but you must build a **separate artefact for each operating-system/architecture**.  Think of it like how a Windows *.exe* and a macOS *.app* are two different files compiled from the same C programme.

---

### Packaging options that embed Python

| Tool                    | One-file?                                                                       | Platforms             | Notes                                                                                                           |
| ----------------------- | ------------------------------------------------------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------- |
| **PyInstaller**         | `--onefile` flag gives a self-extracting binary 30-100 MB; most common choice   | Windows, macOS, Linux | Not a cross-compiler: build on Windows for Windows, on macOS for macOS, etc. ([pyinstaller.org][1])             |
| **Nuitka**              | `--onefile` or `--standalone`; compiles to C then freezes; often smaller/faster | Windows, macOS, Linux | Produces executables that run “without a separate installer” ([nuitka.net][2])                                  |
| **PyOxidizer**          | Static Rust build; very small size; one binary per CPU family                   | Windows, macOS, Linux | Can’t yet emit a *universal* (Intel + ARM) macOS binary, so you ship two files ([pyoxidizer.readthedocs.io][3]) |
| **BeeWare / Briefcase** | Makes native installers: *.app*, *.msi*, AppImage, iOS/Android projects         | Many                  | Good for GUI apps; handles code-signing scaffolding on macOS and Windows ([briefcase.readthedocs.io][4])        |
| **zipapp / Shiv / Pex** | Single *.pyz* file                                                              | Anywhere              | Still needs a system Python (`python3 myapp.pyz`), so not “no-install” ([shiv.readthedocs.io][5])               |

---

### Typical build workflow (PyInstaller shown)

```bash
# Windows – run this in PowerShell or CMD on a Windows box/VM
py -m pip install --upgrade pyinstaller
pyinstaller --onefile mybankassistant.py    # produces dist\mybankassistant.exe

# macOS (Intel or Apple Silicon) – run on a Mac with the right SDK)
python3 -m pip install --upgrade pyinstaller
pyinstaller --windowed --onefile mybankassistant.py  # dist/MyBankAssistant.app
```

**Cross-compiling** isn’t officially supported, so CI pipelines usually spin up a Windows runner for the *.exe* and a macOS runner for the *.app* (GitHub Actions, Azure etc.) ([pyinstaller.org][1], [pyinstaller.org][1])

---

### Platform gotchas you still need to tackle

* **Code-signing & notarisation (macOS)** – unsigned apps will be blocked by Gatekeeper. Briefcase or the `codesign` and `notarytool` CLIs help.
* **SmartScreen (Windows)** – an unsigned *.exe* will show a blue “unknown publisher” warning. Buy a code-signing certificate or use Windows Store if you need friction-free installs.
* **File size** – self-contained binaries weigh 30-150 MB because they embed the interpreter, stdlib and any binary wheels (Pandas, PyPDF2, etc.).
* **Updates** – you’ll need an auto-update mechanism, or ask users to download a new binary when you ship fixes.

---

### Applying this to your bank-statement-clean-up idea

1. **Core script**

   * Parse CSV, OFX or PDF statements (e.g. with *pandas* or *camelot*).
   * Send each transaction text to your chosen LLM API (OpenAI, Gemini, local model, etc.).
   * Classify: *subscription*, *one-off*, *income*, *unknown*.
   * Produce an action list: “Keep”, “Cancel → contact x via y”, “Review”.

2. **Package**
   Build two artefacts with PyInstaller or Nuitka as above. Store the user’s OpenAI key in an **environment variable**; read it at runtime so it isn’t baked into the binary.

3. **Privacy & risk**
   Remind users that sending raw bank data to the cloud is a data-protection issue. For a public release you’ll need (a) encrypted transport, (b) clear consent, and (c) a way to strip or mask personal data before the LLM sees it.

4. **Future polish**

   * Add a lightweight GUI with *PySide6* or *Toga* (BeeWare) so less-technical users can drag-and-drop a statement file.
   * Integrate UK Open Banking APIs for direct transaction pulls instead of manual uploads.
   * Provide a JSON export or nicely formatted PDF of the “cancel this” report.

Done right, the end-user experience is:

*Download ⇒ double-click ⇒ the app opens, analyses the statement, and tells them what subscriptions to nuke.*

No separate Python install, no pip, no extra hoops.

[1]: https://www.pyinstaller.org/ "PyInstaller Manual — PyInstaller 6.14.1 documentation"
[2]: https://nuitka.net/ "Nuitka the Python Compiler — Nuitka the Python Compiler"
[3]: https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer_distributing_macos.html "Distribution Considerations for macOS — PyOxidizer 0.23.0 documentation"
[4]: https://briefcase.readthedocs.io/ "Briefcase 0.3.23"
[5]: https://shiv.readthedocs.io/ "shiv  — shiv  documentation"


# High-level architecture for a privacy-first “Bank-Clean-up” desktop app

1. Core goals
   • Runs entirely on the end-user’s laptop – no server component.
   • Accepts any PDF statement layout.
   • Lets the user plug in *their* preferred LLM (and API key).
   • Ships as an audited, reproducible, one-file installer for Windows and macOS.
   • Every screen and report carries a plain-English disclaimer explaining limits, privacy and “no financial advice”.

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
2\. Top-level package layout (Python 3.10 + typer CLI)

```
bankcleanr/
│
├── cli.py            ← Typer entry-points: analyse, gui, config
├── gui/              ← Optional Toga UI package
├── io/
│   ├── loader.py     ← Dispatches to pdf, csv, ofx sub-parsers
│   └── pdf/
│        ├── generic.py
│        ├── barclays.py
│        ├── lloyds.py           # bank-specific overrides
│        └── ocr_fallback.py
├── llm/
│   ├── base.py       ← AbstractAdapter with .classify_transactions()
│   ├── openai.py
│   ├── anthropic.py
│   ├── mistral.py
│   └── local_ollama.py
├── rules/
│   ├── regex.py      ← Fast local heuristics (e.g. Spotify, Netflix)
│   └── prompts.py    ← Jinja templates for the chosen LLM
├── reports/
│   ├── writer.py     ← CSV, JSON and PDF summaries
│   └── disclaimers.py
├── settings.py       ← Pydantic: loads ~/.bankcleanr/config.yml
└── __main__.py       ← “python -m bankcleanr …”
```

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
3\. Processing pipeline (runtime flow)

1. Input capture
    • User drags a PDF (or a folder) into the GUI **or** runs `bankcleanr analyse ~/Downloads/*.pdf`.
    • Settings module loads their selected LLM provider and API key from an encrypted keyring entry.

2. Statement parsing
    • `pdfplumber` attempts structured table extraction first (fast, no cloud). ([github.com][1])
    • If confidence < 0.8, fall back to regex line parsing; if all else fails, route through `ocr_fallback.py` (Tesseract).
    • Every transaction becomes a dataclass: date, description, amount, balance↲.

3. Local heuristics
    • Regex-based classifier tags obvious subscriptions (Spotify, iCloud) without an LLM call to save tokens.

4. LLM classification
    • Unmatched items are sent to `llm/<provider>.py`, which wraps that vendor’s SDK behind the same interface.
    • Adapters built with LangChain’s integration layer so switching providers is a one-liner. ([python.langchain.com][2], [github.com][3])
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

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
4\. Security & privacy measures

• All parsing and classification logic runs locally; the *only* outbound traffic is HTTPS calls to the LLM host the user chose.
• Before dispatch, the engine masks account numbers / sort-codes with `****1234` to minimise exposure.
• Opt-in toggle lets paranoid users force *zero* cloud calls (regex-only classification).
• Builds are reproducible: `pyinstaller --onefile --clean --strip --noupx ...` plus the steps documented in PyInstaller’s reproducible-build guide. ([pyinstaller.org][4])
• GitHub Actions workflow:
– macOS runner → signed, notarised `.dmg`
– Windows runner → signed `.exe`
– SHA-256 checksums committed to `RELEASES.md` so a friend can verify their download.
• Optional `--audit` flag prints every prompt/response pair to a local HTML file for manual inspection.

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
5\. Installer and update strategy

• Bundling: PyInstaller (or Nuitka if you want true C compilation). Generates **one** artefact per OS/architecture.
• Signing:
– macOS: `codesign` + `notarytool` using your Apple Developer ID.
– Windows: EV Code-Signing certificate for a clean SmartScreen.
• First-run wizard writes config file + stores API key via `keyring`.
• `bankcleanr update` pings GitHub Releases for a newer tag; if found, downloads the platform file and verifies checksum.

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
6\. Sample disclaimer block (plain text)

“This tool automates the categorisation of your personal bank transactions.
It is **not** regulated financial advice. Results may be incomplete or inaccurate.
All processing occurs on this computer; only transaction descriptions are sent to the language-model provider you choose.
Use at your own risk. Always verify recommendations with the original supplier or your bank before cancelling any service.”

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
7\. Future extensions

• Direct Open Banking API import (with user consent) → no PDFs.
• Plug-in system for new LLMs (Gemini, Llama 3 via local GGUF).
• Action-button in GUI to generate a cancellation email template in Outlook/Apple Mail.
• Aggregate dashboard: recurring spend by merchant, month-on-month savings after cancellations.

This outline should give your auditors confidence (full source + reproducible build path) while letting end-users run a single, self-contained installer.

[1]: https://github.com/jsvine/pdfplumber?utm_source=chatgpt.com "jsvine/pdfplumber - and easily extract text and tables. - GitHub"
[2]: https://python.langchain.com/docs/integrations/llms/?utm_source=chatgpt.com "LLMs - Python LangChain"
[3]: https://github.com/langchain-ai/langchain-mcp-adapters?utm_source=chatgpt.com "LangChain MCP Adapters - GitHub"
[4]: https://pyinstaller.org/en/stable/advanced-topics.html?utm_source=chatgpt.com "Advanced Topics — PyInstaller 6.14.1 documentation"

