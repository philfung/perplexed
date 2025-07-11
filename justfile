#!/usr/bin/env just --justfile

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
    cd backend && uv pip install -r requirements.txt

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
    cd frontend && bun cache clean --force

frontend-prod-build: frontend-prod-clean
    cd frontend && bun i --no-optional --omit=optional
    cd frontend && bun run build

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
