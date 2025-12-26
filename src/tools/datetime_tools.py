"""Date/time operations tools"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

logger = logging.getLogger('datetime_tools')

# Try to import dateutil
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


def get_current_datetime(format: Optional[str] = None) -> Dict[str, Any]:
    """
    Get current datetime
    
    Args:
        format: Optional format string (default: ISO format)
        
    Returns:
        Dict with success, result (datetime string), error, error_type
    """
    try:
        now = datetime.now()
        if format:
            result = now.strftime(format)
        else:
            result = now.isoformat()
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error getting current datetime: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def parse_datetime(datetime_string: str, format: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse datetime string
    
    Args:
        datetime_string: Datetime string to parse
        format: Optional format string
        
    Returns:
        Dict with success, result (datetime ISO string), error, error_type
    """
    try:
        if format:
            dt = datetime.strptime(datetime_string, format)
        elif DATEUTIL_AVAILABLE:
            dt = date_parser.parse(datetime_string)
        else:
            # Try common formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
            ]
            dt = None
            for fmt in formats:
                try:
                    dt = datetime.strptime(datetime_string, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                return _error_response("Could not parse datetime string", 'ValueError')
        
        return _success_response(dt.isoformat())
    except Exception as e:
        logger.error(f"Error parsing datetime {datetime_string}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def format_datetime(datetime_obj: str, format: str = '%Y-%m-%d %H:%M:%S') -> Dict[str, Any]:
    """
    Format datetime
    
    Args:
        datetime_obj: Datetime ISO string
        format: Format string
        
    Returns:
        Dict with success, result (formatted string), error, error_type
    """
    try:
        dt = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
        formatted = dt.strftime(format)
        return _success_response(formatted)
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def add_time_delta(datetime_obj: str, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> Dict[str, Any]:
    """
    Add time delta
    
    Args:
        datetime_obj: Datetime ISO string
        days: Days to add
        hours: Hours to add
        minutes: Minutes to add
        seconds: Seconds to add
        
    Returns:
        Dict with success, result (new datetime ISO string), error, error_type
    """
    try:
        dt = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        new_dt = dt + delta
        return _success_response(new_dt.isoformat())
    except Exception as e:
        logger.error(f"Error adding time delta: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def subtract_time_delta(datetime_obj: str, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> Dict[str, Any]:
    """
    Subtract time delta
    
    Args:
        datetime_obj: Datetime ISO string
        days: Days to subtract
        hours: Hours to subtract
        minutes: Minutes to subtract
        seconds: Seconds to subtract
        
    Returns:
        Dict with success, result (new datetime ISO string), error, error_type
    """
    try:
        dt = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        new_dt = dt - delta
        return _success_response(new_dt.isoformat())
    except Exception as e:
        logger.error(f"Error subtracting time delta: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def datetime_diff(datetime1: str, datetime2: str) -> Dict[str, Any]:
    """
    Calculate difference between two datetimes
    
    Args:
        datetime1: First datetime ISO string
        datetime2: Second datetime ISO string
        
    Returns:
        Dict with success, result (difference dict), error, error_type
    """
    try:
        dt1 = datetime.fromisoformat(datetime1.replace('Z', '+00:00'))
        dt2 = datetime.fromisoformat(datetime2.replace('Z', '+00:00'))
        delta = dt2 - dt1
        
        result = {
            'total_seconds': delta.total_seconds(),
            'days': delta.days,
            'seconds': delta.seconds,
            'microseconds': delta.microseconds,
        }
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error calculating datetime diff: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_timestamp() -> Dict[str, Any]:
    """
    Get Unix timestamp
    
    Returns:
        Dict with success, result (timestamp), error, error_type
    """
    try:
        timestamp = datetime.now().timestamp()
        return _success_response(timestamp)
    except Exception as e:
        logger.error(f"Error getting timestamp: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def timestamp_to_datetime(timestamp: float) -> Dict[str, Any]:
    """
    Convert timestamp to datetime
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Dict with success, result (datetime ISO string), error, error_type
    """
    try:
        dt = datetime.fromtimestamp(timestamp)
        return _success_response(dt.isoformat())
    except Exception as e:
        logger.error(f"Error converting timestamp to datetime: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def datetime_to_timestamp(datetime_obj: str) -> Dict[str, Any]:
    """
    Convert datetime to timestamp
    
    Args:
        datetime_obj: Datetime ISO string
        
    Returns:
        Dict with success, result (timestamp), error, error_type
    """
    try:
        dt = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
        timestamp = dt.timestamp()
        return _success_response(timestamp)
    except Exception as e:
        logger.error(f"Error converting datetime to timestamp: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

