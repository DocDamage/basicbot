"""Compression/decompression tools"""

import gzip
import bz2
import logging
import shutil
from pathlib import Path
from typing import Dict, Any

from .security import validate_path

logger = logging.getLogger('compression_tools')


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


def compress_file(file_path: str, output_path: str, algorithm: str = 'gzip') -> Dict[str, Any]:
    """
    Compress file
    
    Args:
        file_path: Path to file to compress
        output_path: Output compressed file path
        algorithm: Compression algorithm ('gzip', 'bzip2')
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(file_path)
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        if algorithm == 'gzip':
            with open(path_obj, 'rb') as f_in:
                with gzip.open(output_obj, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif algorithm == 'bzip2':
            with open(path_obj, 'rb') as f_in:
                with bz2.open(output_obj, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            return _error_response(f"Unsupported algorithm: {algorithm}", 'ValueError')
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error compressing file {file_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def decompress_file(compressed_path: str, output_path: str, algorithm: str = 'gzip') -> Dict[str, Any]:
    """
    Decompress file
    
    Args:
        compressed_path: Path to compressed file
        output_path: Output decompressed file path
        algorithm: Compression algorithm ('gzip', 'bzip2')
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(compressed_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        compressed_obj = Path(compressed_path)
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        if algorithm == 'gzip':
            with gzip.open(compressed_obj, 'rb') as f_in:
                with open(output_obj, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        elif algorithm == 'bzip2':
            with bz2.open(compressed_obj, 'rb') as f_in:
                with open(output_obj, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            return _error_response(f"Unsupported algorithm: {algorithm}", 'ValueError')
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error decompressing file {compressed_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def compress_directory(dir_path: str, output_path: str, algorithm: str = 'gzip') -> Dict[str, Any]:
    """
    Compress directory
    
    Args:
        dir_path: Path to directory to compress
        output_path: Output compressed file path
        algorithm: Compression algorithm ('gzip', 'bzip2')
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(dir_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        dir_obj = Path(dir_path)
        if not dir_obj.is_dir():
            return _error_response(f"Path is not a directory: {dir_path}", 'NotADirectoryError')
        
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a tar archive first, then compress
        import tarfile
        
        # Determine tar format based on algorithm
        if algorithm == 'gzip':
            tar_format = 'w:gz'
        elif algorithm == 'bzip2':
            tar_format = 'w:bz2'
        else:
            return _error_response(f"Unsupported algorithm: {algorithm}", 'ValueError')
        
        with tarfile.open(output_obj, tar_format) as tar:
            tar.add(dir_obj, arcname=dir_obj.name)
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error compressing directory {dir_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def decompress_directory(compressed_path: str, output_dir: str, algorithm: str = 'gzip') -> Dict[str, Any]:
    """
    Decompress directory
    
    Args:
        compressed_path: Path to compressed file
        output_dir: Output directory
        algorithm: Compression algorithm ('gzip', 'bzip2')
        
    Returns:
        Dict with success, result (output directory), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(compressed_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_dir, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        compressed_obj = Path(compressed_path)
        output_obj = Path(output_dir)
        output_obj.mkdir(parents=True, exist_ok=True)
        
        # Determine tar format based on algorithm
        import tarfile
        
        if algorithm == 'gzip':
            tar_format = 'r:gz'
        elif algorithm == 'bzip2':
            tar_format = 'r:bz2'
        else:
            return _error_response(f"Unsupported algorithm: {algorithm}", 'ValueError')
        
        with tarfile.open(compressed_obj, tar_format) as tar:
            tar.extractall(output_obj)
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error decompressing directory {compressed_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

