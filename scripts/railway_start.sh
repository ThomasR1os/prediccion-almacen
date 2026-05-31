#!/usr/bin/env bash
set -euo pipefail

python manage.py migrate --noinput
python scripts/ensure_model.py

exec gunicorn desercion_escolar.wsgi:application \
  --bind "0.0.0.0:${PORT:-8080}" \
  --workers 1 \
  --timeout 600 \
  --preload
