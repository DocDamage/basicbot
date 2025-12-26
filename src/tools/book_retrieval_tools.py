"""Book retrieval tools for specialized book searches"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..tools.vector_tools import search_vectors
from ..tools.embedding_tools import create_embeddings

# Import Qdrant client functions
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
    import os
    
    def _get_client() -> Optional[QdrantClient]:
        """Get Qdrant client"""
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        try:
            return QdrantClient(host=host, port=port)
        except Exception:
            vector_db_dir = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
            return QdrantClient(path=vector_db_dir)
except ImportError:
    _get_client = None

logger = logging.getLogger('book_retrieval_tools')


def search_by_title(query: str, top_k: int = 10, collection_name: str = "rag_documents") -> List[Dict[str, Any]]:
    """
    Search books by title using semantic search with Qdrant filters
    
    Args:
        query: Title search query
        top_k: Number of results to return
        collection_name: Qdrant collection name
        
    Returns:
        List of search results
    """
    try:
        if _get_client is None:
            return []
        
        client = _get_client()
        
        # Create query embedding for semantic search
        query_embeddings = create_embeddings([query])
        if not query_embeddings:
            return []
        
        # Use semantic search (Qdrant doesn't support fuzzy text matching in filters,
        # so we use semantic search which is better for title matching anyway)
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embeddings[0],
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="content_type",
                        match=MatchValue(value="book")
                    )
                ]
            ),
            limit=top_k
        )
        
        return _format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error searching by title: {e}", exc_info=True)
        return []


def search_by_author(author_name: str, top_k: int = 50, collection_name: str = "rag_documents") -> List[Dict[str, Any]]:
    """
    Find books by author using semantic search (author names may have variations)
    
    Args:
        author_name: Author name
        top_k: Number of results to return
        collection_name: Qdrant collection name
        
    Returns:
        List of search results
    """
    try:
        if _get_client is None:
            return []
        
        client = _get_client()
        
        # Use semantic search (better for author name variations)
        query_embeddings = create_embeddings([author_name])
        if not query_embeddings:
            return []
        
        # Filter for books only
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embeddings[0],
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="content_type",
                        match=MatchValue(value="book")
                    )
                ]
            ),
            limit=top_k
        )
        
        return _format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error searching by author: {e}", exc_info=True)
        return []


def search_by_series(series_name: str, top_k: int = 50, collection_name: str = "rag_documents") -> List[Dict[str, Any]]:
    """
    Find books in a series using semantic search with book filter
    
    Args:
        series_name: Series name
        top_k: Number of results to return
        collection_name: Qdrant collection name
        
    Returns:
        List of search results
    """
    try:
        if _get_client is None:
            return []
        
        client = _get_client()
        
        query_embeddings = create_embeddings([series_name])
        if not query_embeddings:
            return []
        
        # Filter for books only
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embeddings[0],
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="content_type",
                        match=MatchValue(value="book")
                    )
                ]
            ),
            limit=top_k
        )
        
        return _format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error searching by series: {e}", exc_info=True)
        return []


def search_by_character(character_name: str, top_k: int = 20, collection_name: str = "rag_documents") -> List[Dict[str, Any]]:
    """
    Find mentions of a character using semantic search
    
    Args:
        character_name: Character name
        top_k: Number of results to return
        collection_name: Qdrant collection name
        
    Returns:
        List of search results
    """
    try:
        if _get_client is None:
            return []
        
        client = _get_client()
        
        query_embeddings = create_embeddings([character_name])
        if not query_embeddings:
            return []
        
        # Filter for books only, semantic search will find character mentions
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embeddings[0],
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="content_type",
                        match=MatchValue(value="book")
                    )
                ]
            ),
            limit=top_k
        )
        
        return _format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error searching by character: {e}", exc_info=True)
        return []


def search_by_quote(quote_text: str, top_k: int = 10, collection_name: str = "rag_documents") -> List[Dict[str, Any]]:
    """
    Find exact or similar quotes
    
    Args:
        quote_text: Quote text to search for
        top_k: Number of results to return
        collection_name: Qdrant collection name
        
    Returns:
        List of search results
    """
    try:
        # Use semantic search for quote similarity
        query_embeddings = create_embeddings([quote_text])
        if not query_embeddings:
            return []
        
        results = search_vectors(
            query_embedding=query_embeddings[0],
            top_k=top_k,
            collection_name=collection_name
        )
        
        # Filter results that likely contain the quote
        filtered_results = []
        quote_lower = quote_text.lower()
        
        for result in results:
            content = result.get('payload', {}).get('text', '').lower()
            # Check if quote appears in content (exact or similar)
            if quote_lower in content or _similar_quote_match(quote_text, content):
                filtered_results.append(result)
        
        return filtered_results[:top_k]
        
    except Exception as e:
        logger.error(f"Error searching by quote: {e}", exc_info=True)
        return []


def search_by_genre(genre: str, top_k: int = 50, collection_name: str = "rag_documents") -> List[Dict[str, Any]]:
    """
    Filter books by genre using semantic search with book filter
    
    Args:
        genre: Genre name
        top_k: Number of results to return
        collection_name: Qdrant collection name
        
    Returns:
        List of search results
    """
    try:
        if _get_client is None:
            return []
        
        client = _get_client()
        
        query_embeddings = create_embeddings([genre])
        if not query_embeddings:
            return []
        
        # Filter for books only, semantic search will match genre
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embeddings[0],
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="content_type",
                        match=MatchValue(value="book")
                    )
                ]
            ),
            limit=top_k
        )
        
        return _format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error searching by genre: {e}", exc_info=True)
        return []


def get_full_book_text(book_id: str, books_metadata_dir: Optional[str] = None) -> Optional[str]:
    """
    Retrieve complete book text
    
    Args:
        book_id: Book ID
        books_metadata_dir: Directory containing book metadata files
        
    Returns:
        Full book text or None
    """
    try:
        if books_metadata_dir is None:
            books_metadata_dir = os.path.join(os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs"), "books", "metadata")
        
        metadata_file = os.path.join(books_metadata_dir, f"{book_id}.json")
        if not os.path.exists(metadata_file):
            return None
        
        # Load metadata to get processed file path
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Try to get from processed files
        processed_dir = os.path.join(os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs"), "books", "processed")
        processed_file = os.path.join(processed_dir, f"{book_id}.md")
        
        if os.path.exists(processed_file):
            with open(processed_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Remove markdown header if present
                if content.startswith('#'):
                    lines = content.split('\n')
                    # Skip header lines
                    content = '\n'.join(lines[3:]) if len(lines) > 3 else content
                return content
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting full book text for {book_id}: {e}", exc_info=True)
        return None


def get_book_metadata(book_id: str, books_metadata_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get full book metadata
    
    Args:
        book_id: Book ID
        books_metadata_dir: Directory containing book metadata files
        
    Returns:
        Book metadata dictionary or None
    """
    try:
        if books_metadata_dir is None:
            books_metadata_dir = os.path.join(os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs"), "books", "metadata")
        
        metadata_file = os.path.join(books_metadata_dir, f"{book_id}.json")
        if not os.path.exists(metadata_file):
            return None
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    except Exception as e:
        logger.error(f"Error getting book metadata for {book_id}: {e}", exc_info=True)
        return None


def get_related_books(book_id: str, top_k: int = 10, collection_name: str = "rag_documents") -> List[Dict[str, Any]]:
    """
    Find related books (semantic + metadata-based) using Qdrant filter to exclude current book
    
    Args:
        book_id: Book ID
        top_k: Number of related books to return
        collection_name: Qdrant collection name
        
    Returns:
        List of related book results
    """
    try:
        if _get_client is None:
            return []
        
        # Get book metadata
        metadata = get_book_metadata(book_id)
        if not metadata:
            return []
        
        # Get a sample of book content for semantic search
        book_text = get_full_book_text(book_id)
        if not book_text:
            # Use title and author as query
            query = f"{metadata.get('title', '')} {metadata.get('author', '')}"
        else:
            # Use first 1000 chars as query
            query = book_text[:1000]
        
        # Semantic search
        query_embeddings = create_embeddings([query])
        if not query_embeddings:
            return []
        
        client = _get_client()
        
        # Use Qdrant filter to exclude current book and filter for books only
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embeddings[0],
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="content_type",
                        match=MatchValue(value="book")
                    )
                ],
                must_not=[
                    FieldCondition(
                        key="book_id",
                        match=MatchValue(value=book_id)
                    )
                ]
            ),
            limit=top_k
        )
        
        return _format_search_results(results)
        
    except Exception as e:
        logger.error(f"Error finding related books for {book_id}: {e}", exc_info=True)
        return []


