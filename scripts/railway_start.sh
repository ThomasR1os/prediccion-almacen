#!/usr/bin/env bash
set -euo pipefail

echo "=== Railway startup ==="

python manage.py migrate --noinput

echo "=== Downloading ML model (may take 2-3 min) ==="
python scripts/ensure_model.py

echo "=== Starting Gunicorn ==="
exec gunicorn desercion_escolar.wsgi:application -c gunicorn.conf.py
