"""Improved indexing with smaller batches and better progress"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bmad.framework import BMADFramework
from src.agents import RetrievalAgent
from src.tools.vector_tools import initialize_collection
from src.tools.embedding_tools import get_embedding_dimension, create_embeddings
from src.config import get_settings
from dotenv import load_dotenv
import json
import time

load_dotenv()

def index_celebrity_database_improved():
    """Index celebrity database with smaller batches and progress"""
    print("=" * 70)
    print("Indexing Celebrity Database (Improved)")
    print("=" * 70)
    print()
    
    # Initialize framework
    memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
    framework = BMADFramework(memory_storage_path=memory_path)
    
    retrieval_agent = RetrievalAgent(framework=framework)
    framework.register_agent(retrieval_agent)
    
    # Initialize vector store
    settings = get_settings()
    embedding_model = settings.get_embedding_model()
    vector_size = get_embedding_dimension(embedding_model)
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "rag_documents")
    
    try:
        initialize_collection(collection_name, vector_size)
        print(f"✓ Vector store initialized: {collection_name}")
    except Exception as e:
        print(f"⚠️  Note: {e}")
        print("   Will use file-based storage (this is fine)")
    
    # Load database
    db_path = Path(__file__).parent / "data" / "epstein_files" / "celebrity-results.json"
    if not db_path.exists():
        print("Error: celebrity-results.json not found!")
        return
    
    with open(db_path, 'r', encoding='utf-8') as f:
        database = json.load(f)
    
    # Convert to chunks
    chunks = []
    results = database.get('results', [])
    
    print(f"Processing {len(results)} database entries...")
    
    for idx, result in enumerate(results):
        file_path = result.get('file', '')
        celebrities = result.get('celebrities', [])
        page = result.get('page', 1)
        total_pages = result.get('totalPages', 1)
        
        celeb_names = [celeb.get('name', '') for celeb in celebrities]
        celeb_text = ", ".join(celeb_names) if celeb_names else "No celebrities"
        
        text = f"File: {file_path}\nPage: {page}/{total_pages}\nCelebrities: {celeb_text}"
        
        if celebrities:
            for celeb in celebrities:
                text += f"\n{celeb.get('name', '')} (confidence: {celeb.get('confidence', 0):.1f}%)"
        
        chunks.append({
            'content': text,
            'metadata': {
                'source': 'celebrity_database',
                'file_path': file_path,
                'page': page,
                'total_pages': total_pages,
                'celebrities': celeb_names,
                'celebrity_count': len(celebrities),
                'type': 'celebrity_recognition'
            }
        })
    
    print(f"Created {len(chunks)} chunks")
    print()
    
    # Process in smaller batches with progress
    texts = [chunk['content'] for chunk in chunks]
    metadata_list = [chunk['metadata'] for chunk in chunks]
    
    # Smaller batch size for embeddings
    embedding_batch_size = 50  # Reduced from 100
    total_batches = (len(texts) + embedding_batch_size - 1) // embedding_batch_size
    
    print(f"Generating embeddings in {total_batches} batches of {embedding_batch_size}...")
    print()
    
    all_embeddings = []
    start_time = time.time()
    
    for batch_idx in range(0, len(texts), embedding_batch_size):
        batch_texts = texts[batch_idx:batch_idx + embedding_batch_size]
        batch_num = (batch_idx // embedding_batch_size) + 1
        
        batch_start = time.time()
        print(f"[{time.strftime('%H:%M:%S')}] Batch {batch_num}/{total_batches}: Creating embeddings for {len(batch_texts)} chunks...", end='', flush=True)
        
        batch_embeddings = create_embeddings(
            batch_texts,
            model_name=embedding_model,
            batch_size=16  # Smaller internal batch
        )
        
        batch_time = time.time() - batch_start
        
        if batch_embeddings:
            all_embeddings.extend(batch_embeddings)
            elapsed = time.time() - start_time
            rate = (batch_num * embedding_batch_size) / elapsed if elapsed > 0 else 0
            remaining = (total_batches - batch_num) * (batch_time)
            print(f" ✓ ({batch_time:.1f}s, {rate:.1f} chunks/s, ~{remaining/60:.1f} min remaining)")
        else:
            print(f" ✗ FAILED")
            return
    
    print()
    print(f"✓ Generated {len(all_embeddings)} embeddings")
    print(f"Storing in vector database...")
    print()
    
    # Store in batches
    from src.tools.vector_tools import store_vectors
    
    store_batch_size = 100
    total_store_batches = (len(texts) + store_batch_size - 1) // store_batch_size
    
    all_point_ids = []
    for batch_idx in range(0, len(texts), store_batch_size):
        batch_texts = texts[batch_idx:batch_idx + store_batch_size]
        batch_embeddings = all_embeddings[batch_idx:batch_idx + store_batch_size]
        batch_metadata = metadata_list[batch_idx:batch_idx + store_batch_size]
        batch_num = (batch_idx // store_batch_size) + 1
        
        print(f"[{time.strftime('%H:%M:%S')}] Storing batch {batch_num}/{total_store_batches}...", end='', flush=True)
        
        point_ids = store_vectors(
            texts=batch_texts,
            embeddings=batch_embeddings,
            metadata=batch_metadata,
            collection_name=collection_name
        )
        
        all_point_ids.extend(point_ids)
        print(f" ✓ ({len(point_ids)} points)")
    
    total_time = time.time() - start_time
    print()
    print("=" * 70)
    print("✅ INDEXING COMPLETE!")
    print(f"   Total entries: {len(all_point_ids)}")
    print(f"   Time: {total_time/60:.1f} minutes")
    print(f"   Collection: {collection_name}")
    print("=" * 70)

if __name__ == "__main__":
    index_celebrity_database_improved()

