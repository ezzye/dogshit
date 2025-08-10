# dogshit

A simple tool for analysing bank statements using various LLM adapters. It ships a
command line interface and a small test-suite.

## Quick Start

1. Install the backend and frontend dependencies:

   ```bash
   poetry install --with dev
   cd frontend && npm install && cd ..
   ```

2. Start the API and Vite dev server:

   ```bash
   docker compose up --build api frontend
   ```

Open <http://localhost:5173> and follow the three-click flow:

1. **Download** the desktop extractor.
2. **Upload** the generated `transaction_v1.jsonl` file.
3. **Download** the savings report.

### Backend and frontend build

Run the services directly without Docker:

#### Backend

```bash
poetry run uvicorn backend.app:app --reload
```

#### Frontend

```bash
cd frontend
npm run dev   # start Vite dev server
npm run build # create production assets
```

### Build

Create self-contained binaries for the extractor:

```bash
   poetry run bankcleanr build
   ```

## Setup with Poetry

1. [Install Poetry](https://python-poetry.org/docs/#installation).
2. Create the virtual environment and install all dependencies (including test
   requirements):

   ```bash
   poetry install --with dev
   ```

   Alternatively, run `make install` if you prefer using the new Makefile.

## Supported banks

The extractor ships with parsers for a few UK banks:

- `barclays`
- `hsbc`
- `lloyds`

Select the appropriate parser with the `--bank` option:

```bash
poetry run bankcleanr extract statement.pdf tx.jsonl --bank hsbc
```

Unit tests for these parsers live in [`tests/test_parsers.py`](tests/test_parsers.py).
Contributors adding a new bank should extend that file with corresponding
coverage.

## Running the tests

Run the unit tests with `pytest` and the behaviour driven tests with `behave`.
Make sure the development dependencies were installed first:
`poetry install --with dev`.
You can run the tests directly or via the `Makefile`:

```bash
make test
# run Playwright end-to-end tests
make e2e
# or run them manually
poetry run pytest
poetry run behave
cd frontend && npm test
```

### Frontend end-to-end tests

The SPA uses [Playwright](https://playwright.dev/) for browser tests. Install the
JavaScript dependencies and run the suite with:

```bash
cd frontend
npm install
npm test
```

## Configuration

The tool loads settings from `~/.bankcleanr/config.yml`. Set your preferred LLM
provider in this file:

```yaml
# ~/.bankcleanr/config.yml
llm_provider: openai
```

API keys are supplied via environment variables. Set the one matching your chosen
provider:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `MISTRAL_API_KEY`
- `ANTHROPIC_API_KEY`
- `BFL_API_KEY` (falls back to `OPENAI_API_KEY` if unset)
- `MAX_LLM_COST_PER_DAY` (optional, limit spend in GBP)
- `LLM_COST_PATH` (optional, where to track daily spend)

Export the appropriate variable before running the CLI so the adapter can talk
to the LLM service.
The behaviour and end-to-end suites will skip scenarios that require a live
LLM if the corresponding key is missing.

When running the behaviour tests, the live classification steps verify that the
API key isn't a placeholder and perform a short connectivity check. If this
probe fails the scenario is skipped so the suite can run without valid
credentials or network access.

Run `poetry run bankcleanr config` to see which configuration file is in use.

### LLM workflow

1. Transactions are parsed and labelled with regex heuristics.
2. Any remaining `unknown` items are sent to the configured LLM adapter using
   the API key you provided.
3. Recommendations are generated from these labels and written to the summary
   file.

## Running the application

You can invoke the CLI through Poetry:

```bash
poetry run bankcleanr config
poetry run bankcleanr analyse path/to/statement.pdf
# or analyse every PDF in a directory
poetry run bankcleanr analyse "Redacted bank statements"
# write results to a separate directory
poetry run bankcleanr analyse path/to/statement.pdf --outdir results/run1

```
Using `--outdir` keeps your work organised. Test runs can write to something
like `results/tests` while real analyses store their summaries in another
folder.

The second form accepts a folder path and processes each PDF it finds. By
default `summary.csv` is written to the current directory.
PDF output is only produced when you pass `--pdf` or give an `--output`
filename ending in `.pdf`. The command always reminds you to verify each
recommendation manually.

### FastAPI backend

The repository also includes a small FastAPI service. Start it inside Docker:

```bash
docker compose up api
```

This runs the API on [localhost:8000](http://localhost:8000) and sets the
`APP_ENV` variable from `docker-compose.yml` (defaults to `prod`). The Docker
image disables Poetry's virtual environments by setting
`POETRY_VIRTUALENVS_CREATE=false` and exposes port 8000.
Launch the
frontend dev server alongside it with:

```bash
docker compose up frontend
```

The Vite dev server will then be available on port 5173 while the API continues
to listen on port 8000.

When starting with an empty database run the import script once to seed the
default heuristics:

```bash
poetry run python scripts/import_heuristics.py
```

### Updating heuristics

Regex patterns are stored in the application's SQLite database. After LLM
classification the tool asks if newly labelled descriptions should be saved as
new heuristics. Confirm with `y` to store the pattern so future runs recognise
it.

Rules can also be edited through the web interface or via the API. Upload a
JSONL transaction file in the frontend, adjust or add patterns in the table and
click **Save**. This issues a `POST` request to `/heuristics` which writes the
rule to the database.

## Building standalone executables

Run `bankcleanr build` to create a single-file binary for the current operating
system:

```bash
poetry run bankcleanr build
```

Install `pyinstaller` first (either via `pip install pyinstaller` or
`poetry install --with dev`). Because PyInstaller cannot cross compile you must
execute this command on the operating system you want to target. The resulting
file is written to the `dist/` directory.

For macOS builds ensure the Python interpreter matches the desired architecture
(`arm64` or `x86_64`). First locate the active interpreter:

```bash
pyenv which python3
```

Then inspect the binary to confirm its architecture:

```bash
file $(pyenv which python3)
```

The output should mention both `arm64` and `x86_64` when using a universal
build. Installing Python from
[python.org](https://www.python.org) provides such an interpreter.

To verify a build you can run the binary on the included sample PDF:

```bash
./dist/bankcleanr parse "Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf" --jsonl tx.jsonl
```
This command produces a `tx.jsonl` file containing the parsed transactions.

macOS users can run the same command. On Windows use the `.exe` produced in the
`dist` directory:

```cmd
dist\bankcleanr.exe parse "Redacted bank statements\22b583f5-4060-44eb-a844-945cd612353c (1).pdf" --jsonl tx.jsonl
```

## Release process

1. Update the version in `pyproject.toml` and commit the change.
2. Create a new tag and push it to GitHub:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

The `build` workflow builds executables for Linux, macOS (Intel and ARM) and Windows. Each job uploads its binary and a matching `.sha256` checksum file to the GitHub release associated with the tag.

### Verifying checksums

After downloading an executable and its checksum file, confirm the contents match:

```bash
# macOS / Linux
shasum -a 256 -c bankcleanr-linux.sha256

# Windows (PowerShell)
CertUtil -hashfile bankcleanr-windows.exe SHA256
Get-Content bankcleanr-windows.sha256
```

The displayed hash must equal the value stored in the `.sha256` file before running the binary.

## Disclaimer

Every summary includes the following disclaimer:

```
This tool automates the categorisation of your personal bank transactions.
It is not regulated financial advice. Results may be incomplete or inaccurate.
All processing occurs on this computer; only transaction descriptions are sent to the language-model provider you choose.
Use at your own risk. Always verify recommendations with the original supplier or your bank before cancelling any service.
```

Always read this disclaimer in your output and verify each recommendation yourself before taking any action.

## Version control

Personal PDF statements should not be committed to the repository. The
`.gitignore` file contains an `*.pdf` rule so your own statements are skipped,
while allowing the sample files kept in `Redacted bank statements`.
