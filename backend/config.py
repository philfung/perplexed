import os

class Secrets:
    GOOGLE_SEARCH_API_KEY = os.environ["GOOGLE_SEARCH_API_KEY"]
    GOOGLE_SEARCH_ENGINE_ID = os.environ["GOOGLE_SEARCH_ENGINE_ID"]
    GROQ_API_KEY = os.environ["GROQ_API_KEY"]

class Deployment:
    DOMAINS_ALLOW = os.environ.get("DOMAINS_ALLOW", "http://localhost:30000").split(",")

class Search:
    JSON_STREAM_SEPARATOR = "[/PERPLEXED-SEPARATOR]"
