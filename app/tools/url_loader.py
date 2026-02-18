from typing import List, Dict, Any
import logging

from langchain_community.document_loaders import UnstructuredURLLoader


logger = logging.getLogger(__name__)


class UrlLoader:
    """
    Tool for loading and parsing web pages from URLs using LangChain's
    UnstructuredURLLoader.

    This is a class-based tool that can be injected as a dependency into agents.
    """

    def __init__(self, headers: Dict[str, str] | None = None) -> None:
        """
        Initialize the URL loader.

        Args:
            headers: Optional default headers dict (e.g., User-Agent) to help avoid 403 errors
        """
        # Default headers to help avoid 403 Forbidden errors
        self.default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        if headers:
            self.default_headers.update(headers)

    def extract_content(self, urls: List[str], headers: Dict[str, str] | None = None) -> List[Any]:
        """
        Load and parse web pages from the given URLs using LangChain's
        UnstructuredURLLoader.

        Args:
            urls: List of URLs to load
            headers: Optional headers dict to override default headers

        Returns:
            List of Document objects with .page_content and .metadata.
            If a URL fails to load, it will be skipped (not included in the result).
        """
        # Use provided headers or fall back to default
        final_headers = headers if headers else self.default_headers

        # Try loading each URL individually to handle failures gracefully
        all_documents = []
        for url in urls:
            try:
                logger.info("UrlLoader: Attempting to load URL: %s", url)
                loader = UnstructuredURLLoader(urls=[url], headers=final_headers)
                docs = loader.load()
                all_documents.extend(docs)
                logger.info("UrlLoader: Successfully loaded URL: %s (%d documents)", url, len(docs))
            except Exception as exc:
                logger.warning("UrlLoader: Failed to load URL %s: %s", url, exc)
                # Continue with other URLs instead of failing completely
                continue

        return all_documents


# Backward compatibility: keep the function for existing code
def extract_content(urls: List[str], headers: Dict[str, str] | None = None) -> List[Any]:
    """
    Convenience function wrapper around UrlLoader.extract_content().

    For new code, prefer instantiating UrlLoader as a tool dependency.
    """
    loader = UrlLoader(headers=headers)
    return loader.extract_content(urls)


