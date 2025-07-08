## <img height="25" src="https://github.com/philfung/perplexed/blob/main/frontend/public/images/perplexity-color.svg"/> Perplexed
#### An open-source app inspired by the amazing web search product, Perplexity.
[![Last Demo](https://img.shields.io/badge/Live-Demo-green)](https://d37ozmhmvu2kcg.cloudfront.net/)
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

## Deployment Instructions

### A. Python Server
1. ```
   cd backend
   copy config.json.sample config.json
   ```
3. In [`config.json`](https://github.com/philfung/perplexed/blob/main/backend/config.json.example), fill in `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` credentials from [Google Custom Search API](https://developers.google.com/custom-search/v1/overview).
4. Fill in `GROQ_API_KEY` credentials from [Groq](https://console.groq.com/docs/quickstart).
5. Setup virtual environment, packages, and deploy the server
   ```
   virtualenv venv
   . venv/bin/activate
   pip install -r requirements.txt
   python app.py
   ```
   This is fine for dev testing.

   In production, in addition, you probably want to use gunicorn ([1](https://github.com/philfung/perplexed/blob/main/backend/gunicorn_config.py), [2](https://github.com/philfung/perplexed/blob/main/backend/script_start_gunicorn.sh)) and nginx ([1](https://github.com/philfung/perplexed/blob/main/backend/nginx.conf)) in conjunction with your python server ([1](https://github.com/philfung/perplexed/blob/main/backend/script_kill_servers.sh)) (utility scripts linked).
 
### B. React Frontend
1. ```
   cd frontend
   ```
2. Update `API_URL` in [`constants.js`](https://github.com/philfung/perplexed/blob/main/frontend/src/constants.js) to point to your server
3. ```
   npm install
   npm run build
   ```
3. In dev testing, to start the server:
   ```
   npm run start
   ```
   In production, to start the server:
   ```
   npm i -g npm@latest
   rm -rf node_modules
   rm -rf package-lock.json
   npm cache clean --force
   npm i --no-optional --omit=optional
   npm run build
   npm install -g serve
   server -s build
   ```
