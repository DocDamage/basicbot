"""Vector store tools for Qdrant"""

from typing import List, Dict, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny, Range
import uuid
import os


_qdrant_client: Optional[QdrantClient] = None
_collection_name = "rag_documents"


def _get_client() -> QdrantClient:
    """Get or create Qdrant client"""
    global _qdrant_client
    
    if _qdrant_client is None:
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        
        try:
            _qdrant_client = QdrantClient(host=host, port=port)
        except Exception as e:
            print(f"Error connecting to Qdrant: {e}")
            # Try to use local file-based storage
            vector_db_dir = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
            _qdrant_client = QdrantClient(path=vector_db_dir)
    
    return _qdrant_client


def initialize_collection(collection_name: str, vector_size: int):
    """
    Initialize Qdrant collection
    
    Args:
        collection_name: Name of the collection
        vector_size: Size of vectors
    """
    global _collection_name
    _collection_name = collection_name
    
    client = _get_client()
    
    try:
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            # Create collection
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"Created collection: {collection_name}")
        else:
            print(f"Collection {collection_name} already exists")
    except Exception as e:
        print(f"Error initializing collection: {e}")


def store_vectors(
    texts: List[str],
    embeddings: List[List[float]],
    metadata: List[Dict[str, Any]],
    collection_name: Optional[str] = None
) -> List[str]:
    """
    Store vectors in Qdrant
    
    Args:
        texts: Original texts
        embeddings: Embedding vectors
        metadata: Metadata for each vector
        collection_name: Collection name (uses default if None)
        
    Returns:
        List of point IDs
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    point_ids = []
    
    try:
        points = []
        for i, (text, embedding, meta) in enumerate(zip(texts, embeddings, metadata)):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)
            
            # Combine metadata with text
            payload = {
                "text": text,
                **meta
            }
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
            )
        
        # Batch upsert
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        print(f"Stored {len(points)} vectors in {collection_name}")
    except Exception as e:
        print(f"Error storing vectors: {e}")
    
    return point_ids


def search_vectors(
    query_embedding: List[float],
    top_k: int = 5,
    collection_name: Optional[str] = None,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search vectors in Qdrant
    
    Args:
        query_embedding: Query embedding vector
        top_k: Number of results to return
        collection_name: Collection name (uses default if None)
        filter_metadata: Optional metadata filter (dict with field: value pairs)
        
    Returns:
        List of search results with scores
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    
    try:
        # Build filter if metadata provided
        query_filter = None
        if filter_metadata:
            conditions = []
            for field, value in filter_metadata.items():
                if value is not None:
                    conditions.append(
                        FieldCondition(key=field, match=MatchValue(value=value))
                    )
            
            if conditions:
                from qdrant_client.models import Filter
                query_filter = Filter(must=conditions)
        
        search_result = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=query_filter
        )
        
        results = []
        for result in search_result:
            results.append({
                "id": result.id,
                "score": result.score,
                "text": result.payload.get("text", ""),
                "metadata": {k: v for k, v in result.payload.items() if k != "text"}
            })
        
        return results
    except Exception as e:
        print(f"Error searching vectors: {e}")
        return []


def get_indexed_files(collection_name: Optional[str] = None) -> set:
    """
    Get set of all file paths that are already indexed
    
    Args:
        collection_name: Collection name (uses default if None)
        
    Returns:
        Set of file paths that have chunks in the vector database
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    indexed_files = set()
    
    try:
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            return indexed_files
        
        # Scroll through all points to get unique source_file values
        # Use scroll with limit to get all points
        offset = None
        batch_size = 1000
        
        while True:
            result = client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            points, next_offset = result
            
            if not points:
                break
            
            # Extract source_file from each point's payload
            for point in points:
                payload = point.payload or {}
                source_file = payload.get('source_file')
                if source_file:
                    indexed_files.add(source_file)
            
            if next_offset is None:
                break
            
            offset = next_offset
        
        return indexed_files
        
    except Exception as e:
        print(f"Error getting indexed files: {e}")
        return indexed_files


