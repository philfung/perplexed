#!/bin/bash

cd /app/backend
source .venv/bin/activate

log_dir=/var/log/app
mkdir -p $log_dir
backend_log_file=$log_dir/backend.log
gunicorn \
    --bind 0.0.0.0:5000 \
    --daemon \
    --workers 4 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --pid /tmp/gunicorn.pid \
    --log-file $backend_log_file \
    app:app
echo "Follow backgrounded Gunicorn Python backend app log at $log_file"

cd /app/frontend
frontend_log_file=$log_dir/frontend.log
echo "Starting frontend static site in the foreground. Logging to $frontend_log_file"
/usr/local/bin/bun x serve \
    --debug \
    --listen 30000 \
    --no-port-switching \
    /app/frontend | tee $frontend_log_file
