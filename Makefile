.PHONY: install test unit behave lint

install:
	poetry install --with dev

unit:
	poetry run pytest

behave:
	poetry run behave

test: unit behave
lint:
	poetry run ruff bankcleanr
