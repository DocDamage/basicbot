"""Main script to process all books from the books folder"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bmad.framework import BMADFramework
from src.agents.book_agent import BookAgent
from src.agents.document_agent import DocumentAgent
from src.agents.retrieval_agent import RetrievalAgent

print("=" * 70)
print("BOOK PROCESSING PIPELINE")
print("=" * 70)
print()

# Initialize framework
memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
framework = BMADFramework(memory_storage_path=memory_path)

# Register agents
print("Initializing agents...")
book_agent = BookAgent(framework=framework)
framework.register_agent(book_agent)

document_agent = DocumentAgent(framework=framework)
framework.register_agent(document_agent)

retrieval_agent = RetrievalAgent(framework=framework)
framework.register_agent(retrieval_agent)

print("✓ Agents initialized")
print()

# Process books
print("Processing books from books/ folder...")
print("-" * 70)

result = book_agent.process_book_directory()

if result.get('success'):
    print()
    print("=" * 70)
    print("BOOK PROCESSING COMPLETE")
    print("=" * 70)
    print(f"Total files found: {result.get('total_files', 0)}")
    print(f"Successfully processed: {result.get('processed', 0)}")
    print(f"Errors: {result.get('errors', 0)}")
    print(f"Duplicates found: {result.get('duplicates_found', 0)}")
    print()
    
    # Process chunks for indexing
    if result.get('processed'):
        print("Indexing book chunks in vector database...")
        print("-" * 70)
        
        processed_book_ids = result.get('processed_book_ids', [])
        processed_books = book_agent.get_processed_books()
        
        total_chunks = 0
        for book_id in processed_book_ids:
            if book_id in processed_books:
                book_data = processed_books[book_id]
                processed_file = book_data.get('processed_file')
                
                if processed_file and os.path.exists(processed_file):
                    # Process with DocumentAgent (with book metadata for proper chunking)
                    book_metadata = book_data.get('metadata', {})
                    doc_result = document_agent.process({
                        'file_paths': [processed_file]
                    }, book_metadata=book_metadata)
                    
                    chunks = doc_result.get('chunks', [])
                    if chunks:
                        # Add book metadata to chunks if not already present
                        for chunk in chunks:
                            chunk_meta = chunk.get('metadata', {})
                            if 'book_id' not in chunk_meta:
                                chunk_meta['book_id'] = book_id
                                chunk_meta['book_title'] = book_metadata.get('title', '')
                                chunk_meta['author'] = book_metadata.get('author', '')
                                chunk_meta['series'] = book_metadata.get('series', '')
                                chunk_meta['content_type'] = 'book'
                                
                                # Add character/location mentions if available
                                if 'characters' in book_metadata:
                                    chunk_meta['characters_mentioned'] = book_metadata.get('characters', [])
                                if 'locations' in book_metadata:
                                    chunk_meta['locations_mentioned'] = book_metadata.get('locations', [])
                            
                            chunk['metadata'] = chunk_meta
                        
                        # Index chunks
                        retrieval_agent.index_chunks(chunks)
                        total_chunks += len(chunks)
                        print(f"  ✓ Indexed {len(chunks)} chunks from {book_metadata.get('title', book_id)}")
        
        print()
        print(f"✓ Total chunks indexed: {total_chunks}")
        print()
    
    print("=" * 70)
    print("All books are now searchable in the database!")
    print("=" * 70)
    print()
    print("You can now:")
    print("  - Search books by title, author, series, character, quote, or genre")
    print("  - Browse books in the GUI")
    print("  - Read books in the reading interface")
    print("  - Use books as reference for writing")
    print()
else:
    print(f"Error processing books: {result.get('error', 'Unknown error')}")
    sys.exit(1)

# Start file watcher for new books
print("Starting file watcher for new books...")
book_agent.start_watching()
print("✓ File watcher active. New books will be automatically processed.")
print()

print("Press Ctrl+C to stop the file watcher and exit.")
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping file watcher...")
    book_agent.stop_watching()
    print("✓ File watcher stopped.")
    print("Goodbye!")

