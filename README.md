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
provider and API key in this file:

```yaml
llm_provider: openai
api_key: sk-your-key
```

Run `poetry run bankcleanr config` to see which configuration file is in use.

## Running the application

You can invoke the CLI through Poetry:

```bash
poetry run bankcleanr config
poetry run bankcleanr analyse path/to/statement.pdf
```

The `analyse` command writes a `summary.csv` to the working directory.
