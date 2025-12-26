import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class GoogleSearchTool:
    """
    Tool for performing Google searches and fetching article content.
    Uses SerpAPI for search and newspaper3k for article extraction.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Search tool.

        Args:
            api_key: SerpAPI key. If None, will try to get from environment variable SERPAPI_KEY
        """
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise ValueError("SerpAPI key must be provided or set as SERPAPI_KEY environment variable")

        self._search_client = None
        self._article_extractor = None

    def _get_search_client(self):
        """Lazy initialization of search client."""
        if self._search_client is None:
            try:
                from serpapi import GoogleSearch
                self._search_client = GoogleSearch
            except ImportError:
                raise ImportError("serpapi not installed. Install with: pip install serpapi")
        return self._search_client

    def _get_article_extractor(self):
        """Lazy initialization of article extractor."""
        if self._article_extractor is None:
            try:
                from newspaper import Article
                self._article_extractor = Article
            except ImportError:
                raise ImportError("newspaper3k not installed. Install with: pip install newspaper3k")
        return self._article_extractor

    def search(
        self,
        query: str,
        num_results: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Perform a Google search and return results.

        Args:
            query: Search query string
            num_results: Number of results to return (default: 5)
            **kwargs: Additional parameters for SerpAPI

        Returns:
            List of search result dictionaries with title, link, snippet, etc.
        """
        try:
            search_client = self._get_search_client()

            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
                **kwargs
            }

            search = search_client(params)
            results = search.get_dict()

            return self._extract_organic_results(results)

        except Exception as e:
            logger.error(f"Error performing Google search: {e}")
            return []

    def _extract_organic_results(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract organic search results from SerpAPI response.

        Args:
            search_results: Raw SerpAPI response

        Returns:
            List of cleaned search results
        """
        organic_results = []

        if "organic_results" in search_results:
            for result in search_results["organic_results"]:
                cleaned_result = {
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "displayed_link": result.get("displayed_link", ""),
                    "position": result.get("position", 0),
                    "source": "google_search"
                }
                organic_results.append(cleaned_result)

        return organic_results

    def fetch_article_content(self, url: str, timeout: int = 10) -> str:
        """
        Fetch and extract article content from a URL.

        Args:
            url: URL of the article to fetch
            timeout: Request timeout in seconds

        Returns:
            Extracted article text content
        """
        try:
            article_class = self._get_article_extractor()
            article = article_class(url, timeout=timeout)

            article.download()
            article.parse()

            return article.text or ""

        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return ""

    def search_and_fetch_content(
        self,
        query: str,
        num_results: int = 3,
        fetch_content: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform search and optionally fetch full content of results.

        Args:
            query: Search query
            num_results: Number of results to process
            fetch_content: Whether to fetch full article content

        Returns:
            List of search results with optional full content
        """
        search_results = self.search(query, num_results)

        if fetch_content:
            for result in search_results:
                if result.get("link"):
                    content = self.fetch_article_content(result["link"])
                    result["full_content"] = content

        return search_results

    def is_available(self) -> bool:
        """Check if the Google Search tool is properly configured."""
        return self.api_key is not None


class SearchAugmentedRAG:
    """
    RAG system augmented with web search capabilities.
    Combines local knowledge base with real-time web search results.
    """

    def __init__(
        self,
        vector_db,
        search_tool: GoogleSearchTool,
        reranker=None
    ):
        """
        Initialize search-augmented RAG.

        Args:
            vector_db: Local vector database (e.g., Chroma)
            search_tool: GoogleSearchTool instance
            reranker: Optional reranker for improving result quality
        """
        self.vector_db = vector_db
        self.search_tool = search_tool
        self.reranker = reranker

    def retrieve_augmented(
        self,
        query: str,
        local_k: int = 3,
        web_k: int = 3,
        combine_results: bool = True
    ) -> tuple:
        """
        Perform augmented retrieval combining local and web results.

        Args:
            query: Search query
            local_k: Number of local documents to retrieve
            web_k: Number of web results to fetch
            combine_results: Whether to combine and rerank results

        Returns:
            Tuple of (documents, sources) where sources indicate local vs web
        """
        # Retrieve from local knowledge base
        local_docs, local_sources = self.vector_db.similarity_search_with_threshold(
            query=query, k=local_k
        )

        # Search web for additional information
        web_results = self.search_tool.search_and_fetch_content(
            query=query, num_results=web_k, fetch_content=True
        )

        # Convert web results to Document format
        web_docs = []
        web_sources = []
        for result in web_results:
            content = result.get("full_content", result.get("snippet", ""))
            if content:
                from entities.document import Document

                web_doc = Document(
                    page_content=content,
                    metadata={
                        "source": result.get("link", ""),
                        "title": result.get("title", ""),
                        "search_result": True
                    }
                )
                web_docs.append(web_doc)

                web_sources.append({
                    "score": 0.0,  # Web results don't have relevance scores
                    "document": result.get("link", ""),
                    "content_preview": result.get("snippet", "")[:256] + "...",
                    "source": "web_search"
                })

        # Combine results
        if combine_results:
            all_docs = local_docs + web_docs
            all_sources = local_sources + web_sources

            # Apply reranking if available
            if self.reranker and all_docs:
                reranked_docs = self.reranker.rerank(
                    query=query,
                    documents=all_docs,
                    top_k=min(len(all_docs), local_k + web_k)
                )
                return reranked_docs, all_sources
            else:
                return all_docs, all_sources
        else:
            return local_docs + web_docs, local_sources + web_sources
