"""Math and statistics tools"""

import math
import statistics
import logging
from typing import Dict, List, Any

logger = logging.getLogger('math_tools')


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


def calculate_statistics(numbers: List[float]) -> Dict[str, Any]:
    """
    Calculate statistics (mean, median, std, etc.)
    
    Args:
        numbers: List of numbers
        
    Returns:
        Dict with success, result (statistics dict), error, error_type
    """
    try:
        if not numbers:
            return _error_response("Empty list provided", 'ValueError')
        
        result = {
            'count': len(numbers),
            'mean': statistics.mean(numbers),
            'median': statistics.median(numbers),
            'stdev': statistics.stdev(numbers) if len(numbers) > 1 else 0,
            'min': min(numbers),
            'max': max(numbers),
            'sum': sum(numbers),
        }
        
        # Add mode if available
        try:
            result['mode'] = statistics.mode(numbers)
        except statistics.StatisticsError:
            result['mode'] = None
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def round_number(number: float, decimals: int = 2) -> Dict[str, Any]:
    """
    Round number
    
    Args:
        number: Number to round
        decimals: Number of decimal places
        
    Returns:
        Dict with success, result (rounded number), error, error_type
    """
    try:
        rounded = round(number, decimals)
        return _success_response(rounded)
    except Exception as e:
        logger.error(f"Error rounding number: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def format_number(number: float, decimals: int = 2, thousands_sep: str = ',') -> Dict[str, Any]:
    """
    Format number
    
    Args:
        number: Number to format
        decimals: Number of decimal places
        thousands_sep: Thousands separator
        
    Returns:
        Dict with success, result (formatted string), error, error_type
    """
    try:
        formatted = f"{number:,.{decimals}f}".replace(',', thousands_sep)
        return _success_response(formatted)
    except Exception as e:
        logger.error(f"Error formatting number: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def calculate_percentage(part: float, total: float) -> Dict[str, Any]:
    """
    Calculate percentage
    
    Args:
        part: Part value
        total: Total value
        
    Returns:
        Dict with success, result (percentage), error, error_type
    """
    try:
        if total == 0:
            return _error_response("Cannot calculate percentage: total is zero", 'ValueError')
        
        percentage = (part / total) * 100
        return _success_response(percentage)
    except Exception as e:
        logger.error(f"Error calculating percentage: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def convert_units(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
    """
    Unit conversion (basic conversions)
    
    Args:
        value: Value to convert
        from_unit: Source unit
        to_unit: Target unit
        
    Returns:
        Dict with success, result (converted value), error, error_type
    """
    try:
        # Basic conversion factors
        conversions = {
            # Length
            'm_to_ft': 3.28084,
            'ft_to_m': 0.3048,
            'km_to_mi': 0.621371,
            'mi_to_km': 1.60934,
            # Weight
            'kg_to_lb': 2.20462,
            'lb_to_kg': 0.453592,
            # Temperature (special case)
            'c_to_f': lambda x: (x * 9/5) + 32,
            'f_to_c': lambda x: (x - 32) * 5/9,
        }
        
        key = f"{from_unit}_to_{to_unit}"
        if key in conversions:
            factor = conversions[key]
            if callable(factor):
                result = factor(value)
            else:
                result = value * factor
            return _success_response(result)
        
        return _error_response(f"Unsupported conversion: {from_unit} to {to_unit}", 'ValueError')
    except Exception as e:
        logger.error(f"Error converting units: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def evaluate_expression(expression: str) -> Dict[str, Any]:
    """
    Safely evaluate math expression
    
    Args:
        expression: Math expression string
        
    Returns:
        Dict with success, result (evaluated result), error, error_type
    """
    try:
        # Only allow safe math operations
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return _error_response("Expression contains invalid characters", 'ValueError')
        
        # Use eval with restricted globals
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error evaluating expression: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

