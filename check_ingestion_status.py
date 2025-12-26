"""Quick script to check ebook ingestion status"""

import os
import json
from pathlib import Path

print("=" * 70)
print("EBOOK INGESTION STATUS CHECK")
print("=" * 70)
print()

# Check metadata files
metadata_dir = Path("data/extracted_docs/books/metadata")
if metadata_dir.exists():
    metadata_files = list(metadata_dir.glob("*.json"))
    print(f"✓ Metadata files: {len(metadata_files)}")
    if metadata_files:
        # Sample a few metadata files
        print("\nSample metadata files:")
        for f in metadata_files[:3]:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    title = data.get('title', 'Unknown')
                    author = data.get('author', 'Unknown')
                    print(f"  - {title} by {author}")
            except Exception as e:
                print(f"  - {f.name} (error reading: {e})")
else:
    print("✗ Metadata directory not found")

print()

# Check processed files
processed_dir = Path("data/extracted_docs/books/processed")
if processed_dir.exists():
    processed_files = list(processed_dir.glob("*.md"))
    print(f"✓ Processed markdown files: {len(processed_files)}")
    if processed_files:
        total_size = sum(f.stat().st_size for f in processed_files)
        print(f"  Total size: {total_size / (1024*1024):.2f} MB")
else:
    print("✗ Processed directory not found")

print()

# Check entity index
entity_index = Path("data/extracted_docs/books/entities/entity_index.json")
if entity_index.exists():
    try:
        with open(entity_index, 'r', encoding='utf-8') as f:
            entities = json.load(f)
            total_entities = sum(len(v) if isinstance(v, list) else 1 for v in entities.values())
            print(f"✓ Entity index found: {len(entities)} entity types, {total_entities} total entities")
    except Exception as e:
        print(f"✗ Error reading entity index: {e}")
else:
    print("✗ Entity index not found")

print()

# Check vector database (if Qdrant is accessible)
try:
    from qdrant_client import QdrantClient
    import os
    
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    
    try:
        client = QdrantClient(host=host, port=port)
        collections = client.get_collections()
        print("✓ Qdrant connection successful")
        
        # Check for book chunks
        collection_name = os.getenv("QDRANT_COLLECTION", "rag_documents")
        try:
            collection_info = client.get_collection(collection_name)
            points_count = collection_info.points_count
            print(f"✓ Collection '{collection_name}': {points_count:,} points indexed")
            
            # Try to search for book content
            from src.tools.embedding_tools import create_embeddings
            query_embedding = create_embeddings(["book"], model_name="all-MiniLM-L6-v2")
            if query_embedding:
                from src.tools.vector_tools import search_vectors
                results = search_vectors(
                    query_embedding[0],
                    top_k=5,
                    filter_metadata={"content_type": "book"}
                )
                if results:
                    print(f"✓ Found {len(results)} book chunks in vector database")
                    print("\nSample book chunks:")
                    for i, result in enumerate(results[:3], 1):
                        meta = result.get('metadata', {})
                        title = meta.get('book_title', 'Unknown')
                        print(f"  {i}. {title}")
                else:
                    print("⚠ No book chunks found in vector database (may not have been indexed)")
        except Exception as e:
            print(f"⚠ Could not check collection: {e}")
    except Exception as e:
        # Try local file-based storage
        vector_db_dir = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
        if os.path.exists(vector_db_dir):
            print(f"✓ Using local Qdrant storage at: {vector_db_dir}")
        else:
            print(f"⚠ Qdrant not accessible: {e}")
except ImportError:
    print("⚠ qdrant-client not available for checking vector database")

print()
print("=" * 70)

