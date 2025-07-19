from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import logging
import time
from typing import AsyncGenerator, Dict, List
import json

from config import Deployment
from models import SearchRequest, StreamSearchResponse, SearchAllStage
from query_cache import QueryCache
from search import search_all_async

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Perplexed API", version="2.0.0", description="A search aggregation service with LLM-powered responses"
)

# Configure CORS
origins = Deployment.DOMAINS_ALLOW.split(",") if Deployment.DOMAINS_ALLOW else ["http://localhost:30000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize query cache
query_cache = QueryCache()


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response


@app.get("/test", response_model=str)
async def test():
    """Simple health check endpoint."""
    return "HELLO"


@app.get("/env", response_model=Dict)
async def env_report():
    """Simple env verification endpoint."""
    return Deployment.ENV_REPORT


def transform_backend_to_frontend_response(
    stage_response: StreamSearchResponse, websearch_docs: List[Dict] = None
) -> str:
    """Transform backend response format to match frontend expectations."""
    # Initialize websearch_docs list to persist across stages
    if websearch_docs is None:
        websearch_docs = []

    frontend_response = {
        "success": stage_response.error is None,
        "stage": None,
        "num_tokens_used": 0,
        "websearch_docs": websearch_docs,
        "answer": "",
        "message": stage_response.error or "",
    }

    # Map backend stages to frontend stages
    if stage_response.stage == SearchAllStage.SEARCH:
        frontend_response["stage"] = "Querying Google"
        if stage_response.data and "results" in stage_response.data:
            # Convert search results to websearch_docs format
            for idx, result in enumerate(stage_response.data["results"]):
                url = result.get("link", "")
                # Skip invalid URLs
                if not url or not url.startswith(("http://", "https://")):
                    continue
                frontend_response["websearch_docs"].append(
                    {
                        "id": idx + 1,
                        "title": result.get("title", "Untitled"),
                        "url": url,
                        "text": result.get("snippet", ""),
                    }
                )

    elif stage_response.stage == SearchAllStage.SCRAPE:
        frontend_response["stage"] = "Downloading Webpages"
        # Keep existing websearch_docs

    elif stage_response.stage == SearchAllStage.LLM:
        frontend_response["stage"] = "Results ready"
        if stage_response.data and "response" in stage_response.data:
            frontend_response["answer"] = stage_response.data["response"]
        if stage_response.token_usage:
            frontend_response["num_tokens_used"] = stage_response.token_usage.get("total_tokens", 0)
        # Update websearch_docs with sources from LLM response if available
        if stage_response.data and "sources" in stage_response.data:
            # Update the websearch_docs with scraped content
            for idx, source in enumerate(stage_response.data["sources"]):
                if idx < len(frontend_response["websearch_docs"]):
                    frontend_response["websearch_docs"][idx]["title"] = source.get(
                        "title", frontend_response["websearch_docs"][idx]["title"]
                    )

    return json.dumps(frontend_response) + "[/PERPLEXED-SEPARATOR]"


@app.post("/stream_search")
async def stream_search(request: SearchRequest) -> StreamingResponse:
    """
    Stream search results with multi-stage processing:
    1. Search stage - Google Custom Search
    2. Scrape stage - Web content extraction
    3. LLM stage - AI-powered response generation
    """
    user_prompt = request.user_prompt

    async def generate() -> AsyncGenerator[str, None]:
        """Generate streaming responses for each stage."""
        websearch_docs = []  # Persist websearch_docs across stages

        try:
            # Check cache first
            cached_response = query_cache.get(user_prompt)
            if cached_response:
                logger.info(f"Cache hit for query: {user_prompt}")
                # Create a response that matches frontend expectations
                frontend_cache_response = {
                    "success": True,
                    "stage": "Results ready",
                    "num_tokens_used": cached_response.get("token_usage", {}).get("total_tokens", 0),
                    "websearch_docs": [],
                    "answer": cached_response["data"].get("response", ""),
                    "message": "",
                }

                # Add sources as websearch_docs if available
                if "sources" in cached_response["data"]:
                    for idx, source in enumerate(cached_response["data"]["sources"]):
                        url = source.get("url", "")
                        # Skip invalid URLs
                        if not url or not url.startswith(("http://", "https://")):
                            continue
                        frontend_cache_response["websearch_docs"].append(
                            {"id": idx + 1, "title": source.get("title", "Untitled"), "url": url, "text": ""}
                        )

                yield json.dumps(frontend_cache_response) + "[/PERPLEXED-SEPARATOR]"
                return

            logger.info(f"Processing new query: {user_prompt}")

            # Execute search pipeline
            async for stage_response in search_all_async(user_prompt):
                # Update websearch_docs from search stage
                if (
                    stage_response.stage == SearchAllStage.SEARCH
                    and stage_response.data
                    and "results" in stage_response.data
                ):
                    websearch_docs = []
                    for idx, result in enumerate(stage_response.data["results"]):
                        url = result.get("link", "")
                        # Ensure URL is valid
                        if not url or not url.startswith(("http://", "https://")):
                            continue
                        websearch_docs.append(
                            {
                                "id": idx + 1,
                                "title": result.get("title", "Untitled"),
                                "url": url,
                                "text": result.get("snippet", ""),
                            }
                        )

                yield transform_backend_to_frontend_response(stage_response, websearch_docs)

                # Cache the final LLM response
                if stage_response.stage == SearchAllStage.LLM and stage_response.data:
                    query_cache.set(
                        user_prompt, {"data": stage_response.data, "token_usage": stage_response.token_usage}
                    )

        except Exception as e:
            logger.error(f"Error in stream_search: {str(e)}")
            error_response = {
                "success": False,
                "stage": None,
                "num_tokens_used": 0,
                "websearch_docs": [],
                "answer": "",
                "message": f"An error occurred: {str(e)}",
            }
            yield json.dumps(error_response) + "[/PERPLEXED-SEPARATOR]"

    return StreamingResponse(
        generate(),
        media_type="application/json",
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "no-cache"},
    )


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return {"error": exc.detail}


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return {"error": "Internal server error"}


if __name__ == "__main__":
    import uvicorn
    from config import Deployment

    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=Deployment.FASTAPI_APP_PORT, reload=True)
