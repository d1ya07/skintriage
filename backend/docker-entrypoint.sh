#!/bin/sh
set -e
echo "▶ Running database migrations"
python -m alembic upgrade head
if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "▶ Seeding demo data (safe to repeat)"
  python scripts/seed.py
fi
echo "▶ Starting API"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 \
  --workers "${UVICORN_WORKERS:-2}" --proxy-headers --forwarded-allow-ips="*"
