from enum import Enum
import bs4
import concurrent.futures
import groq
import pprint
import requests
import json
import sys
import time
from typing import List, Callable
import urllib.parse

from rate_limiter import RateLimiter

CONFIG = json.load(open('./config.json'))
GROQ_CLIENT = groq.Groq(api_key = CONFIG['GROQ_API_KEY'])
GROQ_MODEL = 'mixtral-8x7b-32768'
WEBSEARCH_DOMAINS_BLACKLIST = ["quora.com", "www.quora.com"]
WEBSEARCH_RESULT_MIN_TOKENS = 50
WEBSEARCH_NUM_RESULTS_SLICE = 4
WEBSEARCH_READ_TIMEOUT_SECS = 5
WEBSEARCH_CONNECT_TIMEOUT_SECS = 3
WEBSEARCH_CONTENT_LIMIT_TOKENS = 1000 
LIMIT_TOKENS_PER_MINUTE = 5000

class WebSearchDocument:
    def __init__(self, id, title, url, text=''):
        self.id = id
        self.title = title
        self.url = url
        self.text = text
    
    def __str__(self) -> str:
        return f"{self.title}\n{self.url}\n{self.text[:100]}"

def limit_tokens(input_string: str, N: int) -> str:
    tokens = input_string.split()
    limited_tokens = tokens[:N]
    return ' '.join(limited_tokens)

def count_tokens(input_string: str) -> int:
    tokens = input_string.split()
    return len(tokens)

def query_websearch(query: str)->list[WebSearchDocument]:
    url = f"https://www.googleapis.com/customsearch/v1?key={CONFIG['GOOGLE_SEARCH_API_KEY']}&cx={CONFIG['GOOGLE_SEARCH_ENGINE_ID']}&q={query}"
    response = requests.get(url)
    results = response.json()['items']
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
                id = id,
                title=title,
                url=link
            )
        )
    return ret

    # print(response.json())
def scrape_webpage(url: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    response = requests.get(url,  timeout=(WEBSEARCH_CONNECT_TIMEOUT_SECS, WEBSEARCH_READ_TIMEOUT_SECS), headers=headers)
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

def query_chatbot(user_prompt, websearch_docs: list[WebSearchDocument])->str:
    content_docs = ""
    for doc in websearch_docs:
        num_tokens = count_tokens(doc.text)
        if num_tokens < WEBSEARCH_RESULT_MIN_TOKENS:
            continue
        content_docs += f"====\nDOCUMENT ID:{doc.id}\nDOCUMENT TITLE:{doc.title}\nDOCUMENT URL:{doc.url}\nDOCUMENT TEXT:{doc.text}\n"
    system_prompt = "You are AI assistant for answering questions.  Using the provided documents, answer the user's question as thoroughly as possible.  Answer in a list of points, omitting inconclusive documents.  Format the answer as markdown.  After each sentence, cite the document information used using the exact syntax \"[DOCUMENT ID:<ID>]\".  Check over your work."

    system_content = f"====SYSTEM PROMPT:{system_prompt}\n{content_docs}\n====QUESTION: {user_prompt}"

    print(system_content)
    messages=[
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": user_prompt,
        }
    ]

    response = GROQ_CLIENT.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        tools=[],
        max_tokens=4096
    )

    response_message = response.choices[0].message.content
    return response_message

class SearchAllStage(Enum):
    STARTING = "Starting search"
    QUERYING_GOOGLE = "Querying Google"
    DOWNLOADING_WEBPAGES = "Downloading Webpages"
    QUERYING_LLM = "Querying LLM"
    RESULTS_READY = "Results ready"

class SearchAllResponse:
    def __init__(self, answer: str, num_tokens_used: int, websearch_docs: list[WebSearchDocument]):
        self.answer = answer
        self.num_tokens_used = num_tokens_used
        self.websearch_docs = websearch_docs

    def __str__(self) -> str:
        return f"Answer: {self.answer}\nTokens used: {self.num_tokens_used}\nWebsearch docs: {str(self.websearch_docs)}"

SearchAllListenerType = Callable[[List[WebSearchDocument], SearchAllStage], None]


def search_all(user_prompt: str, listener: SearchAllListenerType)->SearchAllResponse:
    time_start_google = time.time()
    if listener:
        listener([], SearchAllStage.QUERYING_GOOGLE)

    websearch_docs: list[WebSearchDocument] = query_websearch(user_prompt)

    websearch_docs_scraped = []
    time_start_scrape = time.time()

    if listener:
        listener(websearch_docs, SearchAllStage.DOWNLOADING_WEBPAGES)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        websearch_docs_scraped = list(executor.map(scrape_webpage_threaded, websearch_docs))

    num_tokens_used = sum([count_tokens(doc.text) for doc in websearch_docs_scraped])

    time_start_groq = time.time()
    if listener:
        listener(websearch_docs_scraped, SearchAllStage.QUERYING_LLM)

    answer = query_chatbot(user_prompt, websearch_docs_scraped)
    time_end = time.time()
    if listener:
        listener(websearch_docs_scraped, SearchAllStage.RESULTS_READY)
    print(f"Perf: Total={time_end-time_start_google}s Google={time_start_scrape - time_start_google}s Scrape={time_start_groq-time_start_scrape}s Groq={time_end-time_start_groq}s")
    return SearchAllResponse(answer=answer, num_tokens_used=num_tokens_used, websearch_docs=websearch_docs_scraped)

def search_all_listener(websearch_docs: List[WebSearchDocument], stage: SearchAllStage):
    if stage == SearchAllStage.QUERYING_GOOGLE:
        print("Querying Google...")

    elif stage == SearchAllStage.DOWNLOADING_WEBPAGES:
        for doc in websearch_docs:
            print(f"{doc.id}: {doc.title}; {doc.url}")
        print("Downloading webpages...")
    elif stage == SearchAllStage.QUERYING_LLM:
        print("Querying LLM...")
    elif stage == SearchAllStage.RESULTS_READY:
        print("Results ready")
        # for doc in websearch_docs:
        #     print(str(doc))
        

if __name__ == "__main__":
    rate_limiter = RateLimiter(LIMIT_TOKENS_PER_MINUTE)
    while True:
        user_prompt = input("Enter your question: ")
        if rate_limiter.is_over_limit():
            print("Rate limit exceeded.  Please wait a minute before trying again.")
        else:
            response = search_all(user_prompt=user_prompt, listener=search_all_listener)
            rate_limiter.record(num_tokens=response.num_tokens_used)
            print(str(response))