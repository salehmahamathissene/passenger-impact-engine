#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=/app/src

echo "✅ Waiting for Postgres..."
python - <<'PY'
import os, time
import psycopg2

url = os.environ["DATABASE_URL"]
for i in range(60):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print("✅ Postgres is ready")
        break
    except Exception as e:
        print(f"⏳ not ready yet ({i+1}/60): {e}")
        time.sleep(1)
else:
    raise SystemExit("❌ Postgres never became ready")
PY

echo "✅ Running migrations..."
alembic -c /app/alembic.ini upgrade head

echo "✅ Starting SaaS API..."
exec gunicorn -k uvicorn.workers.UvicornWorker \
  -w "${WEB_CONCURRENCY:-1}" \
  -b "0.0.0.0:${PORT:-8001}" \
  --timeout 120 \
  --graceful-timeout 120 \
  --keep-alive 5 \
  --access-logfile - \
  --error-logfile - \
  pie.main:app

alembic -c /app/alembic.ini upgrade head
