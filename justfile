#!/usr/bin/env just --justfile

set shell := ["bash", "-c"]

# Default recipe lists available commands
default:
    @just --list

# Backend recipes
backend-setup:
    cd backend && (test -f .env && echo ".env cloned previously" || cp .env.example .env)
    @echo "Please fill in your API keys in backend/.env"

backend-venv:
    cd backend && uv venv

backend-activate:
    @echo "Run: source backend/.venv/bin/activate"

backend-install:
    cd backend && \
    uv venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt && \
    python -c 'import groq'

backend-dev:
    cd backend && \
    test -f .env && source .env \
    && . .venv/bin/activate \
    && python fastapi_app.py

# Frontend recipes
frontend-install:
    cd frontend && bun install

frontend-clean:
    cd frontend && rm -rf node_modules

frontend-build-dev:
    cd frontend && \
    bun run build:dev

frontend-dev:
    cd frontend && \
    PORT=30000 bun start ./build-dev


frontend-build-staging:
    cd frontend && \
    bun install --no-optional --omit=optional && \
    bun run build:staging
    test -f ./frontend/build-staging/index.html

frontend-build-prod:
    cd frontend && \
    bun install --no-optional --omit=optional && \
    bun run build:prod
    test -f ./frontend/build-prod/index.html

frontend-build-cloudflare namespace:
    mkdir -p ./deployment/cloudflare/dist
    cd frontend && \
    bun install --no-optional --omit=optional && \
    bun run build:cloudflare-{{ namespace }}
    test -f ./deployment/cloudflare/dist/frontend-{{ namespace }}/index.html

frontend-build-cloudflare-local:
    just frontend-build-cloudflare local

frontend-build-cloudflare-prod:
    just frontend-build-cloudflare prod

# Combined recipes
setup: backend-setup frontend-install
    @echo "Setup complete! Don't forget to fill in backend/.env"

dev:
    @echo "Starting backend and frontend in dev mode..."
    @echo "Run these in separate terminals:"
    @echo "1. just backend-dev"
    @echo "2. just frontend-dev"

# Utility recipes
clean:
    cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    cd frontend && rm -rf node_modules build

lint-backend:
    cd backend && uvx ruff check --fix .

format-backend:
    cd backend && uvx ruff format .


# Docker packaging

build-image-staging extra_flags="":
    test -d ./frontend/build-staging
    docker build -t perplexed-staging \
        --build-arg FRONTEND_BUILD_DIR=./frontend/build-staging \
        --progress plain {{extra_flags}} .

build-image-prod extra_flags="":
    docker build -t perplexed \
        --build-arg FRONTEND_BUILD_DIR=./frontend/build-prod \
        --progress plain {{extra_flags}} .

rebuild-image:
    docker build -t perplexed --no-cache --progress plain .

run cmd="":
    @if [ ! -d ./frontend/build-staging ]; then \
        just frontend-build-staging; \
    fi
    @if ! docker image inspect perplexed-staging; then \
        just build-image-staging; \
    fi
    @if [ ! -f ./backend/.env ]; then \
        cp ./backend/.env.example ./backend/.env; \
        echo "Required: must first fill out the secrets in ./backend/.env" >&2; \
        cat ./backend/.env >&2; \
        exit 1; \
    fi
    docker run \
        --env-file <(sed s/'export '//g ./backend/.env | sed 's/"//g' | grep -v '^#') \
        --env DOMAINS_ALLOW="http://localhost:30000" \
        -p 30000:30000 \
        -it perplexed-staging \
        {{cmd}}

backend-log:
    docker exec $(docker ps --filter "ancestor=perplexed" --format '{{{{.ID}}') \
        tail -f /var/log/app/backend.log

live-sh:
    docker exec -it $(docker ps --filter "ancestor=perplexed" --format '{{{{.ID}}') \
        /bin/bash

sh:
    # same as "run" but drop into shell for interactive debug
    just run /bin/bash
