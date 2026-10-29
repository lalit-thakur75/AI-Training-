from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.schemas.chat import SourceReference
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    max_results: Optional[int] = 5

class SearchResponse(BaseModel):
    query: str
    results_count: int
    sources: List[SourceReference]

@router.post("", response_model=SearchResponse)
async def perform_search(request: SearchRequest):
    """
    Dedicated web search endpoint returning verified web results with URLs.
    """
    sources = SearchService.search_web(request.query, max_results=request.max_results)
    return SearchResponse(
        query=request.query,
        results_count=len(sources),
        sources=sources
    )
