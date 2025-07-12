#!/bin/bash

cd /app/backend
source .venv/bin/activate
mkdir -p /var/log/app
log_file=/var/log/app/backend.log
gunicorn \
    --bind localhost:5000 \
    --daemon \
    --workers 4 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --pid /tmp/gunicorn.pid \
    --log-file $log_file \
    app:app
echo "Follow app log at $log_file"
