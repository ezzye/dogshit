.PHONY: install test unit behave component lint e2e start

install:
	poetry install --with dev
	cd frontend && npm install

unit:
	poetry run pytest

behave:
	poetry run behave

component:
	poetry run pytest tests/test_backend_api.py

test:
	poetry run pytest --cov=. --cov-fail-under=$${COV_FAIL_UNDER:-50}
	poetry run behave

lint:
	poetry run ruff check .
	poetry run mypy .

e2e:
	@if command -v podman >/dev/null 2>&1; then \
	podman compose up --build frontend e2e; \
	elif docker compose version >/dev/null 2>&1; then \
	docker compose up --build frontend e2e; \
	else \
        docker-compose up --build frontend e2e; \
        fi

start:
	docker compose up --build api frontend
