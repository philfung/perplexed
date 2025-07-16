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

## Development

To take advantage of the configured build steps, our recommended tools are:

- [any container runtime](https://www.google.com/search?rls=en&q=docker+and+docker+alternatives&ie=UTF-8&oe=UTF-8)
- [`just`](https://github.com/casey/just?tab=readme-ov-file#packages)
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
  - [`uv tool install pre-commit`](https://pre-commit.com/#install)
  - [`uv tool install ruff`](https://docs.astral.sh/ruff/installation/)

### Workflow and Local Deployment

- run `just` in the terminal to see available recipes. We support recipes to launch the app in dev, staging and production modes.
  - dev: run app as two processes on localhost
  - staging: run app inside a docker container as a single http service, fronted by `nginx`
  - production: a variant of staging with diff env vars
- e.g. if testing in staging, fill out `frontend/.env.staging` then `just build-image-staging && just run` to take your app into the container and launch the server on `http://localhost:30000`

## Deployment Instructions - Manual, without our justfile recipes

Refer to the justfile for step by step recipes. The following describes the requirements if you choose to re-implement in a different environment.

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
6. Wherever you run this backend, you need to define env var `DOMAINS_ALLOW` to match the frontend domain the browser sees.

   For production, check `docker/` for example containerized/cloud process management scripts.

   You may choose to do add-on engineering with `supervisord`, `nginx` or a variety of modifications.
   
   Furthermore, in production environments you should set the secrets according the platform best practices, you should expect a secrets get/set API or CLI, e.g. in our Fly.io example you would use `fly secrets set|unset` prior to deploying your app.
 
### B. React Frontend

The React app can be compiled into a static site you can serve with `nginx`, `npx serve` or your choice of framework.

1. ```
   cd frontend
   ```
2. Update `REACT_APP_API_URL` in [`constants.js`](https://github.com/philfung/perplexed/blob/main/frontend/src/constants.js) to point to your server
3. [Install Bun](https://bun.sh/docs/installation) TL;DR: `curl -fsSL https://bun.com/install | bash`, or use `npx bun` if you already have `npx`
   ```
   bun install
   bun run build:dev
   bun run build:staging
   bun run build:prod
   ```
   
   There are justfile recipes for all of the above.
3. In dev testing, to start the server:
   ```
   just frontend-dev
   PORT=30000 bun start ./build-[dev|staging|prod]
   ```
4. In staging the docker app on your host, to start the server:
   
   Fill in values in `frontend/.env.staging`.
   Refer to the justfile recipes for implementation details.
   
   ```
   just run
   ```

# Contributors

- `git add -u` your modified files and run `pre-commit` to perform `ruff` lint/format checks

# TODOS

- [ ] Clarify the pre-existing Cloudfront deployment strategy for the frontend
- [ ] Create `./deployment/cloudflare` example for [Cloudflare Containers](https://developers.cloudflare.com/containers/)
