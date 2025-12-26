"""Security utilities for tool operations"""

import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple
import logging

logger = logging.getLogger('security')

# Configuration
ALLOWED_DIRECTORIES: List[str] = [
    # Default to workspace root and common data directories
    str(Path.cwd()),
    str(Path.cwd() / 'data'),
    str(Path.cwd() / 'data' / 'extracted_docs'),
    str(Path.cwd() / 'data' / 'epstein_files'),
    str(Path.cwd() / 'data' / 'wikiepstein_documents'),
]

# Blocked patterns for path traversal and dangerous operations
BLOCKED_PATTERNS: List[str] = [
    r'\.\./',  # Directory traversal
    r'\.\.\\',  # Windows directory traversal
    r'^/',  # Absolute paths (Unix)
    r'^[A-Z]:\\',  # Absolute paths (Windows)
    r'^\s*$',  # Empty paths
]

# Maximum file size limits (in bytes)
MAX_FILE_SIZE: int = 10 * 1024 * 1024 * 1024  # 10 GB default
MAX_ARCHIVE_SIZE: int = 50 * 1024 * 1024 * 1024  # 50 GB for archives

# Allowed file extensions for safety
ALLOWED_EXTENSIONS: Set[str] = set()  # Empty = allow all (can be restricted)

# Blocked file extensions
BLOCKED_EXTENSIONS: Set[str] = {
    '.exe', '.bat', '.cmd', '.com', '.scr', '.vbs', '.js', '.jar', '.app', '.deb', '.rpm'
}


def validate_path(path: str, operation: str = 'read', allow_absolute: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate a file path for security
    
    Args:
        path: Path to validate
        operation: Operation type ('read', 'write', 'delete')
        allow_absolute: Whether to allow absolute paths
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path or not isinstance(path, str):
        return False, "Path must be a non-empty string"
    
    # Check for blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, path):
            if not allow_absolute or not (pattern == r'^/' or pattern == r'^[A-Z]:\\'):
                return False, f"Path contains blocked pattern: {pattern}"
    
    # Normalize path
    try:
        normalized = Path(path).resolve()
    except Exception as e:
        return False, f"Invalid path format: {str(e)}"
    
    # Check if absolute paths are allowed
    if not allow_absolute and normalized.is_absolute():
        # Check if it's within allowed directories
        is_allowed = False
        for allowed_dir in ALLOWED_DIRECTORIES:
            try:
                allowed_path = Path(allowed_dir).resolve()
                if str(normalized).startswith(str(allowed_path)):
                    is_allowed = True
                    break
            except Exception:
                continue
        
        if not is_allowed:
            return False, f"Path outside allowed directories: {path}"
    
    # Check file extension if it's a file
    if normalized.is_file() or '.' in normalized.name:
        ext = normalized.suffix.lower()
        if ext in BLOCKED_EXTENSIONS:
            return False, f"Blocked file extension: {ext}"
    
    # Check if path exists for read operations
    if operation == 'read' and not normalized.exists():
        return False, f"Path does not exist: {path}"
    
    # Check permissions
    if operation == 'read' and normalized.exists():
        if not os.access(normalized, os.R_OK):
            return False, f"No read permission: {path}"
    
    if operation == 'write':
        parent = normalized.parent
        if parent.exists() and not os.access(parent, os.W_OK):
            return False, f"No write permission: {parent}"
    
    return True, None


def sanitize_path(path: str) -> str:
    """
    Sanitize a file path
    
    Args:
        path: Path to sanitize
        
    Returns:
        Sanitized path
    """
    if not path:
        return ""
    
    # Remove null bytes
    path = path.replace('\x00', '')
    
    # Normalize path separators
    path = path.replace('\\', os.sep).replace('/', os.sep)
    
    # Remove leading/trailing whitespace
    path = path.strip()
    
    # Remove multiple separators
    while os.sep + os.sep in path:
        path = path.replace(os.sep + os.sep, os.sep)
    
    return path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to remove dangerous characters
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return ""
    
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Remove dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing dots and spaces (Windows issue)
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    return filename


def check_file_size(file_path: str, max_size: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """
    Check if file size is within limits
    
    Args:
        file_path: Path to file
        max_size: Maximum size in bytes (defaults to MAX_FILE_SIZE)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if max_size is None:
        max_size = MAX_FILE_SIZE
    
    try:
        size = os.path.getsize(file_path)
        if size > max_size:
            return False, f"File size {size} exceeds maximum {max_size} bytes"
        return True, None
    except OSError as e:
        return False, f"Cannot check file size: {str(e)}"


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a URL for security
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    # Check for dangerous protocols
    dangerous_protocols = ['file://', 'javascript:', 'data:', 'vbscript:']
    url_lower = url.lower()
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return False, f"Dangerous protocol: {protocol}"
    
    # Check for valid URL format
    if not (url.startswith('http://') or url.startswith('https://')):
        return False, "URL must start with http:// or https://"
    
    return True, None


def validate_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a shell command for security
    
    Args:
        command: Command to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not command or not isinstance(command, str):
        return False, "Command must be a non-empty string"
    
    # Block dangerous commands
    dangerous_commands = ['rm -rf', 'del /f', 'format', 'mkfs', 'dd if=', 'shutdown', 'reboot']
    command_lower = command.lower()
    for dangerous in dangerous_commands:
        if dangerous in command_lower:
            return False, f"Dangerous command detected: {dangerous}"
    
    # Block command chaining
    if '&&' in command or '||' in command or ';' in command or '|' in command:
        return False, "Command chaining not allowed"
    
    return True, None


def add_allowed_directory(directory: str) -> bool:
    """
    Add a directory to the allowed list
    
    Args:
        directory: Directory path to add
        
    Returns:
        True if added successfully
    """
    try:
        abs_path = str(Path(directory).resolve())
        if abs_path not in ALLOWED_DIRECTORIES:
            ALLOWED_DIRECTORIES.append(abs_path)
            logger.info(f"Added allowed directory: {abs_path}")
        return True
    except Exception as e:
        logger.error(f"Error adding allowed directory: {e}")
        return False


def get_allowed_directories() -> List[str]:
    """Get list of allowed directories"""
    return ALLOWED_DIRECTORIES.copy()

