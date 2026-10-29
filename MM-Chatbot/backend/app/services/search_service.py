import logging
import asyncio
from typing import List
from app.config import settings
from app.schemas.chat import SourceReference

logger = logging.getLogger(__name__)


def _ddg_search_sync(query: str, max_results: int) -> List[SourceReference]:
    """Synchronous DuckDuckGo search helper — runs in a thread pool."""
    sources = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            for r in results:
                title = r.get("title", "Web Source")
                href = r.get("href", "")
                body = r.get("body", "")
                if href:
                    sources.append(
                        SourceReference(
                            title=title,
                            source_type="web",
                            url_or_file=href,
                            snippet=body[:250] + "..." if len(body) > 250 else body
                        )
                    )
    except Exception as e:
        logger.warning(f"DuckDuckGo search error: {e}")
    return sources


class SearchService:
    @staticmethod
    async def search_web_async(query: str, max_results: int = 4) -> List[SourceReference]:
        """
        Async-safe web search using the configured provider.
        DuckDuckGo runs in a thread pool to avoid blocking the event loop.
        """
        if not query.strip():
            return []

        if settings.SEARCH_PROVIDER == "duckduckgo":
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _ddg_search_sync, query, max_results)

        elif settings.SEARCH_PROVIDER == "tavily" and settings.TAVILY_API_KEY:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": settings.TAVILY_API_KEY,
                            "query": query,
                            "max_results": max_results
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return [
                            SourceReference(
                                title=r.get("title", "Web Source"),
                                source_type="web",
                                url_or_file=r.get("url", ""),
                                snippet=r.get("content", "")[:250]
                            )
                            for r in data.get("results", [])
                        ]
            except Exception as e:
                logger.warning(f"Tavily search error: {e}")

        return []

    @staticmethod
    def search_web(query: str, max_results: int = 4) -> List[SourceReference]:
        """
        Synchronous wrapper kept for backward-compatibility with any sync callers.
        NOTE: Prefer search_web_async() from async contexts.
        """
        return _ddg_search_sync(query, max_results)

    @staticmethod
    def build_search_context(sources: List[SourceReference]) -> str:
        """Formats retrieved search results for LLM prompt injection."""
        if not sources:
            return ""

        context_lines = ["\n[WEB SEARCH RESULTS - CURRENT INFORMATION]:"]
        for idx, src in enumerate(sources, 1):
            context_lines.append(f"{idx}. [{src.title}]({src.url_or_file})\nSummary: {src.snippet}")
        context_lines.append("\nPlease answer the question using the retrieved web results above when applicable, citing the source titles and URLs.")
        return "\n".join(context_lines)
