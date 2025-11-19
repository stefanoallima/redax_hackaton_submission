"""
API Models for CodiceCivile.ai
Pydantic models based on OpenAPI specification
See: docs/openapi.yaml
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator


# ARTICLE MODELS

class Article(BaseModel):
    """Legal article model"""
    id: str = Field(..., description="Unique article identifier")
    article_number: str = Field(..., description="Article number (e.g., '1234')")
    book: int = Field(..., ge=1, le=6, description="Book number (1-6)")
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article full content")
    keywords: List[str] = Field(default_factory=list, description="Article keywords")
    last_modified: Optional[str] = Field(None, description="Last modification date (ISO format)")
    embedding: Optional[List[float]] = Field(None, description="768-dimensional embedding vector")

    class Config:
        schema_extra = {
            "example": {
                "id": "art-1234",
                "article_number": "1234",
                "book": 4,
                "title": "Diritti del consumatore",
                "content": "Il consumatore ha diritto...",
                "keywords": ["consumatore", "contratti", "diritti"],
                "last_modified": "2024-01-15"
            }
        }


ArticleType = Literal["contract", "property", "family", "succession", "obligations"]


class ArticleFilter(BaseModel):
    """Article filtering criteria"""
    book: Optional[int] = Field(None, ge=1, le=6)
    article_type: Optional[ArticleType] = None


# SEARCH MODELS

class DateRange(BaseModel):
    """Date range for filtering"""
    start: str = Field(..., description="Start date (ISO format)")
    end: str = Field(..., description="End date (ISO format)")


class SearchFilter(BaseModel):
    """Search filters"""
    book: Optional[int] = Field(None, ge=1, le=6)
    article_type: Optional[ArticleType] = None
    date_range: Optional[DateRange] = None


SortBy = Literal["relevance", "date", "article_number"]


class SearchRequest(BaseModel):
    """Semantic search request"""
    query: str = Field(..., min_length=1, description="Natural language search query")
    filters: Optional[SearchFilter] = None
    limit: int = Field(10, ge=1, le=50, description="Number of results")
    sort_by: SortBy = Field("relevance", description="Sort order")

    class Config:
        schema_extra = {
            "example": {
                "query": "diritti del consumatore nei contratti",
                "filters": {"book": 4},
                "limit": 10,
                "sort_by": "relevance"
            }
        }


class SearchResult(BaseModel):
    """Single search result"""
    article: Article
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score (0-1)")
    matched_snippet: Optional[str] = Field(None, description="Relevant excerpt")


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: int


# CHAT MODELS

MessageRole = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    """Chat message"""
    role: MessageRole
    content: str = Field(..., min_length=1)


class ChatContext(BaseModel):
    """Optional article context for chat"""
    article_id: Optional[str] = None
    article_title: Optional[str] = None
    article_content: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request"""
    messages: List[ChatMessage] = Field(..., min_items=1)
    context: Optional[ChatContext] = None
    stream: bool = Field(False, description="Enable streaming responses")

    class Config:
        schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "Cosa dice l'articolo 1234?"}
                ],
                "stream": False
            }
        }


class ChatResponse(BaseModel):
    """Chat response"""
    id: str
    role: Literal["assistant"]
    content: str
    related_articles: List[str] = Field(default_factory=list, description="Cited article IDs")
    timestamp: datetime


# EMBEDDINGS MODELS

class EmbeddingRequest(BaseModel):
    """Embedding generation request"""
    text: str = Field(..., max_length=8000, description="Text to embed")


class EmbeddingResponse(BaseModel):
    """Embedding response"""
    embedding: List[float] = Field(..., description="768-dimensional vector")
    model: str = Field(..., description="Model name")

    @validator('embedding')
    def validate_embedding_dimension(cls, v):
        if len(v) != 768:
            raise ValueError('Embedding must be 768-dimensional')
        return v


# USER MODELS

class Bookmark(BaseModel):
    """User bookmark"""
    article: Article
    bookmarked_at: datetime


class BookmarksResponse(BaseModel):
    """User bookmarks response"""
    bookmarks: List[Bookmark]


class AddBookmarkRequest(BaseModel):
    """Add bookmark request"""
    article_id: str = Field(..., min_length=1)


class AddBookmarkResponse(BaseModel):
    """Add bookmark response"""
    success: bool
    bookmark_id: str


class SearchHistoryItem(BaseModel):
    """Search history item"""
    id: str
    query: str
    results_count: int
    created_at: datetime


class SearchHistoryResponse(BaseModel):
    """Search history response"""
    history: List[SearchHistoryItem]


# RELATED ARTICLES MODELS

class RelatedArticleResult(BaseModel):
    """Related article result"""
    article: Article
    similarity_score: float = Field(..., ge=0, le=1)


class RelatedArticlesResponse(BaseModel):
    """Related articles response"""
    article_id: str
    related_articles: List[RelatedArticleResult]


# PAGINATION MODELS

class PaginationParams(BaseModel):
    """Pagination parameters"""
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    data: List[Article]
    total: int
    limit: int
    offset: int


# ERROR MODELS

class ErrorDetail(BaseModel):
    """API error details"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")


class APIError(BaseModel):
    """API error response"""
    error: ErrorDetail

    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Invalid article ID provided",
                    "details": {}
                }
            }
        }


# HELPER CONSTANTS

BOOK_NAMES = {
    1: "Persone e Famiglia",
    2: "Successioni",
    3: "Proprieta",
    4: "Obbligazioni",
    5: "Lavoro",
    6: "Tutela dei Diritti"
}

ARTICLE_TYPE_NAMES = {
    "contract": "Contratti",
    "property": "Proprieta",
    "family": "Famiglia",
    "succession": "Successioni",
    "obligations": "Obbligazioni"
}
