import os

class Secrets:
    GOOGLE_SEARCH_API_KEY = os.environ.get("GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

class Deployment:
    DOMAINS_ALLOW = os.environ.get("DOMAINS_ALLOW", "http://localhost:30000").split(",")

class Search:
    JSON_STREAM_SEPARATOR = "[/PERPLEXED-SEPARATOR]"
