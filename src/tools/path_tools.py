"""Path operations tools"""

import os
import logging
from pathlib import Path
from typing import Dict, Any

from .security import validate_path, sanitize_path, sanitize_filename as _sanitize_filename

logger = logging.getLogger('path_tools')


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


def join_paths(*paths: str) -> Dict[str, Any]:
    """
    Join path components
    
    Args:
        *paths: Path components
        
    Returns:
        Dict with success, result (joined path), error, error_type
    """
    try:
        joined = os.path.join(*paths)
        return _success_response(joined)
    except Exception as e:
        logger.error(f"Error joining paths: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def normalize_path(path: str) -> Dict[str, Any]:
    """
    Normalize path
    
    Args:
        path: Path to normalize
        
    Returns:
        Dict with success, result (normalized path), error, error_type
    """
    try:
        normalized = os.path.normpath(path)
        return _success_response(normalized)
    except Exception as e:
        logger.error(f"Error normalizing path {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_absolute_path(path: str) -> Dict[str, Any]:
    """
    Get absolute path
    
    Args:
        path: Path to convert
        
    Returns:
        Dict with success, result (absolute path), error, error_type
    """
    try:
        abs_path = os.path.abspath(path)
        return _success_response(abs_path)
    except Exception as e:
        logger.error(f"Error getting absolute path {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_relative_path(path: str, start: str = None) -> Dict[str, Any]:
    """
    Get relative path
    
    Args:
        path: Path to convert
        start: Start directory (default: current directory)
        
    Returns:
        Dict with success, result (relative path), error, error_type
    """
    try:
        if start is None:
            start = os.getcwd()
        
        rel_path = os.path.relpath(path, start)
        return _success_response(rel_path)
    except Exception as e:
        logger.error(f"Error getting relative path {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_file_extension(path: str) -> Dict[str, Any]:
    """
    Get file extension
    
    Args:
        path: File path
        
    Returns:
        Dict with success, result (extension), error, error_type
    """
    try:
        ext = Path(path).suffix
        return _success_response(ext)
    except Exception as e:
        logger.error(f"Error getting file extension {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_file_name(path: str, with_extension: bool = True) -> Dict[str, Any]:
    """
    Get filename
    
    Args:
        path: File path
        with_extension: Include extension
        
    Returns:
        Dict with success, result (filename), error, error_type
    """
    try:
        path_obj = Path(path)
        if with_extension:
            name = path_obj.name
        else:
            name = path_obj.stem
        return _success_response(name)
    except Exception as e:
        logger.error(f"Error getting filename {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_directory_name(path: str) -> Dict[str, Any]:
    """
    Get directory name
    
    Args:
        path: Path
        
    Returns:
        Dict with success, result (directory name), error, error_type
    """
    try:
        dir_name = os.path.dirname(path)
        return _success_response(dir_name)
    except Exception as e:
        logger.error(f"Error getting directory name {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_parent_directory(path: str) -> Dict[str, Any]:
    """
    Get parent directory
    
    Args:
        path: Path
        
    Returns:
        Dict with success, result (parent directory), error, error_type
    """
    try:
        parent = Path(path).parent
        return _success_response(str(parent))
    except Exception as e:
        logger.error(f"Error getting parent directory {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def path_exists(path: str) -> Dict[str, Any]:
    """
    Check if path exists
    
    Args:
        path: Path to check
        
    Returns:
        Dict with success, result (bool), error, error_type
    """
    try:
        exists = os.path.exists(path)
        return _success_response(exists)
    except Exception as e:
        logger.error(f"Error checking path existence {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def is_file(path: str) -> Dict[str, Any]:
    """
    Check if path is file
    
    Args:
        path: Path to check
        
    Returns:
        Dict with success, result (bool), error, error_type
    """
    try:
        is_file_result = os.path.isfile(path)
        return _success_response(is_file_result)
    except Exception as e:
        logger.error(f"Error checking if file {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def is_directory(path: str) -> Dict[str, Any]:
    """
    Check if path is directory
    
    Args:
        path: Path to check
        
    Returns:
        Dict with success, result (bool), error, error_type
    """
    try:
        is_dir = os.path.isdir(path)
        return _success_response(is_dir)
    except Exception as e:
        logger.error(f"Error checking if directory {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def is_absolute_path(path: str) -> Dict[str, Any]:
    """
    Check if absolute path
    
    Args:
        path: Path to check
        
    Returns:
        Dict with success, result (bool), error, error_type
    """
    try:
        is_abs = os.path.isabs(path)
        return _success_response(is_abs)
    except Exception as e:
        logger.error(f"Error checking if absolute path {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def sanitize_filename(filename: str) -> Dict[str, Any]:
    """
    Sanitize filename
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Dict with success, result (sanitized filename), error, error_type
    """
    try:
        sanitized = _sanitize_filename(filename)
        return _success_response(sanitized)
    except Exception as e:
        logger.error(f"Error sanitizing filename {filename}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

