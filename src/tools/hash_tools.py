"""Hash and checksum tools"""

import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

from .security import validate_path

logger = logging.getLogger('hash_tools')


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


def calculate_md5(file_path: str) -> Dict[str, Any]:
    """
    Calculate MD5 hash
    
    Args:
        file_path: Path to file
        
    Returns:
        Dict with success, result (hash hex string), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(file_path)
        hash_md5 = hashlib.md5()
        
        with open(path_obj, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        
        return _success_response(hash_md5.hexdigest())
    except Exception as e:
        logger.error(f"Error calculating MD5 {file_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def calculate_sha1(file_path: str) -> Dict[str, Any]:
    """
    Calculate SHA1 hash
    
    Args:
        file_path: Path to file
        
    Returns:
        Dict with success, result (hash hex string), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(file_path)
        hash_sha1 = hashlib.sha1()
        
        with open(path_obj, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_sha1.update(chunk)
        
        return _success_response(hash_sha1.hexdigest())
    except Exception as e:
        logger.error(f"Error calculating SHA1 {file_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def calculate_sha256(file_path: str) -> Dict[str, Any]:
    """
    Calculate SHA256 hash
    
    Args:
        file_path: Path to file
        
    Returns:
        Dict with success, result (hash hex string), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(file_path)
        hash_sha256 = hashlib.sha256()
        
        with open(path_obj, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_sha256.update(chunk)
        
        return _success_response(hash_sha256.hexdigest())
    except Exception as e:
        logger.error(f"Error calculating SHA256 {file_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def calculate_sha512(file_path: str) -> Dict[str, Any]:
    """
    Calculate SHA512 hash
    
    Args:
        file_path: Path to file
        
    Returns:
        Dict with success, result (hash hex string), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(file_path)
        hash_sha512 = hashlib.sha512()
        
        with open(path_obj, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_sha512.update(chunk)
        
        return _success_response(hash_sha512.hexdigest())
    except Exception as e:
        logger.error(f"Error calculating SHA512 {file_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> Dict[str, Any]:
    """
    Generic hash calculation
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
        
    Returns:
        Dict with success, result (hash hex string), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        algorithm = algorithm.lower()
        if algorithm not in ['md5', 'sha1', 'sha256', 'sha512']:
            return _error_response(f"Unsupported algorithm: {algorithm}", 'ValueError')
        
        path_obj = Path(file_path)
        hash_obj = hashlib.new(algorithm)
        
        with open(path_obj, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        
        return _success_response(hash_obj.hexdigest())
    except Exception as e:
        logger.error(f"Error calculating hash {file_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def verify_file_hash(file_path: str, expected_hash: str, algorithm: str = 'sha256') -> Dict[str, Any]:
    """
    Verify file hash
    
    Args:
        file_path: Path to file
        expected_hash: Expected hash value
        algorithm: Hash algorithm
        
    Returns:
        Dict with success, result (verification result), error, error_type
    """
    try:
        result = calculate_file_hash(file_path, algorithm)
        if not result['success']:
            return result
        
        calculated = result['result']
        matches = calculated.lower() == expected_hash.lower()
        
        return _success_response({
            'matches': matches,
            'calculated': calculated,
            'expected': expected_hash,
        })
    except Exception as e:
        logger.error(f"Error verifying hash {file_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def calculate_string_hash(text: str, algorithm: str = 'sha256') -> Dict[str, Any]:
    """
    Hash string
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm
        
    Returns:
        Dict with success, result (hash hex string), error, error_type
    """
    try:
        algorithm = algorithm.lower()
        if algorithm not in ['md5', 'sha1', 'sha256', 'sha512']:
            return _error_response(f"Unsupported algorithm: {algorithm}", 'ValueError')
        
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(text.encode('utf-8'))
        
        return _success_response(hash_obj.hexdigest())
    except Exception as e:
        logger.error(f"Error calculating string hash: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

