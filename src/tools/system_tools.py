"""System operations tools"""

import os
import sys
import platform
import subprocess
import logging
import shutil
from pathlib import Path
from typing import Dict, Optional, Any

# Try to import psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .security import validate_path, validate_command

logger = logging.getLogger('system_tools')


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


def run_command(command: str, shell: bool = False, timeout: Optional[int] = None, cwd: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute shell command
    
    Args:
        command: Command to execute
        shell: Use shell execution
        timeout: Command timeout in seconds
        cwd: Working directory
        
    Returns:
        Dict with success, result (command output), error, error_type
    """
    try:
        # Validate command
        is_valid, error_msg = validate_command(command)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        # Validate working directory if provided
        if cwd:
            is_valid, error_msg = validate_path(cwd, operation='read')
            if not is_valid:
                return _error_response(error_msg, 'ValidationError')
        
        result = subprocess.run(
            command,
            shell=shell,
            timeout=timeout,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        output = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0,
        }
        
        return _success_response(output)
    except subprocess.TimeoutExpired:
        return _error_response(f"Command timed out after {timeout} seconds", 'TimeoutError')
    except Exception as e:
        logger.error(f"Error running command {command}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_environment_variable(name: str, default: Optional[str] = None) -> Dict[str, Any]:
    """
    Get environment variable
    
    Args:
        name: Variable name
        default: Default value if not found
        
    Returns:
        Dict with success, result (variable value), error, error_type
    """
    try:
        value = os.environ.get(name, default)
        return _success_response(value)
    except Exception as e:
        logger.error(f"Error getting environment variable {name}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def set_environment_variable(name: str, value: str) -> Dict[str, Any]:
    """
    Set environment variable
    
    Args:
        name: Variable name
        value: Variable value
        
    Returns:
        Dict with success, result (None), error, error_type
    """
    try:
        os.environ[name] = value
        return _success_response(None)
    except Exception as e:
        logger.error(f"Error setting environment variable {name}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def list_environment_variables() -> Dict[str, Any]:
    """
    List all environment variables
    
    Returns:
        Dict with success, result (dict of env vars), error, error_type
    """
    try:
        env_vars = dict(os.environ)
        return _success_response(env_vars)
    except Exception as e:
        logger.error(f"Error listing environment variables: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_system_info() -> Dict[str, Any]:
    """
    Get system information (OS, CPU, memory)
    
    Returns:
        Dict with success, result (system info), error, error_type
    """
    try:
        info = {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'cpu_count': os.cpu_count(),
        }
        
        # Add memory info if psutil available
        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            info['memory'] = {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'percent': mem.percent,
            }
        
        return _success_response(info)
    except Exception as e:
        logger.error(f"Error getting system info: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_disk_usage(path: str) -> Dict[str, Any]:
    """
    Get disk usage
    
    Args:
        path: Path to check
        
    Returns:
        Dict with success, result (disk usage), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        usage = shutil.disk_usage(path_obj)
        
        result = {
            'total': usage.total,
            'used': usage.used,
            'free': usage.free,
            'percent_used': (usage.used / usage.total) * 100,
        }
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error getting disk usage {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_process_info(pid: Optional[int] = None) -> Dict[str, Any]:
    """
    Get process information
    
    Args:
        pid: Process ID (default: current process)
        
    Returns:
        Dict with success, result (process info), error, error_type
    """
    try:
        if pid is None:
            pid = os.getpid()
        
        if not PSUTIL_AVAILABLE:
            return _error_response("psutil not available. Install with: pip install psutil", 'ImportError')
        
        try:
            proc = psutil.Process(pid)
            info = {
                'pid': proc.pid,
                'name': proc.name(),
                'status': proc.status(),
                'cpu_percent': proc.cpu_percent(),
                'memory_info': proc.memory_info()._asdict(),
                'create_time': proc.create_time(),
            }
            return _success_response(info)
        except psutil.NoSuchProcess:
            return _error_response(f"Process {pid} not found", 'ProcessNotFoundError')
    except Exception as e:
        logger.error(f"Error getting process info {pid}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def kill_process(pid: int, force: bool = False) -> Dict[str, Any]:
    """
    Kill process
    
    Args:
        pid: Process ID
        force: Force kill
        
    Returns:
        Dict with success, result (None), error, error_type
    """
    try:
        if not PSUTIL_AVAILABLE:
            return _error_response("psutil not available. Install with: pip install psutil", 'ImportError')
        
        try:
            proc = psutil.Process(pid)
            if force:
                proc.kill()
            else:
                proc.terminate()
            return _success_response(None)
        except psutil.NoSuchProcess:
            return _error_response(f"Process {pid} not found", 'ProcessNotFoundError')
    except Exception as e:
        logger.error(f"Error killing process {pid}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_current_directory() -> Dict[str, Any]:
    """
    Get current working directory
    
    Returns:
        Dict with success, result (directory path), error, error_type
    """
    try:
        cwd = os.getcwd()
        return _success_response(cwd)
    except Exception as e:
        logger.error(f"Error getting current directory: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def change_directory(path: str) -> Dict[str, Any]:
    """
    Change directory
    
    Args:
        path: Directory path
        
    Returns:
        Dict with success, result (new directory), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(path)
        if not path_obj.is_dir():
            return _error_response(f"Path is not a directory: {path}", 'NotADirectoryError')
        
        os.chdir(path_obj)
        return _success_response(str(os.getcwd()))
    except Exception as e:
        logger.error(f"Error changing directory to {path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_path_separator() -> Dict[str, Any]:
    """
    Get OS path separator
    
    Returns:
        Dict with success, result (separator), error, error_type
    """
    try:
        return _success_response(os.sep)
    except Exception as e:
        logger.error(f"Error getting path separator: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

