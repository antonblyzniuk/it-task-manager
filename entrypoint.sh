#!/bin/bash

echo "=== IT Task Manager starting ==="
echo "Python: $(python --version 2>&1)"
echo "PORT: ${PORT:-8000}"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo yes || echo NO)"

# Wait for the database to be ready (up to 90s)
echo "Waiting for database..."
DB_READY=0
for i in $(seq 1 30); do
    if python -c "
import os, sys
from urllib.parse import urlparse
import psycopg2

url = os.environ.get('DATABASE_URL', '')
if not url:
    print('ERROR: DATABASE_URL is not set', flush=True)
    sys.exit(2)
p = urlparse(url)
sslmode = os.environ.get('DB_SSLMODE', 'require')
try:
    c = psycopg2.connect(
        host=p.hostname, port=p.port or 5432,
        user=p.username, password=p.password,
        dbname=p.path[1:], sslmode=sslmode,
        connect_timeout=5,
    )
    c.close()
    print('Database ready!', flush=True)
    sys.exit(0)
except Exception as e:
    print(f'  not ready: {e}', flush=True)
    sys.exit(1)
" 2>&1; then
        DB_READY=1
        break
    fi
    echo "  attempt $i/30, retrying in 3s..."
    sleep 3
done

if [ "$DB_READY" -eq 0 ]; then
    echo "FATAL: database not available after 90s"
    exit 1
fi

echo "Running collectstatic..."
if ! python manage.py collectstatic --no-input 2>&1; then
    echo "FATAL: collectstatic failed"
    exit 1
fi

echo "Running migrations..."
if ! python manage.py migrate 2>&1; then
    echo "FATAL: migrate failed"
    exit 1
fi

echo "Starting gunicorn on 0.0.0.0:${PORT:-8000}..."
exec gunicorn it_task_manager.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 2 \
    --timeout 120 \
    --log-file -
