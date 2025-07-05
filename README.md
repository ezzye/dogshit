# dogshit

A simple tool for analysing bank statements using various LLM adapters. It ships a
command line interface and a small test-suite.

## Setup with Poetry

1. [Install Poetry](https://python-poetry.org/docs/#installation).
2. Create the virtual environment and install dependencies:

   ```bash
   poetry install
   ```

## Running the tests

Run the unit tests with `pytest` and the behaviour driven tests with `behave`:

```bash
poetry run pytest
poetry run behave
```

## Configuration

The tool loads settings from `~/.bankcleanr/config.yml`. Set your preferred LLM
provider in this file. API keys are taken from environment variables so you
never need to store them on disk:

```yaml
llm_provider: openai

# API keys
OPENAI_API_KEY=sk-your-openai-key
GEMINI_API_KEY=your-gemini-key
```

Run `poetry run bankcleanr config` to see which configuration file is in use.

## Running the application

You can invoke the CLI through Poetry:

```bash
poetry run bankcleanr config
poetry run bankcleanr analyse path/to/statement.pdf
# or analyse every PDF in a directory
poetry run bankcleanr analyse "Redacted bank statements"

```

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