def is_file_indexed(file_path: str, collection_name: Optional[str] = None) -> bool:
    """
    Check if a specific file is already indexed
    
    Args:
        file_path: Path to file to check
        collection_name: Collection name (uses default if None)
        
    Returns:
        True if file has chunks in the vector database, False otherwise
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    
    try:
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            return False
        
        # Check if any points exist with this source_file
        # Use scroll with filter to check efficiently
        result = client.scroll(
            collection_name=collection_name,
            limit=1,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="source_file", match=MatchValue(value=file_path))
                ]
            ),
            with_payload=False,
            with_vectors=False
        )
        
        points, _ = result
        return len(points) > 0
        
    except Exception as e:
        print(f"Error checking if file is indexed: {e}")
        return False


def search_by_cas_number(
    cas_number: str,
    top_k: int = 5,
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for documents by CAS number (exact match)
    
    Args:
        cas_number: CAS registry number
        top_k: Number of results to return
        collection_name: Collection name (uses default if None)
        
    Returns:
        List of search results
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        query_filter = Filter(
            must=[
                FieldCondition(key="cas_number", match=MatchValue(value=cas_number))
            ]
        )
        
        # Use scroll to get all matching documents (since we're filtering, not vector searching)
        scroll_result = client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        
        results = []
        for point in scroll_result[0]:  # scroll_result is (points, next_page_offset)
            results.append({
                "id": point.id,
                "score": 1.0,  # Exact match
                "text": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"}
            })
        
        return results
    except Exception as e:
        print(f"Error searching by CAS number: {e}")
        return []


def search_by_article_number(
    article_number: str,
    top_k: int = 5,
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for documents by REACH article number
    
    Args:
        article_number: Article number (e.g., "Article 33")
        top_k: Number of results to return
        collection_name: Collection name (uses default if None)
        
    Returns:
        List of search results
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    
    try:
        query_filter = Filter(
            must=[
                FieldCondition(key="article_number", match=MatchValue(value=article_number))
            ]
        )
        
        scroll_result = client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        
        results = []
        for point in scroll_result[0]:
            results.append({
                "id": point.id,
                "score": 1.0,
                "text": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"}
            })
        
        return results
    except Exception as e:
        print(f"Error searching by article number: {e}")
        return []


def search_by_hazard_tags(
    hazard_tags: List[str],
    top_k: int = 5,
    collection_name: Optional[str] = None,
    match_all: bool = False
) -> List[Dict[str, Any]]:
    """
    Search for documents by hazard tags
    
    Args:
        hazard_tags: List of hazard tags to search for
        top_k: Number of results to return
        collection_name: Collection name (uses default if None)
        match_all: If True, all tags must match; if False, any tag matches
        
    Returns:
        List of search results
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    
    try:
        # For hazard_tags, we need to check if any/all tags are in the array
        # Qdrant supports array matching
        if match_all:
            # All tags must be present
            conditions = [
                FieldCondition(key="hazard_tags", match=MatchAny(any=[tag]))
                for tag in hazard_tags
            ]
            query_filter = Filter(must=conditions)
        else:
            # Any tag matches
            query_filter = Filter(
                must=[
                    FieldCondition(key="hazard_tags", match=MatchAny(any=hazard_tags))
                ]
            )
        
        scroll_result = client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        
        results = []
        for point in scroll_result[0]:
            # Calculate relevance score based on number of matching tags
            point_tags = point.payload.get("hazard_tags", [])
            if isinstance(point_tags, str):
                import json
                try:
                    point_tags = json.loads(point_tags)
                except:
                    point_tags = []
            
            matching_tags = set(hazard_tags) & set(point_tags)
            score = len(matching_tags) / len(hazard_tags) if hazard_tags else 0.0
            
            results.append({
                "id": point.id,
                "score": score,
                "text": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"}
            })
        
        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    except Exception as e:
        print(f"Error searching by hazard tags: {e}")
        return []


