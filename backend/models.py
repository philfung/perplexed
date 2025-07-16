from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class SearchRequest(BaseModel):
    user_prompt: str = Field(..., min_length=1, description="Search query")


class SearchAllStage(str, Enum):
    SEARCH = "search"
    SCRAPE = "scrape"
    LLM = "llm"


class StreamSearchResponse(BaseModel):
    stage: SearchAllStage
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None

    def to_json_data(self) -> str:
        """Convert to JSON string with custom separator for streaming."""
        return self.model_dump_json() + "[/PERPLEXED-SEPARATOR]"


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: 'TokenUsage') -> 'TokenUsage':
        """Add token usage from another instance."""
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens
        return self


class SearchResult(BaseModel):
    """Model for search result from Google Custom Search API."""

    title: str
    link: str
    snippet: str
    displayLink: Optional[str] = None
