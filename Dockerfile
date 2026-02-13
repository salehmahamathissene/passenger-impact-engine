FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim

WORKDIR /app

RUN useradd -m -u 1000 appuser

COPY --from=builder /usr/local /usr/local

COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser alembic/ /app/alembic/
COPY --chown=appuser:appuser alembic.ini /app/alembic.ini
COPY --chown=appuser:appuser deploy/ /app/deploy/
COPY --chown=appuser:appuser README.md /app/README.md

ENV PYTHONPATH=/app/src
ENV PORT=8001

USER appuser
EXPOSE 8001

CMD ["bash", "/app/deploy/start.sh"]
