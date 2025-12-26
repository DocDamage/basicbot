"""Book Processing Agent for PDF, EPUB, MOBI, and TXT files"""

import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.book_tools import (
    extract_book_content,
    extract_book_metadata,
    merge_book_formats,
    archive_original_file
)
from ..tools.entity_extraction_tools import extract_entities, build_entity_index


class BookFileHandler(FileSystemEventHandler):
    """Handler for book file system changes"""
    
    def __init__(self, agent):
        self.agent = agent
    
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if any(file_path.lower().endswith(ext) for ext in ['.pdf', '.epub', '.mobi', '.txt']):
                self.agent.on_new_book(file_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if any(file_path.lower().endswith(ext) for ext in ['.pdf', '.epub', '.mobi', '.txt']):
                self.agent.on_book_changed(file_path)


class BookAgent(BaseAgent):
    """Agent for processing book files (PDF, EPUB, MOBI, TXT)"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="process_book_file",
                description="Process a single book file",
                func=self._process_book_file
            ),
            AgentTool(
                name="process_book_directory",
                description="Batch process all books in a directory",
                func=self._process_book_directory
            ),
            AgentTool(
                name="extract_book_metadata",
                description="Extract comprehensive metadata from book file",
                func=self._extract_book_metadata
            ),
            AgentTool(
                name="detect_duplicates",
                description="Find duplicate books across formats",
                func=self._detect_duplicates
            ),
            AgentTool(
                name="merge_duplicates",
                description="Merge duplicate book entries",
                func=self._merge_duplicates
            )
        ]
        
        super().__init__(
            agent_id="book_agent",
            role=AgentRole.BOOK_PROCESSOR,
            description="Processes book files (PDF, EPUB, MOBI, TXT) and extracts metadata",
            tools=tools,
            framework=framework
        )
        
        self.books_dir = os.getenv("BOOKS_DIR", "./books")
        self.extracted_docs_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
        self.archive_dir = os.path.join(self.books_dir, ".archive")
        self.books_metadata_dir = os.path.join(self.extracted_docs_dir, "books", "metadata")
        self.books_processed_dir = os.path.join(self.extracted_docs_dir, "books", "processed")
        self.entities_dir = os.path.join(self.extracted_docs_dir, "books", "entities")
        
        # Create directories
        for dir_path in [self.archive_dir, self.books_metadata_dir, self.books_processed_dir, self.entities_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        self.processed_books: Dict[str, Dict] = {}  # book_id -> book_data
        self.observer: Optional[Observer] = None
        
        # Setup logging
        log_dir = os.getenv("LOG_DIR", "./data/logs")
        os.makedirs(log_dir, exist_ok=True)
        self.logger = logging.getLogger(f"{self.agent_id}_logger")
        self.logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(
            os.path.join(log_dir, f"book_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
    
    def _process_book_file(self, file_path: str, extract_entities_flag: bool = True) -> Dict[str, Any]:
        """
        Process a single book file
        
        Args:
            file_path: Path to book file
            extract_entities_flag: Whether to extract entities
            
        Returns:
            Dictionary with processing results
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            file_ext = path_obj.suffix.lower()
            if file_ext not in ['.pdf', '.epub', '.mobi', '.txt']:
                return {'success': False, 'error': f'Unsupported file format: {file_ext}'}
            
            self.logger.info(f"Processing book: {file_path}")
            
            # Extract content
            result = extract_book_content(file_path)
            if not result.get('success'):
                return result
            
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            chapters = result.get('chapters', [])
            
            # Generate book ID
            book_id = str(uuid.uuid4())
            metadata['book_id'] = book_id
            metadata['file_path'] = file_path
            metadata['chapters'] = chapters
            
            # Extract entities if requested
            if extract_entities_flag and content:
                entities = extract_entities(content)
                metadata['characters'] = entities.get('characters', [])
                metadata['locations'] = entities.get('locations', [])
                metadata['entities'] = entities.get('entities', [])
            
            # Save metadata
            metadata_file = os.path.join(self.books_metadata_dir, f"{book_id}.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Save processed content as markdown
            processed_file = os.path.join(self.books_processed_dir, f"{book_id}.md")
            with open(processed_file, 'w', encoding='utf-8') as f:
                f.write(f"# {metadata.get('title', 'Unknown Title')}\n\n")
                f.write(f"**Author:** {metadata.get('author', 'Unknown')}\n\n")
                if metadata.get('series'):
                    f.write(f"**Series:** {metadata.get('series')}\n\n")
                f.write("---\n\n")
                f.write(content)
            
            # Store in memory
            book_data = {
                'book_id': book_id,
                'metadata': metadata,
                'content': content,
                'chapters': chapters,
                'processed_file': processed_file,
                'metadata_file': metadata_file
            }
            self.processed_books[book_id] = book_data
            
            self.logger.info(f"Successfully processed book: {metadata.get('title', file_path)}")
            
            return {
                'success': True,
                'book_id': book_id,
                'book_data': book_data,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error processing book {file_path}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _process_book_directory(self, directory: Optional[str] = None, recursive: bool = True) -> Dict[str, Any]:
        """
        Batch process all books in a directory
        
        Args:
            directory: Directory path (defaults to books_dir)
            recursive: Whether to process recursively
            
        Returns:
            Dictionary with processing results
        """
        if directory is None:
            directory = self.books_dir
        
        dir_path = Path(directory)
        if not dir_path.exists():
            return {'success': False, 'error': f'Directory not found: {directory}'}
        
        # Find all book files
        extensions = ['.pdf', '.epub', '.mobi', '.txt']
        book_files = []
        
        if recursive:
            for ext in extensions:
                book_files.extend(dir_path.rglob(f'*{ext}'))
        else:
            for ext in extensions:
                book_files.extend(dir_path.glob(f'*{ext}'))
        
        # Filter out archived files
        book_files = [f for f in book_files if '.archive' not in str(f)]
        
        self.logger.info(f"Found {len(book_files)} book files to process")
        
        processed = []
        errors = []
        duplicates_found = []
        
        # Process each file
        for i, file_path in enumerate(book_files, 1):
            self.logger.info(f"Processing {i}/{len(book_files)}: {file_path.name}")
            
            result = self._process_book_file(str(file_path))
            if result.get('success'):
                processed.append(result.get('book_id'))
            else:
                errors.append({'file': str(file_path), 'error': result.get('error')})
        
        # Detect and merge duplicates
        if processed:
            duplicates = self._detect_duplicates()
            if duplicates:
                duplicates_found = duplicates
                merged = self._merge_duplicates()
                self.logger.info(f"Merged {len(merged)} duplicate book groups")
        
        # Build entity index
        entity_index = None
        if processed:
            books_data = [self.processed_books[book_id] for book_id in processed if book_id in self.processed_books]
            entity_index = build_entity_index(books_data)
            
            # Save entity index
            index_file = os.path.join(self.entities_dir, "entity_index.json")
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(entity_index, f, indent=2, ensure_ascii=False)
        
        return {
            'success': True,
            'total_files': len(book_files),
            'processed': len(processed),
            'errors': len(errors),
            'duplicates_found': len(duplicates_found),
            'processed_book_ids': processed,
            'error_details': errors,
            'entity_index': entity_index is not None
        }
    
    def _extract_book_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from book file"""
        path_obj = Path(file_path)
        file_ext = path_obj.suffix.lower()
        file_type = file_ext[1:] if file_ext.startswith('.') else file_ext
        
        return extract_book_metadata(file_path, file_type)
    
    def _detect_duplicates(self) -> List[List[str]]:
        """
        Detect duplicate books across formats
        
        Returns:
            List of duplicate groups (each group contains book_ids of duplicates)
        """
        # Group books by title and author
        title_author_map = {}
        
        for book_id, book_data in self.processed_books.items():
            metadata = book_data.get('metadata', {})
            title = metadata.get('title', '').lower().strip()
            author = metadata.get('author', '').lower().strip()
            
            if title and author:
                key = f"{title}::{author}"
                if key not in title_author_map:
                    title_author_map[key] = []
                title_author_map[key].append(book_id)
        
        # Find groups with multiple entries (duplicates)
        duplicates = [book_ids for book_ids in title_author_map.values() if len(book_ids) > 1]
        
        return duplicates
    
    def _merge_duplicates(self) -> List[Dict[str, Any]]:
        """
        Merge duplicate book entries
        
        Returns:
            List of merged book data dictionaries
        """
        duplicates = self._detect_duplicates()
        merged_books = []
        
        for duplicate_group in duplicates:
            # Get book data for all duplicates
            book_entries = []
            for book_id in duplicate_group:
                if book_id in self.processed_books:
                    book_data = self.processed_books[book_id]
                    book_entries.append({
                        'metadata': book_data.get('metadata', {}),
                        'content': book_data.get('content', ''),
                        'chapters': book_data.get('chapters', [])
                    })
            
            if book_entries:
                # Merge entries
                merged = merge_book_formats(book_entries)
                
                # Use first book_id as primary
                primary_id = duplicate_group[0]
                merged['book_id'] = primary_id
                merged['metadata']['book_id'] = primary_id
                
                # Update processed_books
                self.processed_books[primary_id].update(merged)
                
                # Remove other duplicates from processed_books
                for book_id in duplicate_group[1:]:
                    if book_id in self.processed_books:
                        del self.processed_books[book_id]
                
                merged_books.append(merged)
        
        return merged_books
    
    def on_new_book(self, file_path: str):
        """Handle new book file detected"""
        self.logger.info(f"New book detected: {file_path}")
        result = self._process_book_file(file_path)
        if result.get('success'):
            # Notify DocumentAgent to process the new book
            if self.framework:
                document_agent = self.framework.get_agent("document_agent")
                if document_agent:
                    book_data = result.get('book_data', {})
                    processed_file = book_data.get('processed_file')
                    if processed_file:
                        self.send_message("document_agent", {
                            "action": "process_book",
                            "file_path": processed_file,
                            "book_id": result.get('book_id')
                        })
    
    def on_book_changed(self, file_path: str):
        """Handle book file modification"""
        self.logger.info(f"Book file changed: {file_path}")
        # Re-process the book
        self.on_new_book(file_path)
    
    def start_watching(self):
        """Start watching books directory for new files"""
        if self.observer is not None:
            return
        
        event_handler = BookFileHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.books_dir, recursive=True)
        self.observer.start()
        self.logger.info(f"Started watching books directory: {self.books_dir}")
    
    def stop_watching(self):
        """Stop watching books directory"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.logger.info("Stopped watching books directory")
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process books based on input
        
        Args:
            input_data: Can be a file path, directory path, or dict with 'file_path' or 'directory'
            **kwargs: Additional parameters
            
        Returns:
            Processing results
        """
        if isinstance(input_data, str):
            path_obj = Path(input_data)
            if path_obj.is_file():
                return self._process_book_file(input_data)
            elif path_obj.is_dir():
                return self._process_book_directory(input_data)
            else:
                return {'success': False, 'error': f'Path not found: {input_data}'}
        elif isinstance(input_data, dict):
            file_path = input_data.get('file_path')
            directory = input_data.get('directory')
            
            if file_path:
                return self._process_book_file(file_path)
            elif directory:
                return self._process_book_directory(directory)
            else:
                return {'success': False, 'error': 'No file_path or directory specified'}
        else:
            # Default: process books directory
            return self._process_book_directory()
    
    def get_processed_books(self) -> Dict[str, Dict]:
        """Get all processed books"""
        return self.processed_books
    
    def shutdown(self):
        """Shutdown agent"""
        self.stop_watching()

