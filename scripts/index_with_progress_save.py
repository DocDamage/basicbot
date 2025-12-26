"""Index with progress saving and resume capability"""

import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bmad.framework import BMADFramework
from src.agents import RetrievalAgent
from src.tools.vector_tools import initialize_collection, store_vectors
from src.tools.embedding_tools import get_embedding_dimension, create_embeddings
from src.config import get_settings
from dotenv import load_dotenv

load_dotenv()

PROGRESS_FILE = "indexing_progress.json"

def load_progress():
    """Load saved progress"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return None

def save_progress(embeddings_done, total, embeddings):
    """Save progress"""
    progress = {
        'embeddings_done': embeddings_done,
        'total': total,
        'embeddings': embeddings  # Save embeddings to avoid recomputing
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def index_celebrity_database_with_resume():
    """Index with ability to resume"""
    print("=" * 70)
    print("Indexing Celebrity Database (With Progress Saving)")
    print("=" * 70)
    print()
    
    # Check for existing progress
    saved_progress = load_progress()
    if saved_progress:
        print(f"Found saved progress: {saved_progress['embeddings_done']}/{saved_progress['total']} embeddings done")
        # Auto-resume if running non-interactively, or check command line arg
        if len(sys.argv) > 1 and sys.argv[1] == '--no-resume':
            resume = False
            print("Starting fresh (--no-resume flag)")
        else:
            resume = True
            print("Auto-resuming from saved progress...")
        
        if not resume:
            os.remove(PROGRESS_FILE)
            saved_progress = None
    
    # Initialize
    memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
    framework = BMADFramework(memory_storage_path=memory_path)
    
    retrieval_agent = RetrievalAgent(framework=framework)
    framework.register_agent(retrieval_agent)
    
    settings = get_settings()
    embedding_model = settings.get_embedding_model()
    vector_size = get_embedding_dimension(embedding_model)
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "rag_documents")
    
    try:
        initialize_collection(collection_name, vector_size)
        print(f"✓ Vector store initialized")
    except Exception as e:
        print(f"⚠️  Note: {e}")
    
    # Load database
    db_path = Path(__file__).parent / "data" / "epstein_files" / "celebrity-results.json"
    if not db_path.exists():
        print("Error: celebrity-results.json not found!")
        return
    
    with open(db_path, 'r', encoding='utf-8') as f:
        database = json.load(f)
    
    # Create chunks
    chunks = []
    results = database.get('results', [])
    
    print(f"Processing {len(results)} entries...")
    
    for result in results:
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
    
    texts = [chunk['content'] for chunk in chunks]
    metadata_list = [chunk['metadata'] for chunk in chunks]
    total = len(texts)
    
    # Load or create embeddings
    if saved_progress and saved_progress.get('embeddings'):
        print(f"Resuming from saved progress...")
        all_embeddings = saved_progress['embeddings']
        start_idx = saved_progress['embeddings_done']
    else:
        all_embeddings = []
        start_idx = 0
    
    # Generate remaining embeddings
    embedding_batch_size = 50
    total_batches = (total + embedding_batch_size - 1) // embedding_batch_size
    
    print(f"\nGenerating embeddings...")
    print(f"Starting from batch {start_idx // embedding_batch_size + 1}/{total_batches}")
    print()
    
    start_time = time.time()
    
    try:
        for batch_idx in range(start_idx, total, embedding_batch_size):
            batch_texts = texts[batch_idx:batch_idx + embedding_batch_size]
            batch_num = (batch_idx // embedding_batch_size) + 1
            
            print(f"[{time.strftime('%H:%M:%S')}] Batch {batch_num}/{total_batches} ({len(batch_texts)} chunks)...", end='', flush=True)
            
            batch_embeddings = create_embeddings(
                batch_texts,
                model_name=embedding_model,
                batch_size=16
            )
            
            if batch_embeddings:
                all_embeddings.extend(batch_embeddings)
                elapsed = time.time() - start_time
                rate = (batch_num * embedding_batch_size) / elapsed if elapsed > 0 else 0
                remaining = (total_batches - batch_num) * (elapsed / batch_num) if batch_num > 0 else 0
                print(f" ✓ ({rate:.1f} chunks/s, ~{remaining/60:.1f} min remaining)")
                
                # Save progress every 10 batches
                if batch_num % 10 == 0:
                    save_progress(batch_idx + len(batch_texts), total, all_embeddings)
                    print(f"    [Progress saved]")
            else:
                print(f" ✗ FAILED")
                return
        
        # All embeddings done, save final progress
        save_progress(total, total, all_embeddings)
        
        print(f"\n✓ Generated {len(all_embeddings)} embeddings")
        print(f"Storing in vector database...\n")
        
        # Store in vector DB
        store_batch_size = 100
        total_store_batches = (total + store_batch_size - 1) // store_batch_size
        
        all_point_ids = []
        for batch_idx in range(0, total, store_batch_size):
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
        
        # Clean up progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        
        total_time = time.time() - start_time
        print()
        print("=" * 70)
        print("✅ INDEXING COMPLETE!")
        print(f"   Total entries: {len(all_point_ids)}")
        print(f"   Time: {total_time/60:.1f} minutes")
        print(f"   Collection: {collection_name}")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted! Progress saved.")
        print(f"   Run again to resume from batch {batch_idx // embedding_batch_size + 1}")
        save_progress(batch_idx, total, all_embeddings)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        if batch_idx > start_idx:
            print(f"\n⚠️  Saving progress...")
            save_progress(batch_idx, total, all_embeddings)

if __name__ == "__main__":
    index_celebrity_database_with_resume()

