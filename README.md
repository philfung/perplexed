## Perplexed 
Open-source app inspired by the amazing web search product, Perplexity.

<img width="279" alt="Screenshot 2024-05-08 at 1 23 35 PM" src="https://github.com/philfung/perplexed/assets/1054593/28ac5a06-abc6-4a8d-ab60-36f3e1f1e596">
<img width="279" alt="Screenshot 2024-05-08 at 1 24 33 PM" src="https://github.com/philfung/perplexed/assets/1054593/a932819e-6e24-45c6-9138-234e1870a558">

## Implementation
Given a user query, the app conducts a web search,
downloads the top N resulting web pages, then analyzes those pages 
with an LLM.  
The LLM can be any smaller, consumer-grade with at least 5k context window (assuming each web page ~1k tokens)

## Deployment Instructions

### Python Server
1. ```
   cd backend
   copy config.json.sample config.json
   ```
3. In `config.json`, fill in `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` credentials from [Google Custom Search API](https://developers.google.com/custom-search/v1/overview).
4. Fill in `GROQ_API_KEY` credentials from [Groq](https://console.groq.com/docs/quickstart).
5. Setup virtual environment, packages, and deploy the server
   ```
   virtualenv venv
   . venv/bin/activate
   pip install -r requirements.txt
   python app.py
   ```
   (In the future, only need to do:
   ```
   . venv/bin/activate
   python app.py
   ````
### React Frontend
1. Update `API_URL` in `constants.js` to point to your server
2. ```
   npm install
   ```
3. In dev, to start the server:
   ```
   npm run start
   ```
   In production, to start the server:
   ```
   npm run build
   npm install -g serve
   server -s build
   ```
