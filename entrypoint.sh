#!/bin/bash
set -e

python manage.py collectstatic --no-input
python manage.py migrate

exec gunicorn it_task_manager.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 2 \
    --timeout 120 \
    --log-file -
