FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.6.17 /uv /uvx /bin/

COPY pyproject.toml ./pyproject.toml
COPY src ./src

RUN uv pip install --system -e .

CMD ["uvicorn", "quant_cover_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
