"""Archive operations tools"""

import zipfile
import tarfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .security import validate_path, check_file_size, sanitize_filename

logger = logging.getLogger('archive_tools')

# Try to import optional dependencies
try:
    import rarfile
    RARFILE_AVAILABLE = True
except ImportError:
    RARFILE_AVAILABLE = False

try:
    import py7zr
    PY7ZR_AVAILABLE = True
except ImportError:
    PY7ZR_AVAILABLE = False


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


def zip_create(archive_path: str, files: List[str], compression: str = 'zip') -> Dict[str, Any]:
    """
    Create ZIP archive
    
    Args:
        archive_path: Path to create archive
        files: List of file paths to include
        compression: Compression method ('zip', 'zip_deflated', 'zip_bzip2', 'zip_lzma')
        
    Returns:
        Dict with success, result (archive path), error, error_type
    """
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        archive_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Map compression string to zipfile constant
        compression_map = {
            'zip': zipfile.ZIP_STORED,
            'zip_deflated': zipfile.ZIP_DEFLATED,
            'zip_bzip2': zipfile.ZIP_BZIP2,
            'zip_lzma': zipfile.ZIP_LZMA,
        }
        comp_method = compression_map.get(compression, zipfile.ZIP_DEFLATED)
        
        # Create archive
        with zipfile.ZipFile(archive_obj, 'w', compression=comp_method) as zipf:
            for file_path in files:
                # Validate each file
                is_valid, error_msg = validate_path(file_path, operation='read')
                if not is_valid:
                    logger.warning(f"Skipping invalid file: {file_path} - {error_msg}")
                    continue
                
                file_obj = Path(file_path)
                if file_obj.exists() and file_obj.is_file():
                    zipf.write(file_obj, file_obj.name)
        
        return _success_response(str(archive_obj))
    except Exception as e:
        logger.error(f"Error creating ZIP archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def zip_extract(archive_path: str, extract_to: str, password: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract ZIP archive
    
    Args:
        archive_path: Path to ZIP archive
        extract_to: Directory to extract to
        password: Optional password for encrypted archives
        
    Returns:
        Dict with success, result (list of extracted files), error, error_type
    """
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        # Validate extract directory
        is_valid, error_msg = validate_path(extract_to, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        extract_obj = Path(extract_to)
        extract_obj.mkdir(parents=True, exist_ok=True)
        
        extracted_files = []
        
        with zipfile.ZipFile(archive_obj, 'r') as zipf:
            if password:
                zipf.setpassword(password.encode())
            
            for member in zipf.namelist():
                # Security: Check for path traversal
                if '..' in member or member.startswith('/'):
                    logger.warning(f"Skipping potentially dangerous path: {member}")
                    continue
                
                zipf.extract(member, extract_obj)
                extracted_path = extract_obj / member
                if extracted_path.exists():
                    extracted_files.append(str(extracted_path))
        
        return _success_response(extracted_files)
    except Exception as e:
        logger.error(f"Error extracting ZIP archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def zip_list(archive_path: str) -> Dict[str, Any]:
    """
    List ZIP contents
    
    Args:
        archive_path: Path to ZIP archive
        
    Returns:
        Dict with success, result (list of file info), error, error_type
    """
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        
        file_list = []
        with zipfile.ZipFile(archive_obj, 'r') as zipf:
            for info in zipf.infolist():
                file_list.append({
                    'filename': info.filename,
                    'size': info.file_size,
                    'compressed_size': info.compress_size,
                    'date_time': info.date_time,
                })
        
        return _success_response(file_list)
    except Exception as e:
        logger.error(f"Error listing ZIP archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def zip_add_file(archive_path: str, file_path: str, arcname: Optional[str] = None) -> Dict[str, Any]:
    """
    Add file to ZIP
    
    Args:
        archive_path: Path to ZIP archive
        file_path: File to add
        arcname: Archive name (default: filename)
        
    Returns:
        Dict with success, result (archive path), error, error_type
    """
    try:
        # Validate paths
        is_valid, error_msg = validate_path(archive_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        file_obj = Path(file_path)
        
        if not file_obj.exists():
            return _error_response(f"File does not exist: {file_path}", 'FileNotFoundError')
        
        with zipfile.ZipFile(archive_obj, 'a') as zipf:
            zipf.write(file_obj, arcname or file_obj.name)
        
        return _success_response(str(archive_obj))
    except Exception as e:
        logger.error(f"Error adding file to ZIP {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def zip_remove_file(archive_path: str, file_to_remove: str) -> Dict[str, Any]:
    """
    Remove file from ZIP
    
    Args:
        archive_path: Path to ZIP archive
        file_to_remove: File to remove from archive
        
    Returns:
        Dict with success, result (archive path), error, error_type
    """
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        
        # Read existing archive
        temp_archive = archive_obj.with_suffix('.tmp')
        with zipfile.ZipFile(archive_obj, 'r') as zip_read:
            with zipfile.ZipFile(temp_archive, 'w') as zip_write:
                for item in zip_read.infolist():
                    if item.filename != file_to_remove:
                        data = zip_read.read(item.filename)
                        zip_write.writestr(item, data)
        
        # Replace original with temp
        temp_archive.replace(archive_obj)
        
        return _success_response(str(archive_obj))
    except Exception as e:
        logger.error(f"Error removing file from ZIP {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def tar_create(archive_path: str, files: List[str], format: str = 'tar.gz') -> Dict[str, Any]:
    """
    Create TAR/TAR.GZ/TAR.BZ2 archive
    
    Args:
        archive_path: Path to create archive
        files: List of file paths to include
        format: Archive format ('tar', 'tar.gz', 'tar.bz2', 'tar.xz')
        
    Returns:
        Dict with success, result (archive path), error, error_type
    """
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        archive_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # Map format to mode
        mode_map = {
            'tar': 'w',
            'tar.gz': 'w:gz',
            'tar.bz2': 'w:bz2',
            'tar.xz': 'w:xz',
        }
        mode = mode_map.get(format, 'w:gz')
        
        # Create archive
        with tarfile.open(archive_obj, mode) as tar:
            for file_path in files:
                # Validate each file
                is_valid, error_msg = validate_path(file_path, operation='read')
                if not is_valid:
                    logger.warning(f"Skipping invalid file: {file_path} - {error_msg}")
                    continue
                
                file_obj = Path(file_path)
                if file_obj.exists() and file_obj.is_file():
                    tar.add(file_obj, arcname=file_obj.name)
        
        return _success_response(str(archive_obj))
    except Exception as e:
        logger.error(f"Error creating TAR archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def tar_extract(archive_path: str, extract_to: str) -> Dict[str, Any]:
    """
    Extract TAR archives
    
    Args:
        archive_path: Path to TAR archive
        extract_to: Directory to extract to
        
    Returns:
        Dict with success, result (list of extracted files), error, error_type
    """
    try:
        # Validate paths
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(extract_to, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        extract_obj = Path(extract_to)
        extract_obj.mkdir(parents=True, exist_ok=True)
        
        extracted_files = []
        
        with tarfile.open(archive_obj, 'r:*') as tar:
            for member in tar.getmembers():
                # Security: Check for path traversal
                if '..' in member.name or member.name.startswith('/'):
                    logger.warning(f"Skipping potentially dangerous path: {member.name}")
                    continue
                
                tar.extract(member, extract_obj)
                extracted_path = extract_obj / member.name
                if extracted_path.exists():
                    extracted_files.append(str(extracted_path))
        
        return _success_response(extracted_files)
    except Exception as e:
        logger.error(f"Error extracting TAR archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def tar_list(archive_path: str) -> Dict[str, Any]:
    """
    List TAR contents
    
    Args:
        archive_path: Path to TAR archive
        
    Returns:
        Dict with success, result (list of file info), error, error_type
    """
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        
        file_list = []
        with tarfile.open(archive_obj, 'r:*') as tar:
            for member in tar.getmembers():
                file_list.append({
                    'name': member.name,
                    'size': member.size,
                    'mtime': member.mtime,
                    'type': member.type,
                })
        
        return _success_response(file_list)
    except Exception as e:
        logger.error(f"Error listing TAR archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def rar_extract(archive_path: str, extract_to: str, password: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract RAR archive (requires unrar)
    
    Args:
        archive_path: Path to RAR archive
        extract_to: Directory to extract to
        password: Optional password for encrypted archives
        
    Returns:
        Dict with success, result (list of extracted files), error, error_type
    """
    if not RARFILE_AVAILABLE:
        return _error_response("rarfile library not available. Install with: pip install rarfile", 'ImportError')
    
    try:
        # Validate paths
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(extract_to, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        extract_obj = Path(extract_to)
        extract_obj.mkdir(parents=True, exist_ok=True)
        
        extracted_files = []
        
        with rarfile.RarFile(archive_obj) as rar:
            if password:
                rar.setpassword(password)
            
            for member in rar.namelist():
                # Security: Check for path traversal
                if '..' in member or member.startswith('/'):
                    logger.warning(f"Skipping potentially dangerous path: {member}")
                    continue
                
                rar.extract(member, extract_obj)
                extracted_path = extract_obj / member
                if extracted_path.exists():
                    extracted_files.append(str(extracted_path))
        
        return _success_response(extracted_files)
    except Exception as e:
        logger.error(f"Error extracting RAR archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def rar_list(archive_path: str) -> Dict[str, Any]:
    """
    List RAR contents
    
    Args:
        archive_path: Path to RAR archive
        
    Returns:
        Dict with success, result (list of file info), error, error_type
    """
    if not RARFILE_AVAILABLE:
        return _error_response("rarfile library not available. Install with: pip install rarfile", 'ImportError')
    
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        
        file_list = []
        with rarfile.RarFile(archive_obj) as rar:
            for info in rar.infolist():
                file_list.append({
                    'filename': info.filename,
                    'file_size': info.file_size,
                    'compress_size': info.compress_size,
                    'date_time': info.date_time,
                })
        
        return _success_response(file_list)
    except Exception as e:
        logger.error(f"Error listing RAR archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def sevenzip_extract(archive_path: str, extract_to: str, password: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract 7Z archive
    
    Args:
        archive_path: Path to 7Z archive
        extract_to: Directory to extract to
        password: Optional password for encrypted archives
        
    Returns:
        Dict with success, result (list of extracted files), error, error_type
    """
    if not PY7ZR_AVAILABLE:
        return _error_response("py7zr library not available. Install with: pip install py7zr", 'ImportError')
    
    try:
        # Validate paths
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(extract_to, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        extract_obj = Path(extract_to)
        extract_obj.mkdir(parents=True, exist_ok=True)
        
        extracted_files = []
        
        with py7zr.SevenZipFile(archive_obj, mode='r', password=password) as archive:
            archive.extractall(path=extract_obj)
            
            # List extracted files
            for file_path in extract_obj.rglob('*'):
                if file_path.is_file():
                    extracted_files.append(str(file_path))
        
        return _success_response(extracted_files)
    except Exception as e:
        logger.error(f"Error extracting 7Z archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def sevenzip_list(archive_path: str) -> Dict[str, Any]:
    """
    List 7Z contents
    
    Args:
        archive_path: Path to 7Z archive
        
    Returns:
        Dict with success, result (list of file info), error, error_type
    """
    if not PY7ZR_AVAILABLE:
        return _error_response("py7zr library not available. Install with: pip install py7zr", 'ImportError')
    
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        
        file_list = []
        with py7zr.SevenZipFile(archive_obj, mode='r') as archive:
            for info in archive.getnames():
                file_list.append({
                    'filename': info,
                })
        
        return _success_response(file_list)
    except Exception as e:
        logger.error(f"Error listing 7Z archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def archive_test(archive_path: str) -> Dict[str, Any]:
    """
    Test archive integrity
    
    Args:
        archive_path: Path to archive
        
    Returns:
        Dict with success, result (test result), error, error_type
    """
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        suffix = archive_obj.suffix.lower()
        
        # Test based on archive type
        if suffix == '.zip':
            with zipfile.ZipFile(archive_obj, 'r') as zipf:
                result = zipf.testzip()
                if result is None:
                    return _success_response({'valid': True, 'message': 'Archive is valid'})
                else:
                    return _success_response({'valid': False, 'message': f'Corrupted file: {result}'})
        
        elif suffix in ['.tar', '.gz', '.bz2', '.xz']:
            with tarfile.open(archive_obj, 'r:*') as tar:
                tar.getmembers()  # This will raise if corrupted
                return _success_response({'valid': True, 'message': 'Archive is valid'})
        
        elif suffix == '.rar':
            if not RARFILE_AVAILABLE:
                return _error_response("rarfile library not available", 'ImportError')
            with rarfile.RarFile(archive_obj) as rar:
                rar.testrar()
                return _success_response({'valid': True, 'message': 'Archive is valid'})
        
        elif suffix == '.7z':
            if not PY7ZR_AVAILABLE:
                return _error_response("py7zr library not available", 'ImportError')
            with py7zr.SevenZipFile(archive_obj, mode='r') as archive:
                archive.getnames()  # This will raise if corrupted
                return _success_response({'valid': True, 'message': 'Archive is valid'})
        
        else:
            return _error_response(f"Unsupported archive format: {suffix}", 'UnsupportedFormatError')
    
    except Exception as e:
        logger.error(f"Error testing archive {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def archive_info(archive_path: str) -> Dict[str, Any]:
    """
    Get archive metadata
    
    Args:
        archive_path: Path to archive
        
    Returns:
        Dict with success, result (archive info), error, error_type
    """
    try:
        # Validate archive path
        is_valid, error_msg = validate_path(archive_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        archive_obj = Path(archive_path)
        suffix = archive_obj.suffix.lower()
        
        info = {
            'path': str(archive_obj),
            'size': archive_obj.stat().st_size,
            'format': suffix,
        }
        
        # Get file count and total size
        if suffix == '.zip':
            with zipfile.ZipFile(archive_obj, 'r') as zipf:
                file_count = len(zipf.namelist())
                total_size = sum(info.file_size for info in zipf.infolist())
                info['file_count'] = file_count
                info['total_size'] = total_size
        
        elif suffix in ['.tar', '.gz', '.bz2', '.xz']:
            with tarfile.open(archive_obj, 'r:*') as tar:
                members = tar.getmembers()
                file_count = len(members)
                total_size = sum(m.size for m in members)
                info['file_count'] = file_count
                info['total_size'] = total_size
        
        elif suffix == '.rar':
            if RARFILE_AVAILABLE:
                with rarfile.RarFile(archive_obj) as rar:
                    members = rar.infolist()
                    file_count = len(members)
                    total_size = sum(m.file_size for m in members)
                    info['file_count'] = file_count
                    info['total_size'] = total_size
        
        elif suffix == '.7z':
            if PY7ZR_AVAILABLE:
                with py7zr.SevenZipFile(archive_obj, mode='r') as archive:
                    names = archive.getnames()
                    info['file_count'] = len(names)
        
        return _success_response(info)
    except Exception as e:
        logger.error(f"Error getting archive info {archive_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

