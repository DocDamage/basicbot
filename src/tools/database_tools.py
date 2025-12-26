"""Database operations tools"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .security import validate_path

logger = logging.getLogger('database_tools')


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


def sqlite_connect(db_path: str) -> Dict[str, Any]:
    """
    Connect to SQLite database
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Dict with success, result (connection info), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(db_path, operation='read', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(db_path)
        exists = path_obj.exists()
        
        return _success_response({
            'path': str(path_obj),
            'exists': exists,
        })
    except Exception as e:
        logger.error(f"Error connecting to SQLite {db_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def sqlite_query(db_path: str, query: str, parameters: Optional[List] = None) -> Dict[str, Any]:
    """
    Execute SQL query (SELECT)
    
    Args:
        db_path: Path to SQLite database
        query: SQL query
        parameters: Query parameters
        
    Returns:
        Dict with success, result (query results), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(db_path, operation='read', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(db_path)
        if not path_obj.exists():
            return _error_response(f"Database does not exist: {db_path}", 'FileNotFoundError')
        
        conn = sqlite3.connect(str(path_obj))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if parameters:
            cursor.execute(query, parameters)
        else:
            cursor.execute(query)
        
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        
        conn.close()
        
        return _success_response(result)
    except sqlite3.Error as e:
        logger.error(f"SQLite error in query: {e}", exc_info=True)
        return _error_response(str(e), 'SQLiteError')
    except Exception as e:
        logger.error(f"Error executing SQL query: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def sqlite_execute(db_path: str, query: str, parameters: Optional[List] = None) -> Dict[str, Any]:
    """
    Execute SQL (INSERT/UPDATE/DELETE)
    
    Args:
        db_path: Path to SQLite database
        query: SQL statement
        parameters: Query parameters
        
    Returns:
        Dict with success, result (execution info), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(db_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(db_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(path_obj))
        cursor = conn.cursor()
        
        if parameters:
            cursor.execute(query, parameters)
        else:
            cursor.execute(query)
        
        conn.commit()
        rowcount = cursor.rowcount
        lastrowid = cursor.lastrowid
        
        conn.close()
        
        return _success_response({
            'rowcount': rowcount,
            'lastrowid': lastrowid,
        })
    except sqlite3.Error as e:
        logger.error(f"SQLite error in execute: {e}", exc_info=True)
        return _error_response(str(e), 'SQLiteError')
    except Exception as e:
        logger.error(f"Error executing SQL: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def sqlite_create_table(db_path: str, table_name: str, schema: str) -> Dict[str, Any]:
    """
    Create table
    
    Args:
        db_path: Path to SQLite database
        table_name: Table name
        schema: Table schema (column definitions)
        
    Returns:
        Dict with success, result (None), error, error_type
    """
    try:
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})"
        return sqlite_execute(db_path, query)
    except Exception as e:
        logger.error(f"Error creating table: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def sqlite_list_tables(db_path: str) -> Dict[str, Any]:
    """
    List tables
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Dict with success, result (list of table names), error, error_type
    """
    try:
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        result = sqlite_query(db_path, query)
        if result['success']:
            tables = [row['name'] for row in result['result']]
            return _success_response(tables)
        return result
    except Exception as e:
        logger.error(f"Error listing tables: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def sqlite_get_schema(db_path: str, table_name: str) -> Dict[str, Any]:
    """
    Get table schema
    
    Args:
        db_path: Path to SQLite database
        table_name: Table name
        
    Returns:
        Dict with success, result (schema info), error, error_type
    """
    try:
        query = f"PRAGMA table_info({table_name})"
        result = sqlite_query(db_path, query)
        if result['success']:
            return _success_response(result['result'])
        return result
    except Exception as e:
        logger.error(f"Error getting schema: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

