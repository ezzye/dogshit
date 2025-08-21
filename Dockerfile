FROM python:3.12-slim
WORKDIR /app

# Disable virtual environments so dependencies install directly into the
# container image. Poetry also respects this environment variable during the
# build stage.
ENV POETRY_VIRTUALENVS_CREATE=false

COPY pyproject.toml poetry.lock README.md ./
# Install runtime dependencies without installing the project itself. The
# application code is copied in a later step to keep Docker layer caching
# effective during local development.
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-root

COPY backend ./backend
COPY bankcleanr ./bankcleanr
COPY rules ./rules
COPY data ./data
COPY schemas ./schemas

# Document which port the FastAPI app listens on
EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
