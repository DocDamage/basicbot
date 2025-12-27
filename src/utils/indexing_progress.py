"""Progress tracking for background indexing"""

import json
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class IndexingProgress:
    """Track indexing progress for GUI display"""
    
    def __init__(self, progress_file: Optional[str] = None):
        if progress_file is None:
            log_dir = os.getenv("LOG_DIR", "./data/logs")
            os.makedirs(log_dir, exist_ok=True)
            progress_file = os.path.join(log_dir, "indexing_progress.json")
        
        self.progress_file = progress_file
        self._initialize_progress()
    
    def _initialize_progress(self):
        """Initialize progress file with default values"""
        default = {
            "status": "idle",  # idle, indexing, complete, error
            "total_files": 0,
            "processed_files": 0,
            "total_chunks": 0,
            "indexed_chunks": 0,
            "current_file": "",
            "errors": 0,
            "start_time": None,
            "last_update": None,
            "message": "Ready to index"
        }
        
        if not os.path.exists(self.progress_file):
            self._write_progress(default)
    
    def _write_progress(self, progress: Dict):
        """Write progress to file"""
        progress["last_update"] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            print(f"Error writing progress: {e}")
    
    def _read_progress(self) -> Dict:
        """Read progress from file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error reading progress: {e}")
        
        return self._initialize_progress()
    
    def start(self, total_files: int, total_chunks: int = 0):
        """Start indexing"""
        progress = {
            "status": "indexing",
            "total_files": total_files,
            "processed_files": 0,
            "total_chunks": total_chunks,
            "indexed_chunks": 0,
            "current_file": "",
            "errors": 0,
            "start_time": datetime.now().isoformat(),
            "last_update": None,
            "message": f"Starting indexing of {total_files} files..."
        }
        self._write_progress(progress)
    
    def update_file(self, processed: int, current_file: str = "", message: str = ""):
        """Update file processing progress"""
        progress = self._read_progress()
        progress["processed_files"] = processed
        progress["current_file"] = current_file
        if message:
            progress["message"] = message
        else:
            progress["message"] = f"Processing file {processed}/{progress['total_files']}: {Path(current_file).name if current_file else 'N/A'}"
        self._write_progress(progress)
    
    def update_chunks(self, indexed: int, total: Optional[int] = None):
        """Update chunk indexing progress"""
        progress = self._read_progress()
        progress["indexed_chunks"] = indexed
        if total is not None:
            progress["total_chunks"] = total
        progress["message"] = f"Indexed {indexed}/{progress['total_chunks']} chunks"
        self._write_progress(progress)
    
    def add_error(self, error_message: str = ""):
        """Increment error count"""
        progress = self._read_progress()
        progress["errors"] = progress.get("errors", 0) + 1
        if error_message:
            progress["message"] = f"Error: {error_message}"
        self._write_progress(progress)
    
    def complete(self, message: str = "Indexing complete"):
        """Mark indexing as complete"""
        progress = self._read_progress()
        progress["status"] = "complete"
        progress["message"] = message
        self._write_progress(progress)
    
    def error(self, error_message: str):
        """Mark indexing as error"""
        progress = self._read_progress()
        progress["status"] = "error"
        progress["message"] = f"Error: {error_message}"
        self._write_progress(progress)
    
    def get_progress(self) -> Dict:
        """Get current progress"""
        return self._read_progress()
    
    def get_percentage(self) -> float:
        """Get completion percentage (0-100)"""
        progress = self._read_progress()
        if progress["status"] == "complete":
            return 100.0
        if progress["status"] != "indexing":
            return 0.0
        
        # Calculate based on files and chunks
        file_progress = 0.0
        chunk_progress = 0.0
        
        if progress["total_files"] > 0:
            file_progress = (progress["processed_files"] / progress["total_files"]) * 50  # Files are 50% of work
        
        if progress["total_chunks"] > 0:
            chunk_progress = (progress["indexed_chunks"] / progress["total_chunks"]) * 50  # Chunks are 50% of work
        
        return min(100.0, file_progress + chunk_progress)
    
    def is_indexing(self) -> bool:
        """Check if indexing is in progress"""
        progress = self._read_progress()
        return progress["status"] == "indexing"

