FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# this Dockerfile runs both the frontend/backend in a monolith container
# frontend is served by nginx static
# backend is reverse proxied to the fastapi app running at localhost:30001 in container
ARG FRONTEND_BUILD_DIR=frontend/build-prod

# Enable bytecode compilation.
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume.
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=never

# Setup nginx reverse proxy to manage frontend + backend as a single http service
COPY --from=nginx:1.29.0-bookworm /usr/sbin/nginx /usr/sbin/nginx
COPY --from=nginx:1.29.0-bookworm /etc/nginx/ /etc/nginx/
COPY --from=nginx:1.29.0-bookworm /var/log/nginx/ /var/log/nginx/

# Create nginx user and group
# Report out system attributes
RUN groupadd -g 101 nginx && \
    useradd -r -u 101 -g nginx -s /sbin/nologin -d /var/cache/nginx -M nginx && \
    mkdir -p /var/cache/nginx /var/log/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/log/nginx && \
    grep PRETTY_NAME /etc/os-release && \
    nginx -v && \
    python -V && \
    echo $(uv --version)

WORKDIR /app

# layer the frontend first - assume to change less frequently
# you can swap front/backend around based on your dev patterns
COPY $FRONTEND_BUILD_DIR /app/frontend
COPY docker/nginx.conf /etc/nginx/nginx.conf
RUN ls -ld /app/frontend/* && \
    test -f /app/frontend/index.html && \
    cat /etc/nginx/nginx.conf

COPY backend backend
# Install the project's backend dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /usr/local/bin/python -r /app/backend/requirements.txt && \
    ls -ald /app/backend/* && \
    gunicorn --version && \
    python -c 'import groq'

# Copy deployment configs / startup scripts
COPY docker/*.sh docker/*.py /app/

# Expose ports if needed (adjust as necessary)
EXPOSE 30000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/app/start_server.sh"]
