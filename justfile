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
    cd backend && (uv venv && . .venv/bin/activate && uv pip install -r requirements.txt)

backend-dev:
    cd backend && (test -f .env && source .env && python app.py)

backend-prod:
    cd backend && ./script_start_gunicorn.sh

backend-kill:
    cd backend && ./script_kill_servers.sh

# Frontend recipes
frontend-install:
    cd frontend && bun install

frontend-build:
    cd frontend && bun run build

frontend-dev:
    cd frontend && PORT=30000 bun run start

frontend-prod-clean:
    cd frontend && rm -rf node_modules package-lock.json

frontend-prod-build: frontend-prod-clean
    cd frontend && bun install --no-optional --omit=optional
    cd frontend && bun run build && ls ./build/index.html

frontend-prod-serve:
    cd frontend && bunx serve -s build -l 30000

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
build-image:
    docker build -t perplexed .

rebuild-image: frontend-prod-build
    docker build -t perplexed --no-cache --progress plain .

run cmd="":
    docker run \
        --env-file <(sed s/'export '//g ./backend/.env | grep -v '^#') \
        --env DOMAINS_ALLOW="http://localhost:30000" \
        -p 5000:5000 \
        -p 30000:30000 \
        -it perplexed \
        {{cmd}}

backend-log:
    docker exec $(docker ps --filter "ancestor=perplexed" --format '{{{{.ID}}') \
        tail -f /var/log/app/backend.log

sh-image:
    # same as "run" but drop into shell for interactive debug
    just run /bin/bash
