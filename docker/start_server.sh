#!/bin/bash -e

show_first_last_3() {
    # show a little bit of secrets to verify that env vars are injected into your remote envs
    # you do not need this helper once you successfully deploy and verify your app
    local str="$@"
    echo "${str:0:3}...${str: -3}"
}

# must have all of these env vars
(
    echo "✔︎ GOOGLE_SEARCH_ENGINE_ID=$GOOGLE_SEARCH_ENGINE_ID"
    test -n "$GOOGLE_SEARCH_API_KEY" && \
        echo "✅ GOOGLE_SEARCH_API_KEY=$(show_first_last_3 $GOOGLE_SEARCH_API_KEY)" || \
        echo "❓ GOOGLE_SEARCH_API_KEY"
    test -n "$GOOGLE_SEARCH_ENGINE_ID" && \
        echo "✅ GOOGLE_SEARCH_ENGINE_ID=$(show_first_last_3 $GOOGLE_SEARCH_ENGINE_ID)" || \
        echo "❓ GOOGLE_SEARCH_ENGINE_ID"
    test -n "$GROQ_API_KEY" && \
        echo "✅ GROQ_API_KEY=$(show_first_last_3 $GROQ_API_KEY)" || \
        echo "❓ GROQ_API_KEY"
    echo "✅ DOMAINS_ALLOW=$DOMAINS_ALLOW"
) | tee /app/env_inspect.txt

cd /app/backend

# this sanity checks env vars, docker run --env, etc
/app/groq_test.py

log_dir=/var/log/app
mkdir -p $log_dir
backend_log_file=$log_dir/backend.log

gunicorn \
    --bind 0.0.0.0:30001 \
    --daemon \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --pid /tmp/gunicorn.pid \
    --log-file $backend_log_file \
    fastapi_app:app

echo "Follow backgrounded Gunicorn + UvicornWorker Python backend app log at $backend_log_file"

# nginx logs are at /var/log/nginx/{access,error}.log
nginx -g "daemon off;"
