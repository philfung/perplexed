FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_PYTHON=/usr/local/bin/python
# Enable bytecode compilation.
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume.
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=never

# bun is a single-executable replacement for Node.js
COPY --from=oven/bun /usr/local/bin/bun /usr/local/bin/bun

RUN grep PRETTY_NAME /etc/os-release && \
    python -V \
    echo $(uv --version) && \
    echo bun $(bun --version) && \
    bun x serve --version && \
    bun x rust-just --version

WORKDIR /app

COPY justfile justfile

# layer the frontend first - assume to change less frequently
# you can swap front/backend around based on your dev patterns
COPY frontend frontend

# we use "bun" to get a "just" executable without separate install step
RUN bun x rust-just frontend-install frontend-build

COPY backend backend
# Install the project's backend dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    ls -ald /app/backend/* && \
    bun x rust-just backend-install

# Copy startup scripts
COPY docker/*.sh /app

#COPY docker/supervisord.conf /etc/supervisor/conf.d/app.conf
#RUN mkdir -p /var/log/supervisor

# Expose ports if needed (adjust as necessary)
EXPOSE 30000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/bin/bash"]
# CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
