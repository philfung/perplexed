## Perplexed 
Open-source app inspired by the amazing web search product, Perplexity.

[**Live Demo**](https://d37ozmhmvu2kcg.cloudfront.net/)

<img width="279" alt="Screenshot 2024-05-08 at 1 23 35 PM" src="https://github.com/philfung/perplexed/assets/1054593/28ac5a06-abc6-4a8d-ab60-36f3e1f1e596">
<img width="277" alt="Screenshot 2024-05-08 at 1 24 33 PM" src="https://github.com/philfung/perplexed/assets/1054593/a932819e-6e24-45c6-9138-234e1870a558">

## Implementation
Given a user query, the app conducts a web search,
downloads the top N resulting web pages, then analyzes those pages 
with an LLM.  

<img height="400" alt="Screenshot 2024-11-16 at 10 06 03 AM" src="https://github.com/user-attachments/assets/e88ff3ee-2efc-4a36-8427-fcf90141a083">

The LLM can be any smaller, consumer-grade with at least 5k context window (assuming each web page ~1k tokens).

## Deployment Instructions

### Python Server
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
 
### React Frontend
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