def _format_search_results(results: List) -> List[Dict[str, Any]]:
    """
    Format search results from Qdrant into standardized format
    
    Args:
        results: List of Qdrant search result objects
        
    Returns:
        List of formatted result dictionaries with score, text, and metadata
    """
    formatted = []
    for result in results:
        payload = result.payload if hasattr(result, 'payload') else result.get('payload', {})
        score = result.score if hasattr(result, 'score') else result.get('score', 0.0)
        
        formatted.append({
            'score': score,
            'text': payload.get('text', ''),
            'metadata': {
                'book_id': payload.get('book_id', ''),
                'book_title': payload.get('book_title', ''),
                'author': payload.get('author', ''),
                'series': payload.get('series', ''),
                'chapter_number': payload.get('chapter_number'),
                'chapter_title': payload.get('chapter_title', ''),
                'characters_mentioned': payload.get('characters_mentioned', []),
                'locations_mentioned': payload.get('locations_mentioned', []),
                'content_type': payload.get('content_type', 'book')
            }
        })
    
    return formatted


def _similar_quote_match(quote: str, content: str, threshold: float = 0.7) -> bool:
    """
    Check if quote is similar to content using word overlap
    
    Args:
        quote: Quote text to match
        content: Content text to search in
        threshold: Similarity threshold (0.0-1.0), default 0.7
        
    Returns:
        True if similarity meets threshold, False otherwise
        
    Example:
        >>> _similar_quote_match("hello world", "hello world test", 0.7)
        True
        >>> _similar_quote_match("hello world", "test example", 0.7)
        False
    """
    quote_words = set(quote.lower().split())
    content_words = set(content.lower().split())
    
    if not quote_words:
        return False
    
    overlap = len(quote_words & content_words)
    similarity = overlap / len(quote_words)
    
    return similarity >= threshold

