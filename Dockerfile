FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --only main
COPY backend ./backend
COPY bankcleanr ./bankcleanr
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
