"""Embedding tools using Hugging Face models"""

from typing import List, Optional
from sentence_transformers import SentenceTransformer
import torch


# Global model cache
_embedding_model_cache: Optional[SentenceTransformer] = None


def create_embeddings(
    texts: List[str],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    batch_size: int = 32
) -> List[List[float]]:
    """
    Create embeddings for texts using Hugging Face model
    
    Args:
        texts: List of texts to embed
        model_name: Name of the embedding model
        batch_size: Batch size for processing
        
    Returns:
        List of embedding vectors
    """
    global _embedding_model_cache
    
    # Load model (cache it)
    if _embedding_model_cache is None or _embedding_model_cache.get_sentence_embedding_dimension() == 0:
        try:
            _embedding_model_cache = SentenceTransformer(model_name)
        except Exception as e:
            print(f"Error loading embedding model {model_name}: {e}")
            # Fallback to default
            _embedding_model_cache = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    elif model_name != _embedding_model_cache.get_sentence_embedding_dimension():
        # Model changed, reload
        _embedding_model_cache = SentenceTransformer(model_name)
    
    # Generate embeddings
    try:
        embeddings = _embedding_model_cache.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True
        )
        
        # Convert to list of lists
        return embeddings.tolist()
    except Exception as e:
        print(f"Error creating embeddings: {e}")
        return []


def get_embedding_dimension(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> int:
    """
    Get the dimension of embeddings for a model
    
    Args:
        model_name: Name of the embedding model
        
    Returns:
        Embedding dimension
    """
    global _embedding_model_cache
    
    if _embedding_model_cache is None:
        try:
            _embedding_model_cache = SentenceTransformer(model_name)
        except:
            _embedding_model_cache = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    return _embedding_model_cache.get_sentence_embedding_dimension()

