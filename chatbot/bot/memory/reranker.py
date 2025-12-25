import logging
from typing import List, Optional

from entities.document import Document

logger = logging.getLogger(__name__)


class Reranker:
    """
    Reranker class for improving document relevance using advanced ranking models.
    Supports multiple reranking backends including FlashRank and Jina Reranker.
    """

    def __init__(
        self,
        model_name: str = "ms-marco-MiniLM-L-12-v2",
        backend: str = "flashrank"
    ):
        """
        Initialize the reranker.

        Args:
            model_name: Name of the reranking model to use
            backend: Backend to use ('flashrank' or 'jinai')
        """
        self.model_name = model_name
        self.backend = backend
        self.ranker = None
        self._initialize_ranker()

    def _initialize_ranker(self):
        """Initialize the appropriate reranking backend."""
        try:
            if self.backend == "flashrank":
                self._initialize_flashrank()
            elif self.backend == "jinai":
                self._initialize_jinai()
            else:
                raise ValueError(f"Unsupported backend: {self.backend}")
        except ImportError as e:
            logger.warning(f"Failed to initialize {self.backend} reranker: {e}")
            logger.info("Falling back to no reranking")
            self.ranker = None

    def _initialize_flashrank(self):
        """Initialize FlashRank reranker."""
        try:
            from flashrank import Ranker, RerankRequest
            self.ranker = Ranker(model_name=self.model_name)
            self.rerank_method = self._rerank_flashrank
            logger.info(f"Initialized FlashRank reranker with model: {self.model_name}")
        except ImportError:
            raise ImportError("flashrank not installed. Install with: pip install flashrank")

    def _initialize_jinai(self):
        """Initialize Jina AI reranker."""
        try:
            from rerankers import Reranker as JinaReranker
            self.ranker = JinaReranker(self.model_name)
            self.rerank_method = self._rerank_jinai
            logger.info(f"Initialized Jina reranker with model: {self.model_name}")
        except ImportError:
            raise ImportError("rerankers not installed. Install with: pip install rerankers")

    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5,
        **kwargs
    ) -> List[Document]:
        """
        Rerank documents based on relevance to the query.

        Args:
            query: The search query
            documents: List of Document objects to rerank
            top_k: Number of top documents to return
            **kwargs: Additional arguments for the reranking model

        Returns:
            List of reranked Document objects
        """
        if not self.ranker or not documents:
            logger.warning("Reranker not initialized or no documents provided")
            return documents[:top_k]

        try:
            return self.rerank_method(query, documents, top_k, **kwargs)
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            logger.info("Falling back to original document order")
            return documents[:top_k]

    def _rerank_flashrank(
        self,
        query: str,
        documents: List[Document],
        top_k: int,
        **kwargs
    ) -> List[Document]:
        """Rerank using FlashRank."""
        from flashrank import RerankRequest

        # Convert documents to passages format
        passages = [{"text": doc.page_content} for doc in documents]

        # Create rerank request
        request = RerankRequest(query=query, passages=passages)

        # Perform reranking
        results = self.ranker.rerank(request, **kwargs)

        # Return reranked documents
        reranked_docs = []
        for result in results[:top_k]:
            original_doc = documents[result['corpus_id']]
            # Add reranking score to metadata
            updated_metadata = original_doc.metadata.copy()
            updated_metadata['rerank_score'] = result['score']
            reranked_doc = Document(
                page_content=original_doc.page_content,
                metadata=updated_metadata
            )
            reranked_docs.append(reranked_doc)

        return reranked_docs

    def _rerank_jinai(
        self,
        query: str,
        documents: List[Document],
        top_k: int,
        **kwargs
    ) -> List[Document]:
        """Rerank using Jina AI reranker."""
        # Convert documents to passages format
        passages = [doc.page_content for doc in documents]

        # Perform reranking
        results = self.ranker.rank(query=query, docs=passages, **kwargs)

        # Return reranked documents
        reranked_docs = []
        for result in results[:top_k]:
            original_doc = documents[result.doc_id]
            # Add reranking score to metadata
            updated_metadata = original_doc.metadata.copy()
            updated_metadata['rerank_score'] = result.score
            reranked_doc = Document(
                page_content=original_doc.page_content,
                metadata=updated_metadata
            )
            reranked_docs.append(reranked_doc)

        return reranked_docs

    def is_available(self) -> bool:
        """Check if reranker is available and initialized."""
        return self.ranker is not None


class RerankerConfig:
    """Configuration class for reranker settings."""

    SUPPORTED_BACKENDS = ['flashrank', 'jinai']
    DEFAULT_MODELS = {
        'flashrank': 'ms-marco-MiniLM-L-12-v2',
        'jinai': 'jinaai/jina-reranker-m0-GGUF'
    }

    @staticmethod
    def get_default_config(backend: str = 'flashrank') -> dict:
        """Get default configuration for a backend."""
        if backend not in RerankerConfig.SUPPORTED_BACKENDS:
            raise ValueError(f"Unsupported backend: {backend}")

        return {
            'model_name': RerankerConfig.DEFAULT_MODELS[backend],
            'backend': backend
        }
