from enum import Enum
import bs4
import datetime
import groq
import html
import os
import requests
import sys
import re
import urllib.parse

from query_cache import QueryCache
from config import Model, Search, Secrets

current_dir_path = os.path.dirname(os.path.realpath(__file__))
GROQ_CLIENT = groq.Groq(api_key=Secrets.GROQ_API_KEY)
# GROQ_MODEL = 'mixtral-8x7b-32768'
GROQ_MODEL = 'llama3-8b-8192'
# GROQ_MODEL = 'llama3-groq-8b-8192-tool-use-preview'
GROQ_LIMIT_TOKENS_PER_MINUTE = 30000
WEBSEARCH_DOMAINS_BLACKLIST = ["quora.com", "www.quora.com"]
WEBSEARCH_RESULT_MIN_TOKENS = 50
WEBSEARCH_NUM_RESULTS_SLICE = 4
WEBSEARCH_READ_TIMEOUT_SECS = 5
WEBSEARCH_CONNECT_TIMEOUT_SECS = 3
WEBSEARCH_CONTENT_LIMIT_TOKENS = 1000

query_cache = QueryCache()


class WebSearchDocument:
    def __init__(self, id, title, url, text=''):
        self.id = id
        self.title = html.escape(title)
        self.url = url
        self.text = html.escape(text)

    def __str__(self) -> str:
        return f"{self.title}\n{self.url}\n{self.text[:100]}"

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'text': self.text,
        }


def print_log(*args, **kwargs):
    datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print('[' + datestr + ']', *args, file=sys.stderr, **kwargs)


def limit_tokens(input_string: str, N: int) -> str:
    tokens = input_string.split()
    limited_tokens = tokens[:N]
    return ' '.join(limited_tokens)


def count_tokens(input_string: str) -> int:
    tokens = input_string.split()
    return len(tokens)


def query_websearch(query: str) -> list[WebSearchDocument]:
    url = f"https://www.googleapis.com/customsearch/v1?key={Secrets.GOOGLE_SEARCH_API_KEY}&cx={Secrets.GOOGLE_SEARCH_ENGINE_ID}&q={query}"
    response = requests.get(url)
    blob = response.json()
    if 'items' not in blob:
        print(f"Error querying Google: {blob}")
        return []
    results = blob['items']
    ret: list[WebSearchDocument] = []
    id = 0
    for result in results:
        link = result['link']
        title = result['title']
        link_parsed = urllib.parse.urlparse(link)
        if link_parsed.netloc in WEBSEARCH_DOMAINS_BLACKLIST:
            continue
        id += 1
        if id > WEBSEARCH_NUM_RESULTS_SLICE:
            break
        ret.append(
            WebSearchDocument(
                id=id,
                title=title,
                url=link,
            )
        )
    return ret

    # print(response.json())


def scrape_webpage(url: str):
    response = requests.get(
        url,
        timeout=(WEBSEARCH_CONNECT_TIMEOUT_SECS, WEBSEARCH_READ_TIMEOUT_SECS),
        headers=Search.DEFAULT_HEADERS,
    )
    soup = bs4.BeautifulSoup(response.text, 'html.parser')

    # Extract main text from the webpage
    # This will vary depending on the structure of the webpage
    # Here we are assuming that the main text is within <p> tags
    main_text = ' '.join([p.text for p in soup.find_all('p')])
    main_text = limit_tokens(main_text, WEBSEARCH_CONTENT_LIMIT_TOKENS)

    return main_text


def scrape_webpage_threaded(websearch_doc):
    try:
        text = scrape_webpage(websearch_doc.url)
    except Exception as e:
        print(f"Error scraping {websearch_doc.url}: {e}")
        text = ""
    websearch_doc.text = text
    return websearch_doc


doc_id_regex = re.compile(r'DOCUMENT ID:(\d+)', re.IGNORECASE)


def replace_documents_with_markdown(text: str) -> str:
    return doc_id_regex.sub(r'**\[\1\]**', text)


def query_chatbot(user_prompt, websearch_docs: list[WebSearchDocument]) -> str:
    value = query_cache.get(user_prompt)
    if value:
        print_log("query_chatbot: cache hit for:", user_prompt)
        return value
    content_docs = ""
    for doc in websearch_docs:
        num_tokens = count_tokens(doc.text)
        if num_tokens < WEBSEARCH_RESULT_MIN_TOKENS:
            continue
        content_docs += (
            f"====\nDOCUMENT ID:{doc.id}\n"
            f"DOCUMENT TITLE:{doc.title}\n"
            f"DOCUMENT URL:{doc.url}\n"
            f"DOCUMENT TEXT:{doc.text}\n"
        )

    system_content = f"====SYSTEM PROMPT:{Model.SYSTEM_PROMPT}\n{content_docs}\n====QUESTION: {user_prompt}"

    # print(system_content)
    messages = [
        {"role": "system", "content": system_content},
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    response = GROQ_CLIENT.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        tools=[],
        max_tokens=4096,
    )

    response_message = response.choices[0].message.content
    # response_message = replace_documents_with_markdown(response_message)

    if user_prompt and response_message:
        query_cache.set(user_prompt, response_message)
    return response_message


class SearchAllStage(Enum):
    STARTING = "Starting search"
    QUERIED_GOOGLE = "Querying Google"
    DOWNLOADED_WEBPAGES = "Downloading Webpages"
    QUERIED_LLM = "Querying LLM"
    RESULTS_READY = "Results ready"
