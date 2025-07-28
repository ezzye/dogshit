.PHONY: install test unit behave component lint e2e

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

e2e:
	@if command -v podman >/dev/null 2>&1; then \
	podman compose up --build frontend e2e; \
	else \
	docker compose up --build frontend e2e; \
	fi
