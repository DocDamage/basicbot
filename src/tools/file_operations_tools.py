"""File operations tools"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

from .security import validate_path, sanitize_path, check_file_size, sanitize_filename

logger = logging.getLogger('file_operations_tools')


def _error_response(error: str, error_type: str) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        'success': False,
        'result': None,
        'error': error,
        'error_type': error_type
    }


def _success_response(result: Any) -> Dict[str, Any]:
    """Create standardized success response"""
    return {
        'success': True,
        'result': result,
        'error': None,
        'error_type': None
    }


def read_file(path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
    """
    Read file with encoding detection
    
    Args:
        path: Path to file
        encoding: File encoding (default: utf-8)
        
    Returns:
        Dict with success, result (file content), error, error_type
    """
    try:
        # Validate path
        is_valid, error_msg = validate_path(path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        
        # Check file size
        is_valid_size, size_error = check_file_size(str(path_obj))
        if not is_valid_size:
            return _error_response(size_error, 'FileSizeError')
        
        # Try to read with specified encoding
        try:
            with open(path_obj, 'r', encoding=encoding) as f:
                content = f.read()
            return _success_response(content)
        except UnicodeDecodeError:
            # Try to detect encoding
            import chardet
            try:
                with open(path_obj, 'rb') as f:
                    raw_data = f.read()
                detected = chardet.detect(raw_data)
                detected_encoding = detected.get('encoding', 'utf-8')
                
                with open(path_obj, 'r', encoding=detected_encoding) as f:
                    content = f.read()
                return _success_response(content)
            except Exception as e:
                return _error_response(f"Encoding error: {str(e)}", 'EncodingError')
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def write_file(path: str, content: str, encoding: str = 'utf-8', create_dirs: bool = True) -> Dict[str, Any]:
    """
    Write file
    
    Args:
        path: Path to file
        content: Content to write
        encoding: File encoding (default: utf-8)
        create_dirs: Create parent directories if they don't exist
        
    Returns:
        Dict with success, result (file path), error, error_type
    """
    try:
        # Validate path
        is_valid, error_msg = validate_path(path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        
        # Create parent directories if needed
        if create_dirs:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(path_obj, 'w', encoding=encoding) as f:
            f.write(content)
        
        return _success_response(str(path_obj))
    except Exception as e:
        logger.error(f"Error writing file {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def copy_file(source: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
    """
    Copy file with validation
    
    Args:
        source: Source file path
        destination: Destination file path
        overwrite: Overwrite if destination exists
        
    Returns:
        Dict with success, result (destination path), error, error_type
    """
    try:
        # Validate source
        is_valid, error_msg = validate_path(source, operation='read')
        if not is_valid:
            return _error_response(f"Source: {error_msg}", 'ValidationError')
        
        # Validate destination
        is_valid, error_msg = validate_path(destination, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(f"Destination: {error_msg}", 'ValidationError')
        
        source_obj = Path(source)
        dest_obj = Path(destination)
        
        # Check if source exists
        if not source_obj.exists():
            return _error_response(f"Source file does not exist: {source}", 'FileNotFoundError')
        
        # Check if destination exists
        if dest_obj.exists() and not overwrite:
            return _error_response(f"Destination file exists: {destination}", 'FileExistsError')
        
        # Create parent directories
        dest_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(source_obj, dest_obj)
        
        return _success_response(str(dest_obj))
    except Exception as e:
        logger.error(f"Error copying file {source} to {destination}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def move_file(source: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
    """
    Move/rename file
    
    Args:
        source: Source file path
        destination: Destination file path
        overwrite: Overwrite if destination exists
        
    Returns:
        Dict with success, result (destination path), error, error_type
    """
    try:
        # Validate source
        is_valid, error_msg = validate_path(source, operation='read')
        if not is_valid:
            return _error_response(f"Source: {error_msg}", 'ValidationError')
        
        # Validate destination
        is_valid, error_msg = validate_path(destination, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(f"Destination: {error_msg}", 'ValidationError')
        
        source_obj = Path(source)
        dest_obj = Path(destination)
        
        # Check if source exists
        if not source_obj.exists():
            return _error_response(f"Source file does not exist: {source}", 'FileNotFoundError')
        
        # Check if destination exists
        if dest_obj.exists() and not overwrite:
            return _error_response(f"Destination file exists: {destination}", 'FileExistsError')
        
        # Create parent directories
        dest_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(str(source_obj), str(dest_obj))
        
        return _success_response(str(dest_obj))
    except Exception as e:
        logger.error(f"Error moving file {source} to {destination}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def delete_file(path: str, safe: bool = True) -> Dict[str, Any]:
    """
    Delete file with safety checks
    
    Args:
        path: Path to file
        safe: If True, only delete files (not directories)
        
    Returns:
        Dict with success, result (deleted path), error, error_type
    """
    try:
        # Validate path
        is_valid, error_msg = validate_path(path, operation='delete')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        
        # Check if exists
        if not path_obj.exists():
            return _error_response(f"File does not exist: {path}", 'FileNotFoundError')
        
        # Safety check
        if safe and path_obj.is_dir():
            return _error_response(f"Path is a directory, use delete_directory: {path}", 'IsADirectoryError')
        
        # Delete file
        path_obj.unlink()
        
        return _success_response(str(path_obj))
    except Exception as e:
        logger.error(f"Error deleting file {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def file_exists(path: str) -> Dict[str, Any]:
    """
    Check if file exists
    
    Args:
        path: Path to check
        
    Returns:
        Dict with success, result (bool), error, error_type
    """
    try:
        path_obj = Path(path)
        exists = path_obj.exists() and path_obj.is_file()
        return _success_response(exists)
    except Exception as e:
        logger.error(f"Error checking file existence {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_file_size(path: str) -> Dict[str, Any]:
    """
    Get file size
    
    Args:
        path: Path to file
        
    Returns:
        Dict with success, result (size in bytes), error, error_type
    """
    try:
        # Validate path
        is_valid, error_msg = validate_path(path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        
        if not path_obj.exists():
            return _error_response(f"File does not exist: {path}", 'FileNotFoundError')
        
        if not path_obj.is_file():
            return _error_response(f"Path is not a file: {path}", 'IsADirectoryError')
        
        size = path_obj.stat().st_size
        return _success_response(size)
    except Exception as e:
        logger.error(f"Error getting file size {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_file_info(path: str) -> Dict[str, Any]:
    """
    Get file metadata (size, modified, permissions)
    
    Args:
        path: Path to file
        
    Returns:
        Dict with success, result (file info dict), error, error_type
    """
    try:
        # Validate path
        is_valid, error_msg = validate_path(path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        
        if not path_obj.exists():
            return _error_response(f"File does not exist: {path}", 'FileNotFoundError')
        
        stat = path_obj.stat()
        info = {
            'path': str(path_obj),
            'name': path_obj.name,
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'is_file': path_obj.is_file(),
            'is_dir': path_obj.is_dir(),
            'extension': path_obj.suffix,
        }
        
        return _success_response(info)
    except Exception as e:
        logger.error(f"Error getting file info {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def list_files(directory: str, pattern: str = '*', recursive: bool = False) -> Dict[str, Any]:
    """
    List files with glob
    
    Args:
        directory: Directory to list
        pattern: Glob pattern (default: '*')
        recursive: Recursive search
        
    Returns:
        Dict with success, result (list of file paths), error, error_type
    """
    try:
        # Validate path
        is_valid, error_msg = validate_path(directory, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        dir_obj = Path(directory)
        
        if not dir_obj.exists():
            return _error_response(f"Directory does not exist: {directory}", 'FileNotFoundError')
        
        if not dir_obj.is_dir():
            return _error_response(f"Path is not a directory: {directory}", 'NotADirectoryError')
        
        # List files
        if recursive:
            files = [str(f) for f in dir_obj.rglob(pattern) if f.is_file()]
        else:
            files = [str(f) for f in dir_obj.glob(pattern) if f.is_file()]
        
        return _success_response(files)
    except Exception as e:
        logger.error(f"Error listing files in {directory}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def search_files(directory: str, pattern: str, recursive: bool = True) -> Dict[str, Any]:
    """
    Search files by pattern
    
    Args:
        directory: Directory to search
        pattern: Search pattern (glob)
        recursive: Recursive search
        
    Returns:
        Dict with success, result (list of file paths), error, error_type
    """
    return list_files(directory, pattern, recursive)


def create_directory(path: str, parents: bool = True, exist_ok: bool = True) -> Dict[str, Any]:
    """
    Create directory
    
    Args:
        path: Directory path
        parents: Create parent directories
        exist_ok: Don't error if directory exists
        
    Returns:
        Dict with success, result (directory path), error, error_type
    """
    try:
        # Validate path
        is_valid, error_msg = validate_path(path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        path_obj.mkdir(parents=parents, exist_ok=exist_ok)
        
        return _success_response(str(path_obj))
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def delete_directory(path: str, recursive: bool = False) -> Dict[str, Any]:
    """
    Delete directory
    
    Args:
        path: Directory path
        recursive: Recursive delete
        
    Returns:
        Dict with success, result (deleted path), error, error_type
    """
    try:
        # Validate path
        is_valid, error_msg = validate_path(path, operation='delete')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        
        if not path_obj.exists():
            return _error_response(f"Directory does not exist: {path}", 'FileNotFoundError')
        
        if not path_obj.is_dir():
            return _error_response(f"Path is not a directory: {path}", 'NotADirectoryError')
        
        if recursive:
            shutil.rmtree(path_obj)
        else:
            path_obj.rmdir()
        
        return _success_response(str(path_obj))
    except Exception as e:
        logger.error(f"Error deleting directory {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_directory_size(path: str) -> Dict[str, Any]:
    """
    Calculate directory size
    
    Args:
        path: Directory path
        
    Returns:
        Dict with success, result (size in bytes), error, error_type
    """
    try:
        # Validate path
        is_valid, error_msg = validate_path(path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        
        if not path_obj.exists():
            return _error_response(f"Directory does not exist: {path}", 'FileNotFoundError')
        
        if not path_obj.is_dir():
            return _error_response(f"Path is not a directory: {path}", 'NotADirectoryError')
        
        total_size = sum(f.stat().st_size for f in path_obj.rglob('*') if f.is_file())
        
        return _success_response(total_size)
    except Exception as e:
        logger.error(f"Error calculating directory size {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def compare_files(file1: str, file2: str) -> Dict[str, Any]:
    """
    Compare two files (content/hash)
    
    Args:
        file1: First file path
        file2: Second file path
        
    Returns:
        Dict with success, result (comparison dict), error, error_type
    """
    try:
        # Validate both paths
        is_valid, error_msg = validate_path(file1, operation='read')
        if not is_valid:
            return _error_response(f"File1: {error_msg}", 'ValidationError')
        
        is_valid, error_msg = validate_path(file2, operation='read')
        if not is_valid:
            return _error_response(f"File2: {error_msg}", 'ValidationError')
        
        file1_obj = Path(file1)
        file2_obj = Path(file2)
        
        if not file1_obj.exists():
            return _error_response(f"File1 does not exist: {file1}", 'FileNotFoundError')
        
        if not file2_obj.exists():
            return _error_response(f"File2 does not exist: {file2}", 'FileNotFoundError')
        
        # Compare sizes
        size1 = file1_obj.stat().st_size
        size2 = file2_obj.stat().st_size
        same_size = size1 == size2
        
        # Compare hashes if same size
        same_content = False
        if same_size:
            hash1 = hashlib.sha256(file1_obj.read_bytes()).hexdigest()
            hash2 = hashlib.sha256(file2_obj.read_bytes()).hexdigest()
            same_content = hash1 == hash2
        
        result = {
            'same_size': same_size,
            'same_content': same_content,
            'size1': size1,
            'size2': size2,
        }
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error comparing files {file1} and {file2}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

