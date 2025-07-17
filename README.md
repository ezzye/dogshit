# dogshit

A simple tool for analysing bank statements using various LLM adapters. It ships a
command line interface and a small test-suite.

## Setup with Poetry

1. [Install Poetry](https://python-poetry.org/docs/#installation).
2. Create the virtual environment and install all dependencies (including test
   requirements):

   ```bash
   poetry install --with dev
   ```

   Alternatively, run `make install` if you prefer using the new Makefile.

## Running the tests

Run the unit tests with `pytest` and the behaviour driven tests with `behave`.
Make sure the development dependencies were installed first:
`poetry install --with dev`.
You can run the tests directly or via the `Makefile`:

```bash
make test
# or run them manually
poetry run pytest
poetry run behave
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

Export the appropriate variable before running the CLI so the adapter can talk
to the LLM service.

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

### Updating heuristics

Regex patterns for the local classifier live in `bankcleanr/data/heuristics.yml`.
After LLM classification the tool asks if newly labelled descriptions should be
added to this file. Confirm with `y` to store the pattern so future runs
recognise it. You can also edit the YAML manually if needed.

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
