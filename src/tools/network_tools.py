"""Network operations tools"""

import requests
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from urllib.parse import urlparse

from .security import validate_path, validate_url

logger = logging.getLogger('network_tools')


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


def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30, verify_ssl: bool = True) -> Dict[str, Any]:
    """
    HTTP GET request
    
    Args:
        url: URL to request
        headers: Optional headers dict
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates
        
    Returns:
        Dict with success, result (response dict), error, error_type
    """
    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        response = requests.get(url, headers=headers, timeout=timeout, verify=verify_ssl)
        response.raise_for_status()
        
        result = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'content_type': response.headers.get('Content-Type', ''),
            'url': response.url,
        }
        
        return _success_response(result)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in HTTP GET {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)
    except Exception as e:
        logger.error(f"Unexpected error in HTTP GET {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def http_post(url: str, data: Optional[Any] = None, json: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    HTTP POST request
    
    Args:
        url: URL to request
        data: Form data
        json: JSON data
        headers: Optional headers dict
        timeout: Request timeout in seconds
        
    Returns:
        Dict with success, result (response dict), error, error_type
    """
    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        response = requests.post(url, data=data, json=json, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        result = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'content_type': response.headers.get('Content-Type', ''),
            'url': response.url,
        }
        
        return _success_response(result)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in HTTP POST {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)
    except Exception as e:
        logger.error(f"Unexpected error in HTTP POST {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def http_put(url: str, data: Optional[Any] = None, json: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    HTTP PUT request
    
    Args:
        url: URL to request
        data: Form data
        json: JSON data
        headers: Optional headers dict
        timeout: Request timeout in seconds
        
    Returns:
        Dict with success, result (response dict), error, error_type
    """
    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        response = requests.put(url, data=data, json=json, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        result = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'content_type': response.headers.get('Content-Type', ''),
            'url': response.url,
        }
        
        return _success_response(result)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in HTTP PUT {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)
    except Exception as e:
        logger.error(f"Unexpected error in HTTP PUT {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def http_delete(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> Dict[str, Any]:
    """
    HTTP DELETE request
    
    Args:
        url: URL to request
        headers: Optional headers dict
        timeout: Request timeout in seconds
        
    Returns:
        Dict with success, result (response dict), error, error_type
    """
    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        response = requests.delete(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        result = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content': response.text,
            'content_type': response.headers.get('Content-Type', ''),
            'url': response.url,
        }
        
        return _success_response(result)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in HTTP DELETE {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)
    except Exception as e:
        logger.error(f"Unexpected error in HTTP DELETE {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def download_file(url: str, destination: str, chunk_size: int = 8192, verify_ssl: bool = True) -> Dict[str, Any]:
    """
    Download file from URL
    
    Args:
        url: URL to download from
        destination: Destination file path
        chunk_size: Chunk size for streaming
        verify_ssl: Verify SSL certificates
        
    Returns:
        Dict with success, result (file path), error, error_type
    """
    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        # Validate destination
        is_valid, error_msg = validate_path(destination, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        dest_obj = Path(destination)
        dest_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Download file
        response = requests.get(url, stream=True, verify=verify_ssl)
        response.raise_for_status()
        
        with open(dest_obj, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        
        return _success_response(str(dest_obj))
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading file {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)
    except Exception as e:
        logger.error(f"Unexpected error downloading file {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def upload_file(url: str, file_path: str, field_name: str = 'file', headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Upload file to URL
    
    Args:
        url: URL to upload to
        file_path: Path to file to upload
        field_name: Form field name
        headers: Optional headers dict
        
    Returns:
        Dict with success, result (response dict), error, error_type
    """
    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        # Validate file path
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        file_obj = Path(file_path)
        if not file_obj.exists():
            return _error_response(f"File does not exist: {file_path}", 'FileNotFoundError')
        
        # Upload file
        with open(file_obj, 'rb') as f:
            files = {field_name: f}
            response = requests.post(url, files=files, headers=headers)
            response.raise_for_status()
        
        result = {
            'status_code': response.status_code,
            'content': response.text,
            'headers': dict(response.headers),
        }
        
        return _success_response(result)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error uploading file {file_path} to {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)
    except Exception as e:
        logger.error(f"Unexpected error uploading file {file_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def check_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Check if URL is accessible
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
        
    Returns:
        Dict with success, result (accessibility info), error, error_type
    """
    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        
        result = {
            'accessible': response.status_code < 400,
            'status_code': response.status_code,
            'url': response.url,
        }
        
        return _success_response(result)
    except requests.exceptions.RequestException as e:
        return _success_response({
            'accessible': False,
            'error': str(e),
        })
    except Exception as e:
        logger.error(f"Unexpected error checking URL {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_url_info(url: str) -> Dict[str, Any]:
    """
    Get URL metadata (headers, content-type, etc.)
    
    Args:
        url: URL to get info for
        
    Returns:
        Dict with success, result (URL info), error, error_type
    """
    try:
        # Validate URL
        is_valid, error_msg = validate_url(url)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        response = requests.head(url, allow_redirects=True)
        
        parsed = urlparse(url)
        result = {
            'url': url,
            'final_url': response.url,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content_type': response.headers.get('Content-Type', ''),
            'content_length': response.headers.get('Content-Length', ''),
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
        }
        
        return _success_response(result)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting URL info {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)
    except Exception as e:
        logger.error(f"Unexpected error getting URL info {url}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

