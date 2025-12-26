"""Text processing tools"""

import re
import logging
from typing import Dict, List, Optional, Any
from unicodedata import normalize, combining

# Try to import chardet
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False

logger = logging.getLogger('text_processing_tools')

# Try to import optional dependencies
try:
    import phonenumbers
    PHONENUMBERS_AVAILABLE = True
except ImportError:
    PHONENUMBERS_AVAILABLE = False

try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False


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


def detect_encoding(file_path: str) -> Dict[str, Any]:
    """
    Detect file encoding
    
    Args:
        file_path: Path to file
        
    Returns:
        Dict with success, result (encoding info), error, error_type
    """
    try:
        from .security import validate_path
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        if not CHARDET_AVAILABLE:
            return _error_response("chardet not available. Install with: pip install chardet", 'ImportError')
        
        from pathlib import Path
        path_obj = Path(file_path)
        
        with open(path_obj, 'rb') as f:
            raw_data = f.read()
        
        detected = chardet.detect(raw_data)
        
        result = {
            'encoding': detected.get('encoding', 'unknown'),
            'confidence': detected.get('confidence', 0.0),
        }
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error detecting encoding {file_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def convert_encoding(text: str, from_encoding: str, to_encoding: str) -> Dict[str, Any]:
    """
    Convert encoding
    
    Args:
        text: Text to convert
        from_encoding: Source encoding
        to_encoding: Target encoding
        
    Returns:
        Dict with success, result (converted text), error, error_type
    """
    try:
        # Decode from source encoding, then encode to target
        decoded = text.encode(from_encoding) if isinstance(text, str) else text
        converted = decoded.decode(to_encoding) if isinstance(decoded, bytes) else decoded.encode(to_encoding).decode(to_encoding)
        return _success_response(converted)
    except Exception as e:
        logger.error(f"Error converting encoding: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def normalize_text(text: str, form: str = 'NFC') -> Dict[str, Any]:
    """
    Unicode normalization
    
    Args:
        text: Text to normalize
        form: Normalization form ('NFC', 'NFD', 'NFKC', 'NFKD')
        
    Returns:
        Dict with success, result (normalized text), error, error_type
    """
    try:
        normalized = normalize(form, text)
        return _success_response(normalized)
    except Exception as e:
        logger.error(f"Error normalizing text: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def remove_accents(text: str) -> Dict[str, Any]:
    """
    Remove accents/diacritics
    
    Args:
        text: Text to process
        
    Returns:
        Dict with success, result (text without accents), error, error_type
    """
    try:
        # Decompose, remove combining characters, recompose
        nfd = normalize('NFD', text)
        removed = ''.join(c for c in nfd if not combining(c))
        result = normalize('NFC', removed)
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error removing accents: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def slugify(text: str) -> Dict[str, Any]:
    """
    Create URL-friendly slug
    
    Args:
        text: Text to slugify
        
    Returns:
        Dict with success, result (slug), error, error_type
    """
    try:
        # Normalize and lowercase
        text = normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = text.lower()
        # Replace spaces and special chars with hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        text = text.strip('-')
        return _success_response(text)
    except Exception as e:
        logger.error(f"Error slugifying text: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def word_count(text: str) -> Dict[str, Any]:
    """
    Count words
    
    Args:
        text: Text to count
        
    Returns:
        Dict with success, result (word count), error, error_type
    """
    try:
        words = text.split()
        count = len(words)
        return _success_response(count)
    except Exception as e:
        logger.error(f"Error counting words: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def character_count(text: str) -> Dict[str, Any]:
    """
    Count characters
    
    Args:
        text: Text to count
        
    Returns:
        Dict with success, result (character count), error, error_type
    """
    try:
        count = len(text)
        return _success_response(count)
    except Exception as e:
        logger.error(f"Error counting characters: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def line_count(text: str) -> Dict[str, Any]:
    """
    Count lines
    
    Args:
        text: Text to count
        
    Returns:
        Dict with success, result (line count), error, error_type
    """
    try:
        lines = text.splitlines()
        count = len(lines)
        return _success_response(count)
    except Exception as e:
        logger.error(f"Error counting lines: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def extract_emails(text: str) -> Dict[str, Any]:
    """
    Extract email addresses
    
    Args:
        text: Text to search
        
    Returns:
        Dict with success, result (list of emails), error, error_type
    """
    try:
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text)
        return _success_response(emails)
    except Exception as e:
        logger.error(f"Error extracting emails: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def extract_urls(text: str) -> Dict[str, Any]:
    """
    Extract URLs
    
    Args:
        text: Text to search
        
    Returns:
        Dict with success, result (list of URLs), error, error_type
    """
    try:
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(pattern, text)
        return _success_response(urls)
    except Exception as e:
        logger.error(f"Error extracting URLs: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def extract_phone_numbers(text: str) -> Dict[str, Any]:
    """
    Extract phone numbers
    
    Args:
        text: Text to search
        
    Returns:
        Dict with success, result (list of phone numbers), error, error_type
    """
    if not PHONENUMBERS_AVAILABLE:
        # Fallback to regex
        try:
            pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            phones = re.findall(pattern, text)
            return _success_response([p[0] if isinstance(p, tuple) else p for p in phones])
        except Exception as e:
            return _error_response(str(e), type(e).__name__)
    
    try:
        phones = []
        for match in phonenumbers.PhoneNumberMatcher(text, None):
            phones.append(phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164))
        return _success_response(phones)
    except Exception as e:
        logger.error(f"Error extracting phone numbers: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def extract_dates(text: str) -> Dict[str, Any]:
    """
    Extract dates
    
    Args:
        text: Text to search
        
    Returns:
        Dict with success, result (list of dates), error, error_type
    """
    if not DATEUTIL_AVAILABLE:
        return _error_response("dateutil not available. Install with: pip install python-dateutil", 'ImportError')
    
    try:
        dates = []
        # Try to find date-like patterns
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
            r'[A-Za-z]+\s+\d{1,2},?\s+\d{4}',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    parsed = date_parser.parse(match.group())
                    dates.append({
                        'text': match.group(),
                        'parsed': parsed.isoformat(),
                    })
                except:
                    pass
        
        return _success_response(dates)
    except Exception as e:
        logger.error(f"Error extracting dates: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def find_replace(text: str, find: str, replace: str, count: Optional[int] = None) -> Dict[str, Any]:
    """
    Find and replace
    
    Args:
        text: Text to process
        find: Text to find
        replace: Replacement text
        count: Maximum replacements (None = all)
        
    Returns:
        Dict with success, result (modified text), error, error_type
    """
    try:
        if count is not None:
            result = text.replace(find, replace, count)
        else:
            result = text.replace(find, replace)
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error in find_replace: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def regex_search(text: str, pattern: str, flags: int = 0) -> Dict[str, Any]:
    """
    Regex search
    
    Args:
        text: Text to search
        pattern: Regex pattern
        flags: Regex flags
        
    Returns:
        Dict with success, result (list of matches), error, error_type
    """
    try:
        matches = re.findall(pattern, text, flags)
        return _success_response(matches)
    except re.error as e:
        logger.error(f"Regex error: {e}", exc_info=True)
        return _error_response(f"Invalid regex: {str(e)}", 'RegexError')
    except Exception as e:
        logger.error(f"Error in regex_search: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def regex_replace(text: str, pattern: str, replacement: str, flags: int = 0) -> Dict[str, Any]:
    """
    Regex replace
    
    Args:
        text: Text to process
        pattern: Regex pattern
        replacement: Replacement string
        flags: Regex flags
        
    Returns:
        Dict with success, result (modified text), error, error_type
    """
    try:
        result = re.sub(pattern, replacement, text, flags=flags)
        return _success_response(result)
    except re.error as e:
        logger.error(f"Regex error: {e}", exc_info=True)
        return _error_response(f"Invalid regex: {str(e)}", 'RegexError')
    except Exception as e:
        logger.error(f"Error in regex_replace: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

