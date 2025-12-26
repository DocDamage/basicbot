"""Properly index WikiEpstein PDFs by extracting text first"""

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
from src.tools.pdf_tools import pdf_extract_text
from src.tools.chunking_tools import hybrid_chunk_markdown
from src.config import get_settings
from dotenv import load_dotenv

load_dotenv()

PROGRESS_FILE = "pdf_indexing_progress.json"

def load_progress():
    """Load saved progress"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return None

def save_progress(files_processed, total_files, chunks_created):
    """Save progress"""
    progress = {
        'files_processed': files_processed,
        'total_files': total_files,
        'chunks_created': chunks_created,
        'timestamp': time.time()
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def index_wikiepstein_pdfs_properly():
    """Index WikiEpstein PDFs by extracting text properly"""
    print("=" * 70)
    print("Indexing WikiEpstein PDFs (Proper PDF Text Extraction)")
    print("=" * 70)
    print()
    
    # Check for existing progress
    saved_progress = load_progress()
    if saved_progress:
        print(f"Found saved progress: {saved_progress['files_processed']}/{saved_progress['total_files']} files, {saved_progress['chunks_created']} chunks")
        if len(sys.argv) > 1 and sys.argv[1] == '--no-resume':
            print("Starting fresh (--no-resume flag)")
            os.remove(PROGRESS_FILE)
            saved_progress = None
        else:
            print("Auto-resuming from saved progress...")
            resume_from = saved_progress['files_processed']
    else:
        resume_from = 0
    
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
    
    print()
    
    # Find PDF files
    extracted_dir = Path(__file__).parent / "data" / "epstein_files" / "wikiepstein_extracted"
    pdf_files = list(extracted_dir.rglob("*.pdf"))
    
    print(f"Found {len(pdf_files)} PDF files to index")
    print()
    
    if not pdf_files:
        print("No PDF files found to index!")
        return
    
    # Resume from saved position if applicable
    if saved_progress and resume_from > 0:
        pdf_files = pdf_files[resume_from:]
        print(f"Resuming from file {resume_from + 1}...")
        print()
    
    # Process PDFs in batches
    batch_size = 20  # Smaller batches for PDFs (they take longer)
    total_processed = saved_progress['files_processed'] if saved_progress else 0
    total_chunks_created = saved_progress['chunks_created'] if saved_progress else 0
    total_files = len(pdf_files) + (saved_progress['files_processed'] if saved_progress else 0)
    
    all_chunks = []
    start_time = time.time()
    
    try:
        for batch_start in range(0, len(pdf_files), batch_size):
            batch_files = pdf_files[batch_start:batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (len(pdf_files) + batch_size - 1) // batch_size
            
            current_file_num = total_processed + batch_start + 1
            
            print(f"[{time.strftime('%H:%M:%S')}] Batch {batch_num}/{total_batches}: Processing {len(batch_files)} PDFs (files {current_file_num}-{min(current_file_num + len(batch_files) - 1, total_files)})...")
            
            batch_chunks = []
            batch_processed = 0
            
            for pdf_file in batch_files:
                try:
                    # Convert to relative path for security validation
                    pdf_path = str(pdf_file)
                    # Try relative path first
                    try:
                        pdf_path = os.path.relpath(pdf_path)
                    except:
                        pass  # Use absolute if relative fails
                    
                    # Extract text from PDF
                    result = pdf_extract_text(pdf_path)
                    
                    if not result.get('success'):
                        print(f"  ⚠️  Failed to extract text from {pdf_file.name}: {result.get('error', 'Unknown error')}")
                        continue
                    
                    text = result.get('result', '')
                    
                    if not text or len(text.strip()) < 10:
                        print(f"  ⚠️  No text extracted from {pdf_file.name} (empty or too short)")
                        continue
                    
                    # Chunk the text (create a simple structure for chunking)
                    structure = {'content': text, 'headers': [], 'code_blocks': [], 'links': [], 'file_path': str(pdf_file)}
                    chunks = hybrid_chunk_markdown(text, structure, chunk_size=500, chunk_overlap=50)
                    
                    # Add metadata to each chunk
                    for chunk in chunks:
                        chunk['metadata'] = {
                            'source': 'wikiepstein_pdf',
                            'file_path': str(pdf_file),
                            'file_name': pdf_file.name,
                            **chunk.get('metadata', {})
                        }
                        chunk['content'] = chunk.get('content', chunk.get('text', ''))
                    
                    batch_chunks.extend(chunks)
                    batch_processed += 1
                    
                except Exception as e:
                    print(f"  ⚠️  Error processing {pdf_file.name}: {e}")
                    continue
            
            if batch_chunks:
                # Index chunks for this batch
                print(f"  Indexing {len(batch_chunks)} chunks...", end='', flush=True)
                retrieval_agent.index_chunks(batch_chunks)
                print(f" ✓")
            
            total_processed += batch_processed
            total_chunks_created += len(batch_chunks)
            
            # Save progress
            save_progress(total_processed, total_files, total_chunks_created)
            
            # Show progress
            elapsed = time.time() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            remaining = (total_files - total_processed) / rate if rate > 0 else 0
            
            print(f"  Progress: {total_processed}/{total_files} files ({total_processed/total_files*100:.1f}%), {total_chunks_created} chunks created")
            print(f"  Rate: {rate:.2f} files/s, Est. remaining: {remaining/60:.1f} minutes")
            print()
        
        # Clean up progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        
        total_time = time.time() - start_time
        print("=" * 70)
        print("✅ INDEXING COMPLETE!")
        print(f"  Files processed: {total_processed}")
        print(f"  Chunks created: {total_chunks_created}")
        print(f"  Time: {total_time/60:.1f} minutes")
        print(f"  Collection: {collection_name}")
        print("=" * 70)
        print()
        print("All PDFs are now searchable in your chatbot!")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted! Progress saved.")
        print(f"   Processed {total_processed}/{total_files} files, {total_chunks_created} chunks")
        print(f"   Run again to resume")
        save_progress(total_processed, total_files, total_chunks_created)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n⚠️  Saving progress...")
        save_progress(total_processed, total_files, total_chunks_created)

if __name__ == "__main__":
    index_wikiepstein_pdfs_properly()

