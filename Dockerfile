FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc curl postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY tests/ ./tests/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["bash", "backend/start.sh"]
