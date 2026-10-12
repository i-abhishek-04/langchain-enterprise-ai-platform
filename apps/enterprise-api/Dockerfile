FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN if [ -f pyproject.toml ]; then \
        pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir . "psycopg[binary]>=3.2.0" "psycopg2-binary>=2.9.9"; \
    elif [ -f apps/enterprise-api/pyproject.toml ]; then \
        pip install --no-cache-dir --upgrade pip && \
        pip install --no-cache-dir ./apps/enterprise-api "psycopg[binary]>=3.2.0" "psycopg2-binary>=2.9.9" && \
        cp -rn apps/enterprise-api/* . 2>/dev/null || true; \
    fi && \
    python -c "import psycopg"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
