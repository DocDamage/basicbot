"""Document Processing Agent"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import os
import logging
import threading
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.document_tools import extract_markdown_from_zip, parse_markdown_structure
from ..tools.chunking_tools import hybrid_chunk_markdown, chunk_by_chapters, hybrid_chunk_book


class DocumentChangeHandler(FileSystemEventHandler):
    """Handler for file system changes"""
    
    def __init__(self, agent):
        self.agent = agent
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            self.agent.on_file_changed(event.src_path)


class DocumentAgent(BaseAgent):
    """Agent for processing Markdown documents"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="extract_zip",
                description="Extract Markdown files from zip archive",
                func=self._extract_zip
            ),
            AgentTool(
                name="parse_markdown",
                description="Parse Markdown file structure",
                func=self._parse_markdown
            ),
            AgentTool(
                name="chunk_document",
                description="Chunk document using hybrid strategy",
                func=self._chunk_document
            )
        ]
        
        super().__init__(
            agent_id="document_agent",
            role=AgentRole.DOCUMENT_PROCESSOR,
            description="Processes and chunks Markdown documents from zip archives",
            tools=tools,
            framework=framework
        )
        
        self.extracted_files: List[str] = []
        self.parsed_documents: Dict[str, Dict] = {}
        self.chunks: List[Dict] = []
        self.observer: Optional[Observer] = None
        self.extracted_docs_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
        
        # Setup logging
        log_dir = os.getenv("LOG_DIR", "./data/logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"document_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # Progress tracking file
        progress_file = os.path.join(log_dir, "progress.txt")
        self.progress_file = progress_file
        
        self.logger = logging.getLogger(f"{self.agent_id}_logger")
        self.logger.setLevel(logging.INFO)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for progress
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Document processing log: {log_file}")
        self.logger.info(f"Live progress tracker: {progress_file}")
        
        # Initialize progress file
        with open(progress_file, 'w', encoding='utf-8') as f:
            f.write("Document Processing Progress\n")
            f.write("=" * 60 + "\n")
            f.write("Status: Starting...\n")
            f.write("Files processed: 0\n")
            f.write("Errors: 0\n")
            f.write("Chunks created: 0\n")
            f.write("Current file: -\n")
            f.write("=" * 60 + "\n")
    
    def _extract_zip(self, zip_path: str, output_dir: Optional[str] = None) -> List[str]:
        """Extract Markdown files from zip"""
        if output_dir is None:
            output_dir = self.extracted_docs_dir
        
        files = extract_markdown_from_zip(zip_path, output_dir)
        self.extracted_files.extend(files)
        return files
    
    def _parse_markdown(self, file_path: str) -> Dict:
        """Parse Markdown file"""
        structure = parse_markdown_structure(file_path)
        self.parsed_documents[file_path] = structure
        return structure
    
    def _chunk_document(self, file_path: str, chunk_size: int = 500, chunk_overlap: int = 50, book_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Chunk a document
        
        Args:
            file_path: Path to document file
            chunk_size: Maximum chunk size
            chunk_overlap: Overlap between chunks
            book_metadata: Optional book metadata for book-specific chunking
        """
        if file_path not in self.parsed_documents:
            # Parse first if not already parsed
            self._parse_markdown(file_path)
        
        structure = self.parsed_documents[file_path]
        content = structure['content']
        
        # Check if this is a book (has book metadata)
        if book_metadata and 'chapters' in book_metadata:
            # Use book-specific chunking
            chapters = book_metadata.get('chapters', [])
            chunks = hybrid_chunk_book(
                content,
                chapters,
                book_metadata,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        else:
            # Use standard markdown chunking
            chunks = hybrid_chunk_markdown(
                content,
                structure,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        
        # Add source file to all chunks (normalize path)
        normalized_path = os.path.abspath(file_path).replace('\\', '/') if file_path else ''
        for chunk in chunks:
            chunk['source_file'] = normalized_path
        
        self.chunks.extend(chunks)
        return chunks
    
    def chunk_by_chapters(self, file_path: str, chapters: List[Dict], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict]:
        """
        Chunk document by chapters (book-specific)
        
        Args:
            file_path: Path to document file
            chapters: List of chapter dictionaries
            chunk_size: Maximum chunk size
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of chunks
        """
        if file_path not in self.parsed_documents:
            self._parse_markdown(file_path)
        
        structure = self.parsed_documents[file_path]
        content = structure['content']
        
        chunks = chunk_by_chapters(
            content,
            chapters,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Add source file to all chunks (normalize path)
        normalized_path = os.path.abspath(file_path).replace('\\', '/') if file_path else ''
        for chunk in chunks:
            chunk['source_file'] = normalized_path
        
        self.chunks.extend(chunks)
        return chunks
    
    def hybrid_chunk_book(self, file_path: str, chapters: List[Dict], book_metadata: Dict, chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict]:
        """
        Hybrid chunk book (chapter-based with sub-chunking)
        
        Args:
            file_path: Path to book file
            chapters: List of chapter dictionaries
            book_metadata: Book metadata dictionary
            chunk_size: Maximum chunk size
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of chunks
        """
        if file_path not in self.parsed_documents:
            self._parse_markdown(file_path)
        
        structure = self.parsed_documents[file_path]
        content = structure['content']
        
        chunks = hybrid_chunk_book(
            content,
            chapters,
            book_metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Add source file to all chunks (normalize path)
        normalized_path = os.path.abspath(file_path).replace('\\', '/') if file_path else ''
        for chunk in chunks:
            chunk['source_file'] = normalized_path
        
        self.chunks.extend(chunks)
        return chunks
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process documents from zip files or already-extracted files
        
        Args:
            input_data: Dict with 'zip_files' list, 'file_paths' list, or 'file_path' string
            **kwargs: Additional parameters (chunk_size, chunk_overlap, book_metadata, progress_tracker)
        """
        chunk_size = kwargs.get('chunk_size', 500)
        chunk_overlap = kwargs.get('chunk_overlap', 50)
        book_metadata = kwargs.get('book_metadata')
        progress_tracker = kwargs.get('progress_tracker')
        
        if isinstance(input_data, dict):
            zip_files = input_data.get('zip_files', [])
            file_paths = input_data.get('file_paths', [])  # List of already-extracted files
            file_path = input_data.get('file_path')
        elif isinstance(input_data, str):
            # Single file path
            if input_data.endswith('.zip'):
                zip_files = [input_data]
                file_path = None
                file_paths = []
            else:
                zip_files = []
                file_path = input_data
                file_paths = []
        else:
            zip_files = []
            file_path = None
            file_paths = []
        
        all_files = []
        
        # Use already-extracted files if provided (skip zip extraction)
        if file_paths:
            all_files = [f for f in file_paths if os.path.exists(f)]
            self.logger.info(f"Processing {len(all_files)} already-extracted files (skipping zip extraction)")
        else:
            # Extract from zip files
            for zip_file in zip_files:
                if os.path.exists(zip_file):
                    files = self.execute_tool("extract_zip", zip_path=zip_file)
                    all_files.extend(files)
            
            # Process single file if provided
            if file_path and os.path.exists(file_path):
                all_files.append(file_path)
        
        # Parse and chunk all files
        all_chunks = []
        total_files = len(all_files)
        processed_count = 0
        error_count = 0
        
        self.logger.info(f"Starting to process {total_files} files...")
        self._update_progress_file(0, total_files, 0, 0, 0, "Starting...")
        
        start_time = datetime.now()
        
        for idx, file_path in enumerate(all_files, 1):
            file_name = os.path.basename(file_path)
            progress_pct = (idx / total_files) * 100
            
            try:
                # Check file size before processing
                try:
                    file_size = os.path.getsize(file_path)
                    file_size_mb = file_size / (1024 * 1024)
                    
                    # Skip very large files (>10MB) to prevent freezing
                    if file_size_mb > 10:
                        self.logger.warning(f"[{idx}/{total_files}] ({progress_pct:.1f}%) ⚠️  SKIPPING large file ({file_size_mb:.1f}MB): {file_name}")
                        error_count += 1
                        continue
                    
                    # Warn about large files (>1MB)
                    if file_size_mb > 1:
                        self.logger.info(f"[{idx}/{total_files}] ({progress_pct:.1f}%) Processing large file ({file_size_mb:.1f}MB): {file_name}")
                    else:
                        self.logger.info(f"[{idx}/{total_files}] ({progress_pct:.1f}%) Processing: {file_name}")
                except OSError:
                    self.logger.warning(f"[{idx}/{total_files}] ({progress_pct:.1f}%) ⚠️  Cannot access file: {file_name}")
                    error_count += 1
                    continue
                
                # Parse with timeout protection (30 seconds per file)
                structure = None
                try:
                    # Use threading-based timeout for cross-platform support
                    parse_result = [None]
                    parse_error = [None]
                    
                    def parse_file():
                        try:
                            parse_result[0] = self.execute_tool("parse_markdown", file_path=file_path)
                        except Exception as e:
                            parse_error[0] = e
                    
                    parse_thread = threading.Thread(target=parse_file, daemon=True)
                    parse_thread.start()
                    parse_thread.join(timeout=30)  # 30 second timeout
                    
                    if parse_thread.is_alive():
                        self.logger.warning(f"  ⚠️  TIMEOUT parsing {file_name} (30s limit) - skipping")
                        error_count += 1
                        continue
                    
                    if parse_error[0]:
                        raise parse_error[0]
                    
                    structure = parse_result[0]
                    
                except TimeoutError:
                    self.logger.warning(f"  ⚠️  TIMEOUT parsing {file_name} - skipping")
                    error_count += 1
                    continue
                
                # Check if parsing was successful (has content)
                if not structure or not structure.get('content'):
                    self.logger.warning(f"  ⚠️  File has no content: {file_name}")
                    error_count += 1
                    continue
                
                # Chunk with timeout protection
                chunks = []
                try:
                    chunk_result = [None]
                    chunk_error = [None]
                    
                    def chunk_file():
                        try:
                            # Use book-specific chunking if book_metadata provided
                            if book_metadata:
                                chunk_result[0] = self.execute_tool(
                                    "chunk_document",
                                    file_path=file_path,
                                    chunk_size=chunk_size,
                                    chunk_overlap=chunk_overlap,
                                    book_metadata=book_metadata
                                )
                            else:
                                chunk_result[0] = self.execute_tool(
                                    "chunk_document",
                                    file_path=file_path,
                                    chunk_size=chunk_size,
                                    chunk_overlap=chunk_overlap
                                )
                        except Exception as e:
                            chunk_error[0] = e
                    
                    chunk_thread = threading.Thread(target=chunk_file, daemon=True)
                    chunk_thread.start()
                    chunk_thread.join(timeout=60)  # 60 second timeout for chunking
                    
                    if chunk_thread.is_alive():
                        self.logger.warning(f"  ⚠️  TIMEOUT chunking {file_name} (60s limit) - skipping")
                        error_count += 1
                        continue
                    
                    if chunk_error[0]:
                        raise chunk_error[0]
                    
                    chunks = chunk_result[0] or []
                    
                except TimeoutError:
                    self.logger.warning(f"  ⚠️  TIMEOUT chunking {file_name} - skipping")
                    error_count += 1
                    continue
                
                all_chunks.extend(chunks)
                processed_count += 1
                
                # Log chunk count for this file
                if chunks:
                    self.logger.debug(f"  ✓ Created {len(chunks)} chunks from {file_name}")
                else:
                    self.logger.warning(f"  ⚠️  No chunks created from {file_name}")
                
                # Update progress tracker if provided
                if progress_tracker:
                    progress_tracker.update_file(
                        processed=processed_count,
                        current_file=file_path,
                        message=f"Processing {os.path.basename(file_path)}"
                    )
                
                # Update progress file after each file
                elapsed = (datetime.now() - start_time).total_seconds()
                current_file_name = os.path.basename(file_path)
                self._update_progress_file(
                    idx, total_files, processed_count, error_count, 
                    len(all_chunks), current_file_name, elapsed
                )
                
                # Progress update every 100 files
                if idx % 100 == 0:
                    elapsed_min = elapsed / 60
                    rate = idx / elapsed if elapsed > 0 else 0
                    eta_seconds = (total_files - idx) / rate if rate > 0 else 0
                    eta_min = eta_seconds / 60
                    self.logger.info(f"  Progress: {processed_count} processed, {error_count} errors, {len(all_chunks)} total chunks")
                    self.logger.info(f"  Rate: {rate:.1f} files/sec | Elapsed: {elapsed_min:.1f} min | ETA: {eta_min:.1f} min")
                    
            except Exception as e:
                error_count += 1
                error_msg = f"Error processing {file_path}: {str(e)}"
                self.logger.error(error_msg, exc_info=True)  # exc_info=True includes full traceback
                self.logger.debug(f"  Full error details for {file_name}:", exc_info=True)
                continue
        
        total_time = (datetime.now() - start_time).total_seconds() / 60
        self.logger.info(f"Processing complete: {processed_count} files processed, {error_count} errors, {len(all_chunks)} total chunks created")
        self.logger.info(f"Total time: {total_time:.1f} minutes")
        self._update_progress_file(
            total_files, total_files, processed_count, error_count,
            len(all_chunks), "COMPLETE", (datetime.now() - start_time).total_seconds()
        )
        
        # Start file watcher for auto-updates
        self._start_file_watcher()
        
        result = {
            "files_processed": len(all_files),
            "chunks_created": len(all_chunks),
            "chunks": all_chunks
        }
        
        # Notify framework
        if self.framework:
            self.framework.memory.store(
                self.agent_id,
                result,
                {"type": "document_processing", "action": "process"}
            )
        
        return result
    
    def _start_file_watcher(self):
        """Start watching for file changes"""
        if self.observer is not None:
            return
        
        # Ensure directory exists
        os.makedirs(self.extracted_docs_dir, exist_ok=True)
        
        event_handler = DocumentChangeHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.extracted_docs_dir, recursive=True)
        self.observer.start()
        self.logger.info(f"File watcher started for: {self.extracted_docs_dir}")
    
    def on_file_changed(self, file_path: str):
        """Handle file change event"""
        self.logger.info(f"File changed: {file_path}, re-indexing...")
        
        try:
            # Re-parse and re-chunk
            structure = self.execute_tool("parse_markdown", file_path=file_path)
            if structure and structure.get('content'):
                chunks = self.execute_tool(
                    "chunk_document",
                    file_path=file_path,
                    chunk_size=500,
                    chunk_overlap=50
                )
                
                # Remove old chunks for this file
                self.chunks = [c for c in self.chunks if c.get('source_file') != file_path]
                
                # Add new chunks
                self.chunks.extend(chunks)
                
                # Notify retrieval agent to update vector store
                if self.framework:
                    self.send_message(
                        "retrieval_agent",
                        {
                            "action": "reindex",
                            "file_path": file_path,
                            "chunks": chunks
                        }
                    )
                    self.logger.info(f"Re-indexed {len(chunks)} chunks for {file_path}")
        except Exception as e:
            self.logger.error(f"Error re-indexing {file_path}: {e}", exc_info=True)
    
    def receive_message(self, from_agent_id: str, message: Any, metadata: Optional[Dict] = None):
        """Handle messages from other agents"""
        if isinstance(message, dict):
            action = message.get('action')
            
            if action == 'process_book':
                # Process book file with book metadata
                file_path = message.get('file_path')
                book_id = message.get('book_id')
                
                if file_path and os.path.exists(file_path):
                    # Get book metadata from BookAgent
                    if self.framework:
                        book_agent = self.framework.get_agent("book_agent")
                        if book_agent:
                            processed_books = book_agent.get_processed_books()
                            if book_id in processed_books:
                                book_data = processed_books[book_id]
                                book_metadata = book_data.get('metadata', {})
                                chapters = book_data.get('chapters', [])
                                
                                # Process with book-specific chunking
                                result = self.process(
                                    {'file_paths': [file_path]},
                                    book_metadata=book_metadata
                                )
                                
                                # Index chunks
                                chunks = result.get('chunks', [])
                                if chunks:
                                    retrieval_agent = self.framework.get_agent("retrieval_agent")
                                    if retrieval_agent:
                                        retrieval_agent.index_chunks(chunks)
                                        self.logger.info(f"Indexed {len(chunks)} chunks for book {book_id}")
    
    def get_chunks(self) -> List[Dict]:
        """Get all chunks"""
        return self.chunks
    
    def _update_progress_file(self, current: int, total: int, processed: int, 
                              errors: int, chunks: int, current_file: str, 
                              elapsed_seconds: float = 0):
        """Update progress tracking file"""
        try:
            progress_pct = (current / total * 100) if total > 0 else 0
            elapsed_min = elapsed_seconds / 60 if elapsed_seconds > 0 else 0
            rate = current / elapsed_seconds if elapsed_seconds > 0 else 0
            eta_seconds = (total - current) / rate if rate > 0 else 0
            eta_min = eta_seconds / 60
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                f.write("Document Processing Progress\n")
                f.write("=" * 60 + "\n")
                f.write(f"Status: {'Processing...' if current < total else 'COMPLETE'}\n")
                f.write(f"Progress: {current}/{total} files ({progress_pct:.1f}%)\n")
                f.write(f"Files processed: {processed}\n")
                f.write(f"Errors/Skipped: {errors}\n")
                f.write(f"Chunks created: {chunks}\n")
                f.write(f"Current file: {current_file}\n")
                if elapsed_seconds > 0:
                    f.write(f"Elapsed time: {elapsed_min:.1f} minutes\n")
                    f.write(f"Processing rate: {rate:.2f} files/second\n")
                    if current < total and rate > 0:
                        f.write(f"Estimated time remaining: {eta_min:.1f} minutes\n")
                f.write("=" * 60 + "\n")
                f.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            # Don't let progress file errors stop processing
            pass
    
    def shutdown(self):
        """Shutdown file watcher"""
        if self.observer:
            self.observer.stop()
            self.observer.join()

