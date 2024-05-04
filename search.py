import bs4
import concurrent.futures
import groq
import pprint
import requests
import json
import sys
import time
import urllib.parse

CONFIG = json.load(open('config.json'))
GROQ_CLIENT = groq.Groq(api_key = CONFIG['GROQ_API_KEY'])
GROQ_MODEL = 'mixtral-8x7b-32768'
WEBSEARCH_DOMAINS_BLACKLIST = ["quora.com", "www.quora.com"]
WEBSEARCH_RESULT_MIN_TEXT_LENGTH = 30
WEBSEARCH_NUM_RESULTS_SLICE = 3
WEBSEARCH_READ_TIMEOUT_SECS = 5
WEBSEARCH_CONNECT_TIMEOUT_SECS = 3

WEBSEARCH_CONTENT_LIMIT_TOKENS = 1000 # TODO: implement


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
        if len(doc.text) < WEBSEARCH_RESULT_MIN_TEXT_LENGTH:
            continue
        content_docs += f"====\nDOCUMENT ID:{doc.id}\nDOCUMENT TITLE:{doc.title}\nDOCUMENT URL:{doc.url}\nDOCUMENT TEXT:{doc.text}\n"
    system_prompt = "You are AI assistant for answering questions.  Using the provided documents, answer the user's question as thoroughly as possible.  Answer in a list of points, omitting inconclusive documents.  Format the answer as markdown.  After each sentence, cite the document information used using the syntax \"[document=ID]\".  Check over your work."

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

def search_all(user_prompt: str)->str:
    time_start_google = time.time()
    print("----Querying Google...----")
    websearch_docs: list[WebSearchDocument] = query_websearch(user_prompt)

    websearch_docs_scraped = []
    time_start_scrape = time.time()
    print("----Downloading webpages...----")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        websearch_docs_scraped = list(executor.map(scrape_webpage_threaded, websearch_docs))

    # for websearch_doc in websearch_docs_scraped:
    #     print(str(websearch_doc))

    time_start_groq = time.time()
    print("----Asking Groq...----")

    answer = query_chatbot(user_prompt, websearch_docs_scraped)
    print(answer)
    time_end = time.time()
    print(f"Perf: Total={time_end-time_start_google}s Google={time_start_scrape - time_start_google}s Scrape={time_start_groq-time_start_scrape}s Groq={time_end-time_start_groq}s")
    return answer

if __name__ == "__main__":
    user_prompt = "What is the best way to skin a cat?"
    answer = search_all(user_prompt)
    print(answer)