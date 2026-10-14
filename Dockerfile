FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim AS builder

WORKDIR /src

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv lock && \
    uv sync --frozen --no-install-project --no-dev

FROM python:3.11-slim

RUN groupadd -g 10001 appgroup && useradd -u 10001 -g appgroup -m -s /bin/bash appuser

WORKDIR /src

RUN pip install --no-cache-dir --upgrade pip setuptools>=79.0.0 wheel>=0.45.1

COPY --from=builder /src/.venv /src/.venv

COPY . .

ENV PATH="/src/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH="/src"

EXPOSE 8000

ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

USER 10001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "src/main.py"]