def search_by_toxicity_type(
    toxicity_type: str,
    top_k: int = 5,
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for documents by Prop 65 toxicity type
    
    Args:
        toxicity_type: Toxicity type (cancer, reproductive, both)
        top_k: Number of results to return
        collection_name: Collection name (uses default if None)
        
    Returns:
        List of search results
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    
    try:
        query_filter = Filter(
            must=[
                FieldCondition(key="toxicity_type", match=MatchValue(value=toxicity_type))
            ]
        )
        
        scroll_result = client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        
        results = []
        for point in scroll_result[0]:
            results.append({
                "id": point.id,
                "score": 1.0,
                "text": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"}
            })
        
        return results
    except Exception as e:
        print(f"Error searching by toxicity type: {e}")
        return []


def search_by_listing_date(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    top_k: int = 5,
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for documents by Prop 65 listing date range
    
    Args:
        date_from: Start date (YYYY-MM-DD format)
        date_to: End date (YYYY-MM-DD format)
        top_k: Number of results to return
        collection_name: Collection name (uses default if None)
        
    Returns:
        List of search results
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    
    try:
        conditions = []
        
        if date_from:
            conditions.append(
                FieldCondition(key="date_listed", range=Range(gte=date_from))
            )
        
        if date_to:
            conditions.append(
                FieldCondition(key="date_listed", range=Range(lte=date_to))
            )
        
        if not conditions:
            return []
        
        query_filter = Filter(must=conditions)
        
        scroll_result = client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        
        results = []
        for point in scroll_result[0]:
            results.append({
                "id": point.id,
                "score": 1.0,
                "text": point.payload.get("text", ""),
                "metadata": {k: v for k, v in point.payload.items() if k != "text"}
            })
        
        return results
    except Exception as e:
        print(f"Error searching by listing date: {e}")
        return []


def check_exposure_compliance(
    cas_number: str,
    exposure_value: float,
    exposure_unit: str,
    collection_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check if exposure exceeds Prop 65 NSRL/MADL thresholds
    
    Args:
        cas_number: CAS number of chemical
        exposure_value: Exposure value
        exposure_unit: Unit of exposure
        collection_name: Collection name (uses default if None)
        
    Returns:
        Dictionary with compliance status
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    
    try:
        # Find chemical by CAS number
        query_filter = Filter(
            must=[
                FieldCondition(key="cas_number", match=MatchValue(value=cas_number))
            ]
        )
        
        scroll_result = client.scroll(
            collection_name=collection_name,
            scroll_filter=query_filter,
            limit=1,
            with_payload=True,
            with_vectors=False
        )
        
        if not scroll_result[0]:
            return {
                "cas_number": cas_number,
                "found": False,
                "compliance_status": "unknown"
            }
        
        point = scroll_result[0][0]
        metadata = point.payload
        
        # Get NSRL and MADL values
        nsrl_value = metadata.get('nsrl_value')
        nsrl_unit = metadata.get('nsrl_unit')
        madl_value = metadata.get('madl_value')
        madl_unit = metadata.get('madl_unit')
        
        # Normalize units for comparison (simplified - would need proper unit conversion)
        exceeds_nsrl = False
        exceeds_madl = False
        
        if nsrl_value and nsrl_unit:
            # Simple comparison (assumes same unit)
            if exposure_unit.lower() == nsrl_unit.lower():
                exceeds_nsrl = exposure_value > nsrl_value
        
        if madl_value and madl_unit:
            if exposure_unit.lower() == madl_unit.lower():
                exceeds_madl = exposure_value > madl_value
        
        compliance_status = "compliant"
        if exceeds_nsrl or exceeds_madl:
            compliance_status = "non_compliant"
        
        return {
            "cas_number": cas_number,
            "found": True,
            "exposure_value": exposure_value,
            "exposure_unit": exposure_unit,
            "nsrl": {
                "value": nsrl_value,
                "unit": nsrl_unit,
                "exceeded": exceeds_nsrl
            } if nsrl_value else None,
            "madl": {
                "value": madl_value,
                "unit": madl_unit,
                "exceeded": exceeds_madl
            } if madl_value else None,
            "compliance_status": compliance_status
        }
    except Exception as e:
        print(f"Error checking exposure compliance: {e}")
        return {
            "cas_number": cas_number,
            "error": str(e),
            "compliance_status": "unknown"
        }


def delete_collection(collection_name: Optional[str] = None):
    """
    Delete a collection
    
    Args:
        collection_name: Collection name (uses default if None)
    """
    if collection_name is None:
        collection_name = _collection_name
    
    client = _get_client()
    
    try:
        client.delete_collection(collection_name)
        print(f"Deleted collection: {collection_name}")
    except Exception as e:
        print(f"Error deleting collection: {e}")

