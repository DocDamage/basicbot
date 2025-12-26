"""Index WikiEpstein PDFs with progress saving and resume capability"""

import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bmad.framework import BMADFramework
from src.agents import DocumentAgent, RetrievalAgent
from src.tools.vector_tools import initialize_collection
from src.tools.embedding_tools import get_embedding_dimension
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

def save_progress(files_processed, total_files, current_file):
    """Save progress"""
    progress = {
        'files_processed': files_processed,
        'total_files': total_files,
        'current_file': current_file,
        'timestamp': time.time()
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def index_wikiepstein_pdfs():
    """Index WikiEpstein PDF files"""
    print("=" * 70)
    print("Indexing WikiEpstein PDFs (With Progress Saving)")
    print("=" * 70)
    print()
    
    # Check for existing progress
    saved_progress = load_progress()
    if saved_progress:
        print(f"Found saved progress: {saved_progress['files_processed']}/{saved_progress['total_files']} files processed")
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
    
    # Register agents
    document_agent = DocumentAgent(framework=framework)
    framework.register_agent(document_agent)
    
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
    
    # Find files to index
    extracted_dir = Path(__file__).parent / "data" / "epstein_files" / "wikiepstein_extracted"
    
    # Find PDFs and text files
    pdf_files = list(extracted_dir.rglob("*.pdf"))
    txt_files = list(extracted_dir.rglob("*.txt"))
    html_files = list(extracted_dir.rglob("*.html")) + list(extracted_dir.rglob("*.htm"))
    
    all_files = pdf_files + txt_files + html_files
    
    print(f"Found {len(all_files)} files to index:")
    print(f"  - PDFs: {len(pdf_files)}")
    print(f"  - Text files: {len(txt_files)}")
    print(f"  - HTML files: {len(html_files)}")
    print()
    
    if not all_files:
        print("No files found to index!")
        return
    
    # Resume from saved position if applicable
    if saved_progress and resume_from > 0:
        all_files = all_files[resume_from:]
        print(f"Resuming from file {resume_from + 1}...")
        print()
    
    # Process files in batches
    batch_size = 50  # Smaller batches for PDFs (they're larger)
    total_processed = saved_progress['files_processed'] if saved_progress else 0
    total_chunks = 0
    total_files = len(all_files) + (saved_progress['files_processed'] if saved_progress else 0)
    
    start_time = time.time()
    
    try:
        for batch_start in range(0, len(all_files), batch_size):
            batch_files = all_files[batch_start:batch_start + batch_size]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (len(all_files) + batch_size - 1) // batch_size
            
            current_file_num = total_processed + batch_start + 1
            
            print(f"[{time.strftime('%H:%M:%S')}] Processing batch {batch_num}/{total_batches} (files {current_file_num}-{min(current_file_num + len(batch_files) - 1, total_files)}/{total_files})...")
            
            # Process files
            result = document_agent.process({
                "file_paths": [str(f) for f in batch_files]
            })
            
            files_processed = result.get('files_processed', 0)
            chunks_created = result.get('chunks_created', 0)
            chunks = result.get('chunks', [])
            
            total_processed += files_processed
            total_chunks += chunks_created
            
            # Index chunks
            if chunks:
                print(f"  Indexing {len(chunks)} chunks...", end='', flush=True)
                retrieval_agent.index_chunks(chunks)
                print(f" ✓")
            
            # Save progress
            save_progress(total_processed, total_files, str(batch_files[-1]) if batch_files else "")
            
            # Show progress
            elapsed = time.time() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            remaining = (total_files - total_processed) / rate if rate > 0 else 0
            
            print(f"  Progress: {total_processed}/{total_files} files ({total_processed/total_files*100:.1f}%)")
            print(f"  Rate: {rate:.2f} files/s, Est. remaining: {remaining/60:.1f} minutes")
            print()
        
        # Clean up progress file
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        
        total_time = time.time() - start_time
        print("=" * 70)
        print("✅ INDEXING COMPLETE!")
        print(f"  Files processed: {total_processed}")
        print(f"  Chunks created: {total_chunks}")
        print(f"  Time: {total_time/60:.1f} minutes")
        print(f"  Collection: {collection_name}")
        print("=" * 70)
        print()
        print("All PDFs are now searchable in your chatbot!")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted! Progress saved.")
        print(f"   Processed {total_processed}/{total_files} files")
        print(f"   Run again to resume")
        save_progress(total_processed, total_files, "")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n⚠️  Saving progress...")
        save_progress(total_processed, total_files, "")

if __name__ == "__main__":
    index_wikiepstein_pdfs()

