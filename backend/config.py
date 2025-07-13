import os


class Secrets:
    GOOGLE_SEARCH_API_KEY = os.environ["GOOGLE_SEARCH_API_KEY"]
    GOOGLE_SEARCH_ENGINE_ID = os.environ["GOOGLE_SEARCH_ENGINE_ID"]
    GROQ_API_KEY = os.environ["GROQ_API_KEY"]


class Deployment:
    DOMAINS_ALLOW = os.environ.get("DOMAINS_ALLOW", "http://localhost:30000").split(",")


class Model:
    SYSTEM_PROMPT = "You are AI assistant for answering questions.  Using the provided documents, answer the user's question as thoroughly as possible.  Omit inconclusive documents.  Make the answer eloquent and well-written, and at least 2 paragraphs long. Use numbered lists as much as possible.  Format the answer as Markdown, make sure the formatting is beautiful, that there are numbers used at the beginning of each item of a list, and two full newlines between each point in the list.  DO NOT cite the Document or Document ID in the response."  # noqa: E501 fmt: off


class Search:
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'  # noqa: E501 fmt: off
    }
    JSON_STREAM_SEPARATOR = "[/PERPLEXED-SEPARATOR]"
