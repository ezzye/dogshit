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
You can run them directly or via the `Makefile`:

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

API keys are supplied via environment variables. Use `OPENAI_API_KEY` for the
OpenAI adapter or `GEMINI_API_KEY` for Gemini. The BFL adapter checks
`BFL_API_KEY` and falls back to `OPENAI_API_KEY` if the former is not set.

Run `poetry run bankcleanr config` to see which configuration file is in use.

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

The second form accepts a folder path and processes each PDF it finds. The
combined results are written to `summary.csv` in the current directory.

The `analyse` command writes a `summary.csv` to the working directory.
If you pass a directory, it processes all PDFs inside before writing the file.
It also prints a reminder to verify each recommendation manually.

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
