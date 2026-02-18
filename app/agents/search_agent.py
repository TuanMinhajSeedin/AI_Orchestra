from typing import List, Dict, Any
import logging

from app.state import ResearchState
from app.tools.web_search import WebSearchTool
from app.tools.vector_store import VectorStore
from app.tools.url_loader import UrlLoader


logger = logging.getLogger(__name__)


class WebSearchAgent:
    """
    WebSearchAgent

    Goal: Retrieve research content based on planner-produced search_queries.

    Input:  state.search_queries (from PlannerAgent), or falls back to state.user_query
    Output: state.search_results as a list of dictionaries with keys:
      - title
      - source
      - content
      - url
    """

    def __init__(self, web_search: WebSearchTool, vector_store: VectorStore, url_loader: UrlLoader) -> None:
        self.web_search = web_search
        # vector_store is currently unused but kept for easy future RAG extension
        self.vector_store = vector_store
        self.url_loader = url_loader

    def run_searches(self, queries: List[str]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for q in queries:
            logger.info("WebSearchAgent: Running web search for query: %s", q)
            web_results = self.web_search.search(q)
            results.extend(web_results)
        return results

    def __call__(self, state: ResearchState) -> ResearchState:
        # Increment attempt counter so the orchestrator can implement
        # simple retry logic if results come back empty.
        state.search_attempts += 1

        queries = state.search_queries or [state.user_query]
        state.search_results = self.run_searches(queries)
        logger.info(
            "WebSearchAgent: Completed search attempt %d, retrieved %d results.",
            state.search_attempts,
            len(state.search_results),
        )

        # After collecting search_results, mimic trail/test_web_search.py:
        # use UnstructuredURLLoader (via extract_content) to fetch full page
        # content for the retrieved URLs, and index them into the vector store.
        urls: List[str] = [
            r.get("url") for r in state.search_results if r.get("url")
        ]  # type: ignore[assignment]
        if urls:
            logger.info(
                "WebSearchAgent: Loading full content for %d URLs via UnstructuredURLLoader.",
                len(urls),
            )
            try:
                docs = self.url_loader.extract_content(urls)
                texts = [doc.page_content for doc in docs if getattr(doc, "page_content", None)]
                if texts:
                    self.vector_store.add_documents(texts)
                    logger.info(
                        "WebSearchAgent: Indexed %d documents into the vector store.",
                        len(texts),
                    )
            except Exception as exc:
                logger.info(
                    "WebSearchAgent: Failed to load URLs via UnstructuredURLLoader: %s",
                    exc,
                )

        return state


