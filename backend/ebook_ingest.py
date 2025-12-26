"""Backend ebook ingestion script for processing books from the books folder"""

# CRITICAL: Python 3.13 compatibility fix - MUST be first, before ANY other imports
import sys
import os
from pathlib import Path

# Add project root to path FIRST
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import and execute compatibility shim IMMEDIATELY
try:
    from src.utils.six_moves_compat import *  # noqa: F401, F403
except ImportError:
    # Fallback: inline compatibility fix if module doesn't exist
    import types
    import io
    import queue
    
    # Create six module if it doesn't exist
    if 'six' not in sys.modules:
        six_module = types.ModuleType('six')
        six_module.string_types = str
        six_module.text_type = str
        six_module.binary_type = bytes
        six_module.integer_types = int
        six_module.class_types = type
        six_module.PY2 = False
        six_module.PY3 = True
        six_module.StringIO = io.StringIO
        
        # Add utility functions
        def b(s):
            """Convert string to bytes (Python 3 compatibility)"""
            if isinstance(s, bytes):
                return s
            return s.encode('utf-8')
        six_module.b = b
        
        def u(s):
            """Convert bytes to string (Python 3 compatibility)"""
            if isinstance(s, str):
                return s
            return s.decode('utf-8')
        six_module.u = u
        
        def add_metaclass(metaclass):
            def wrapper(cls):
                orig_vars = cls.__dict__.copy()
                slots = orig_vars.get('__slots__')
                if slots is not None:
                    if isinstance(slots, str):
                        slots = [slots]
                    for slots_var in slots:
                        orig_vars.pop(slots_var, None)
                orig_vars.pop('__dict__', None)
                orig_vars.pop('__weakref__', None)
                return metaclass(cls.__name__, cls.__bases__, orig_vars)
            return wrapper
        six_module.add_metaclass = add_metaclass
        sys.modules['six'] = six_module
    
    # Create six.moves if it doesn't exist
    if 'six.moves' not in sys.modules:
        moves = types.ModuleType('six.moves')
        moves.__path__ = []
        sys.modules['six.moves'] = moves
        
        try:
            import _thread
            moves._thread = _thread
        except ImportError:
            try:
                import thread as _thread
                moves._thread = _thread
            except ImportError:
                pass
        
        moves.StringIO = io.StringIO
        moves.cStringIO = io.StringIO
        moves.queue = queue
        moves.Queue = queue.Queue
        
        # Create urllib subpackage
        urllib = types.ModuleType('six.moves.urllib')
        urllib.__path__ = []
        sys.modules['six.moves.urllib'] = urllib
        
        try:
            from urllib import parse as urllib_parse_module
            urllib_parse = types.ModuleType('six.moves.urllib_parse')
            urllib_parse.urlparse = urllib_parse_module.urlparse
            urllib_parse.urlunparse = urllib_parse_module.urlunparse
            urllib_parse.urljoin = urllib_parse_module.urljoin
            urllib_parse.urlsplit = urllib_parse_module.urlsplit
            urllib_parse.urlunsplit = urllib_parse_module.urlunsplit
            urllib_parse.quote = urllib_parse_module.quote
            urllib_parse.unquote = urllib_parse_module.unquote
            sys.modules['six.moves.urllib_parse'] = urllib_parse
            
            urllib_parse_nested = types.ModuleType('six.moves.urllib.parse')
            urllib_parse_nested.urlparse = urllib_parse_module.urlparse
            urllib_parse_nested.urlunparse = urllib_parse_module.urlunparse
            urllib_parse_nested.urljoin = urllib_parse_module.urljoin
            urllib_parse_nested.urlsplit = urllib_parse_module.urlsplit
            urllib_parse_nested.urlunsplit = urllib_parse_module.urlunsplit
            urllib_parse_nested.quote = urllib_parse_module.quote
            urllib_parse_nested.unquote = urllib_parse_module.unquote
            sys.modules['six.moves.urllib.parse'] = urllib_parse_nested
            urllib.parse = urllib_parse_nested
        except ImportError:
            pass
        
        try:
            from urllib import request as urllib_request_module
            urllib_request = types.ModuleType('six.moves.urllib_request')
            urllib_request.urlopen = urllib_request_module.urlopen
            urllib_request.Request = urllib_request_module.Request
            sys.modules['six.moves.urllib_request'] = urllib_request
            
            urllib_request_nested = types.ModuleType('six.moves.urllib.request')
            urllib_request_nested.urlopen = urllib_request_module.urlopen
            urllib_request_nested.Request = urllib_request_module.Request
            sys.modules['six.moves.urllib.request'] = urllib_request_nested
            urllib.request = urllib_request_nested
        except ImportError:
            pass

