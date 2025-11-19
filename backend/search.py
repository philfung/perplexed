import asyncio
import html
import httpx
import sys
import re
import urllib.parse
from typing import List, AsyncGenerator
from bs4 import BeautifulSoup
import datetime
import groq

from config import Model, Search, Secrets
from models import StreamSearchResponse, SearchAllStage, TokenUsage
from query_cache import QueryCache

# Initialize clients
# Workaround for groq/httpx compatibility issue

http_client = httpx.AsyncClient()
GROQ_CLIENT = groq.AsyncGroq(api_key=Secrets.GROQ_API_KEY, http_client=http_client)
GROQ_MODEL = 'openai/gpt-oss-20b'
GROQ_LIMIT_TOKENS_PER_MINUTE = 30000
WEBSEARCH_DOMAINS_BLACKLIST = ["quora.com", "www.quora.com"]
WEBSEARCH_RESULT_MIN_TOKENS = 50
WEBSEARCH_NUM_RESULTS_SLICE = 4
WEBSEARCH_READ_TIMEOUT_SECS = 5
WEBSEARCH_CONNECT_TIMEOUT_SECS = 3
WEBSEARCH_CONTENT_LIMIT_TOKENS = 1000

# Token character limit for scraping
TOKEN_CHAR_LIMIT = WEBSEARCH_CONTENT_LIMIT_TOKENS * 5  # Approximate chars per token

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


async def query_websearch_async(query: str, client: httpx.AsyncClient) -> List[WebSearchDocument]:
    """Query Google Custom Search API asynchronously."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": Secrets.GOOGLE_SEARCH_API_KEY, "cx": Secrets.GOOGLE_SEARCH_ENGINE_ID, "q": query}

    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        blob = response.json()

        if 'items' not in blob:
            print(f"Error querying Google: {blob}")
            return []

        results = blob['items']
        ret: List[WebSearchDocument] = []
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

    except Exception as e:
        print(f"Error in query_websearch_async: {e}")
        return []


async def scrape_webpage_async(url: str, client: httpx.AsyncClient) -> str:
    """Scrape webpage content asynchronously."""
    try:
        response = await client.get(
            url,
            timeout=httpx.Timeout(WEBSEARCH_READ_TIMEOUT_SECS, connect=WEBSEARCH_CONNECT_TIMEOUT_SECS),
            headers=Search.DEFAULT_HEADERS,
            follow_redirects=True,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract main text from the webpage
        main_text = ' '.join([p.text for p in soup.find_all('p')])
        main_text = limit_tokens(main_text, WEBSEARCH_CONTENT_LIMIT_TOKENS)

        return main_text

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""


async def scrape_webpages_async(
    websearch_docs: List[WebSearchDocument], max_workers: int = 5
) -> List[WebSearchDocument]:
    """Concurrently scrape multiple webpages with rate limiting."""
    # Configure client with connection pooling
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    timeout = httpx.Timeout(WEBSEARCH_READ_TIMEOUT_SECS, connect=WEBSEARCH_CONNECT_TIMEOUT_SECS)

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_workers)

        async def limited_scrape(doc: WebSearchDocument):
            async with semaphore:
                doc.text = await scrape_webpage_async(doc.url, client)
                return doc

        # Gather results, preserving order
        results = await asyncio.gather(*[limited_scrape(doc) for doc in websearch_docs], return_exceptions=False)

    return results


doc_id_regex = re.compile(r'DOCUMENT ID:(\d+)', re.IGNORECASE)


def replace_documents_with_markdown(text: str) -> str:
    return doc_id_regex.sub(r'**\[\1\]**', text)


async def query_chatbot_async(user_prompt: str, websearch_docs: List[WebSearchDocument]) -> tuple[str, TokenUsage]:
    """Query the LLM asynchronously and return response with token usage."""
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

    messages = [
        {"role": "system", "content": system_content},
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    response = await GROQ_CLIENT.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=4096,
    )

    response_message = response.choices[0].message.content

    # Extract token usage
    token_usage = TokenUsage(
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        total_tokens=response.usage.total_tokens,
    )

    return response_message, token_usage


async def search_all_async(user_prompt: str) -> AsyncGenerator[StreamSearchResponse, None]:
    """
    Execute the complete search pipeline asynchronously.
    Yields StreamSearchResponse objects for each stage.
    """
    total_token_usage = TokenUsage()

    try:
        # Stage 1: Search
        print_log(f"Starting search for: {user_prompt}")

        async with httpx.AsyncClient() as client:
            search_results = await query_websearch_async(user_prompt, client)

        yield StreamSearchResponse(
            stage=SearchAllStage.SEARCH,
            data={"results": [doc.to_dict() for doc in search_results], "count": len(search_results)},
        )

        if not search_results:
            yield StreamSearchResponse(stage=SearchAllStage.LLM, error="No search results found")
            return

        # Stage 2: Scrape
        print_log(f"Scraping {len(search_results)} webpages")

        scraped_docs = await scrape_webpages_async(search_results)

        # Filter out empty results
        valid_docs = [doc for doc in scraped_docs if doc.text]

        yield StreamSearchResponse(
            stage=SearchAllStage.SCRAPE, data={"scraped_count": len(valid_docs), "total_count": len(search_results)}
        )

        # Stage 3: LLM
        print_log(f"Querying LLM with {len(valid_docs)} documents")

        response_text, token_usage = await query_chatbot_async(user_prompt, valid_docs)
        total_token_usage.add(token_usage)

        yield StreamSearchResponse(
            stage=SearchAllStage.LLM,
            data={"response": response_text, "sources": [{"title": doc.title, "url": doc.url} for doc in valid_docs]},
            token_usage=total_token_usage.model_dump(),
        )

    except Exception as e:
        print_log(f"Error in search_all_async: {str(e)}")
        yield StreamSearchResponse(stage=SearchAllStage.LLM, error=f"Search pipeline error: {str(e)}")
