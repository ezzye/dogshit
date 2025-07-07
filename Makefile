.PHONY: install test unit behave

install:
	poetry install --with dev

unit:
	poetry run pytest

behave:
	poetry run behave

test: unit behave