# NOW safe to import other modules
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.bmad.framework import BMADFramework
from src.agents.book_agent import BookAgent
from src.agents.document_agent import DocumentAgent
from src.agents.retrieval_agent import RetrievalAgent

import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'data/logs/ebook_ingest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ebook_ingest')


def ingest_ebooks(books_dir: str = None, recursive: bool = True, index: bool = True):
    """
    Ingest ebooks from the books directory
    
    Args:
        books_dir: Directory containing books (defaults to ./books)
        recursive: Whether to process recursively
        index: Whether to index books in vector database
    """
    logger.info("=" * 70)
    logger.info("EBOOK INGESTION PIPELINE")
    logger.info("=" * 70)
    logger.info("")
    
    # Initialize framework
    memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
    framework = BMADFramework(memory_storage_path=memory_path)
    
    # Register agents
    logger.info("Initializing agents...")
    book_agent = BookAgent(framework=framework)
    framework.register_agent(book_agent)
    
    document_agent = DocumentAgent(framework=framework)
    framework.register_agent(document_agent)
    
    retrieval_agent = RetrievalAgent(framework=framework)
    framework.register_agent(retrieval_agent)
    
    logger.info("✓ Agents initialized")
    logger.info("")
    
    # Process books
    if books_dir is None:
        books_dir = os.getenv("BOOKS_DIR", "./books")
    
    logger.info(f"Processing books from {books_dir}...")
    logger.info("-" * 70)
    
    result = book_agent._process_book_directory(books_dir, recursive=recursive)
    
    if result.get('success'):
        logger.info("")
        logger.info("=" * 70)
        logger.info("BOOK PROCESSING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total files found: {result.get('total_files', 0)}")
        logger.info(f"Successfully processed: {result.get('processed', 0)}")
        logger.info(f"Errors: {result.get('errors', 0)}")
        logger.info(f"Duplicates found: {result.get('duplicates_found', 0)}")
        logger.info("")
        
        # Index books in vector database if requested
        if index and result.get('processed'):
            logger.info("Indexing book chunks in vector database...")
            logger.info("-" * 70)
            
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
                            logger.info(f"  ✓ Indexed {len(chunks)} chunks from {book_metadata.get('title', book_id)}")
            
            logger.info("")
            logger.info(f"✓ Total chunks indexed: {total_chunks}")
            logger.info("")
        
        logger.info("=" * 70)
        logger.info("Ebook ingestion complete!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Books are now:")
        logger.info("  - Processed and stored in data/extracted_docs/books/")
        logger.info("  - Searchable in the vector database")
        logger.info("  - Available for reading in the GUI")
        logger.info("  - Ready for use as writing references")
        logger.info("")
        
        return {
            'success': True,
            'total_files': result.get('total_files', 0),
            'processed': result.get('processed', 0),
            'errors': result.get('errors', 0),
            'total_chunks': total_chunks if index else 0
        }
    else:
        logger.error(f"Error processing books: {result.get('error', 'Unknown error')}")
        return {
            'success': False,
            'error': result.get('error', 'Unknown error')
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest ebooks from books folder')
    parser.add_argument(
        '--books-dir',
        type=str,
        default=None,
        help='Directory containing books (default: ./books)'
    )
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not process subdirectories recursively'
    )
    parser.add_argument(
        '--no-index',
        action='store_true',
        help='Do not index books in vector database'
    )
    
    args = parser.parse_args()
    
    result = ingest_ebooks(
        books_dir=args.books_dir,
        recursive=not args.no_recursive,
        index=not args.no_index
    )
    
    if not result.get('success'):
        sys.exit(1)


if __name__ == '__main__':
    main()

