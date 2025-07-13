## <img height="25" src="https://github.com/philfung/perplexed/blob/main/frontend/public/images/logo-color.svg"/> Perplexed
#### An open-source app inspired by the amazing web search product, Perplexity.
[![Live Demo](https://img.shields.io/badge/Live-Demo-green)](https://d37ozmhmvu2kcg.cloudfront.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Last Commit](https://img.shields.io/github/last-commit/philfung/perplexed)]()


[**Live Demo**](https://d37ozmhmvu2kcg.cloudfront.net/)

<img width="600" alt="Screenshot 2025-03-19 at 1 26 54 PM" src="https://github.com/user-attachments/assets/f190473c-467c-4169-87c9-a285dc0f234f" />
<img width="600" alt="Screenshot 2025-03-19 at 1 26 35 PM" src="https://github.com/user-attachments/assets/07b0ad71-9c53-4d7f-a1e7-b2bded2f1806" />

## Implementation
Given a user query, the app conducts a web search,
downloads the top N resulting web pages, then analyzes those pages 
with an LLM.  

<img height="400" alt="Screenshot 2024-11-16 at 10 06 03 AM" src="https://github.com/user-attachments/assets/e88ff3ee-2efc-4a36-8427-fcf90141a083">

The LLM can be any smaller, consumer-grade with at least 5k context window (assuming each web page ~1k tokens).

## Deployment Instructions - Easy

[How to install Just](https://github.com/casey/just?tab=readme-ov-file#packages)

Then `just` in the terminal to see available recipes.

## Deployment Instructions - with Docker

With these `just` recipes, you do not need to manage `uv` or `bun` on your host system, just have a [container runtime available](https://www.google.com/search?rls=en&q=docker+and+docker+alternatives&ie=UTF-8&oe=UTF-8)

- `just build-image` for iterative cache-enabled builds
- `just rebuild-image` for cache-less clean builds
- `just sh` - starts the Docker container, does not start app, just `bash`
- `just run` - starts the app, access at http://localhost:30000
  - this expects `backend/.env` to be filled out
  - env vars from the `.env` will be parsed/cleaned and passed to `docker run --env-file`
- `just live-sh` - drops into shell of live running container for debugging

## Deployment Instructions - Manual, without Docker

### A. Python Server
1. ```
   cd backend
   cp .env.example .env
   ```
3. In [`backend/.env`](https://github.com/philfung/perplexed/blob/main/backend/.env), fill in `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` credentials from [Google Custom Search API](https://developers.google.com/custom-search/v1/overview).
4. Fill in `GROQ_API_KEY` credentials from [Groq](https://console.groq.com/docs/quickstart).
5. Setup virtual environment, packages, and deploy the server
   ```
   uv venv
   . .venv/bin/activate
   uv pip install -r requirements.txt
   python app.py
   ```
   This is fine for dev testing.

   In production, in addition, you probably want to use gunicorn ([1](https://github.com/philfung/perplexed/blob/main/backend/gunicorn_config.py), [2](https://github.com/philfung/perplexed/blob/main/backend/script_start_gunicorn.sh)) and nginx ([1](https://github.com/philfung/perplexed/blob/main/backend/nginx.conf)) in conjunction with your python server ([1](https://github.com/philfung/perplexed/blob/main/backend/script_kill_servers.sh)) (utility scripts linked).
   
   Furthermore, in production environments you should set the secrets according the platform best practices, you should expect a secrets get/set API or CLI.
 
### B. React Frontend
1. ```
   cd frontend
   ```
2. Update `API_URL` in [`constants.js`](https://github.com/philfung/perplexed/blob/main/frontend/src/constants.js) to point to your server
3. [Install Bun](https://bun.sh/docs/installation) TL;DR: `curl -fsSL https://bun.com/install | bash`, or use `npx bun` if you already have `npx`
   ```
   bun install
   bun run build
   ```
3. In dev testing, to start the server:
   ```
   bun run start
   ```
   In production, to start the server:
   ```
   rm -rf node_modules
   rm -rf package-lock.json
   bun cache clean --force
   bun i --no-optional --omit=optional
   bun run build
   bun x serve -s build -l 30000
   ```
