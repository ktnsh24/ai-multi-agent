FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --only main

COPY src/ ./src/

RUN mkdir -p data

EXPOSE 8400

CMD ["poetry", "run", "uvicorn", "src.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8400"]
