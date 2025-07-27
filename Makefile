.PHONY: install test unit behave component lint

install:
	poetry install --with dev

unit:
	poetry run pytest

behave:
	poetry run behave

component:
	poetry run pytest tests/test_backend_app.py

test: unit component behave
lint:
	poetry run ruff check .
