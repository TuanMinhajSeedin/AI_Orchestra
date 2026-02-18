from typing import List, Dict, Any
import os
import logging

import requests
from dotenv import load_dotenv



# Ensure we can read API keys from a .env file
load_dotenv()



logger = logging.getLogger(__name__)


class WebSearchTool:
    """
    Web search tool backed by Serper (google.serper.dev), with a mock fallback.

    - Reads SERPER_API_KEY from the environment (or .env).
    - If the key is missing or a request fails, returns simulated results.

    Each result dictionary has the shape:
    {
      "title": str,
      "source": str,
      "content": str,
      "url": str,
    }
    """

    def __init__(self) -> None:
        # API key for https://google.serper.dev/search
        self.api_key = os.getenv("SERPER_API_KEY")

    def _mock_results(self, query: str, k: int = 3) -> List[Dict[str, str]]:
        return [
            {
                "title": f"Mock result {i + 1} for: {query}",
                "source": "mock",
                "content": f"This is mocked web content snippet {i + 1} for query: {query}.",
                "url": f"https://example.com/mock/{i+1}?q={query}",
            }
            for i in range(k)
        ]

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        # If no API key, immediately return mock data.
        if not self.api_key:
            logger.info(
                "WebSearchTool: SERPER_API_KEY not set; returning mock results for query: %s",
                query,
            )
            return self._mock_results(query, k=min(k, 3))

        try:
            logger.info("WebSearchTool: Calling Serper API for query: %s", query)
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json",
                },
                json={"q": query},
                timeout=10,
                
            )
            resp.raise_for_status()
            data = resp.json()
            # Serper returns 'organic' for standard search results
            organic = data.get("organic") or data.get("organic_results") or []
            results: List[Dict[str, Any]] = []
            for item in organic[:k]:
                title = item.get("title") or item.get("snippet") or query
                url = item.get("link") or item.get("url") or ""
                # Serper doesn't always provide 'source'; default to 'serper'
                source = item.get("source") or "serper"
                content = item.get("snippet") or item.get("title") or ""
                results.append(
                    {
                        "title": title,
                        "source": source,
                        "content": content,
                        "url": url,
                    }
                )
            if not results:
                logger.info(
                    "WebSearchTool: No organic results from Serper; using mock results."
                )
            # Fallback to mock results if Serper returns nothing useful
            return results or self._mock_results(query, k=min(k, 3))
        except Exception:
            # Avoid logging full exception details here, since they may contain
            # sensitive information such as the full request URL and API key.
            logger.info(
                "WebSearchTool: Exception during Serper API call; using mock results."
            )
            return self._mock_results(query, k=min(k, 3))

