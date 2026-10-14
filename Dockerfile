FROM ghcr.io/astral-sh/uv:python3.11-trixie-slim AS builder

WORKDIR /src

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.loc[k] ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

FROM python:3.11-slim

WORKDIR /src

COPY --from=builder /src/.venv /src/.venv

COPY . .

ENV PATH="/src/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH="/src"

EXPOSE 8000

ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

CMD ["python", "src/main.py"]


