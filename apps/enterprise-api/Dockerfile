FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --no-cache-dir --upgrade pip && \
    python -c "import tomllib, subprocess, sys; deps = tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']; sys.exit(subprocess.call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir'] + deps))"

COPY . .

RUN pip install --no-cache-dir --no-deps . && \
    python -c "import psycopg"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
