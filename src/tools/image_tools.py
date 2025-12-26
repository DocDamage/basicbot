"""Image operations tools"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any, Tuple

from .security import validate_path

logger = logging.getLogger('image_tools')

# Try to import Pillow
try:
    from PIL import Image, ExifTags
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


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


def resize_image(image_path: str, output_path: str, width: int, height: int, maintain_aspect: bool = True) -> Dict[str, Any]:
    """
    Resize image
    
    Args:
        image_path: Path to input image
        output_path: Path to output image
        width: Target width
        height: Target height
        maintain_aspect: Maintain aspect ratio
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    if not PILLOW_AVAILABLE:
        return _error_response("Pillow not available. Install with: pip install Pillow", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(path_obj)
        
        if maintain_aspect:
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
        else:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        img.save(output_obj)
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error resizing image {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def convert_image_format(image_path: str, output_path: str, format: str) -> Dict[str, Any]:
    """
    Convert image format (PNG/JPG/etc)
    
    Args:
        image_path: Path to input image
        output_path: Path to output image
        format: Target format (PNG, JPEG, etc.)
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    if not PILLOW_AVAILABLE:
        return _error_response("Pillow not available. Install with: pip install Pillow", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(path_obj)
        img.save(output_obj, format=format.upper())
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error converting image {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def read_image(image_path: str, return_base64: bool = False) -> Dict[str, Any]:
    """
    Read/open image file
    
    Args:
        image_path: Path to image file
        return_base64: If True, return image as base64 string
        
    Returns:
        Dict with success, result (image info or base64), error, error_type
    """
    if not PILLOW_AVAILABLE:
        return _error_response("Pillow not available. Install with: pip install Pillow", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        
        if not path_obj.exists():
            return _error_response(f"Image file does not exist: {image_path}", 'FileNotFoundError')
        
        img = Image.open(path_obj)
        
        result = {
            'path': str(path_obj),
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.width,
            'height': img.height,
            'file_size': path_obj.stat().st_size,
        }
        
        if return_base64:
            import base64
            import io
            buffer = io.BytesIO()
            img.save(buffer, format=img.format or 'PNG')
            result['base64'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
            result['mime_type'] = f"image/{img.format.lower() if img.format else 'png'}"
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error reading image {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_image_info(image_path: str) -> Dict[str, Any]:
    """
    Get image metadata (dimensions, format, size)
    
    Args:
        image_path: Path to image
        
    Returns:
        Dict with success, result (image info), error, error_type
    """
    if not PILLOW_AVAILABLE:
        return _error_response("Pillow not available. Install with: pip install Pillow", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        img = Image.open(path_obj)
        
        info = {
            'path': str(path_obj),
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
            'width': img.width,
            'height': img.height,
            'file_size': path_obj.stat().st_size,
        }
        
        return _success_response(info)
    except Exception as e:
        logger.error(f"Error getting image info {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def crop_image(image_path: str, output_path: str, x: int, y: int, width: int, height: int) -> Dict[str, Any]:
    """
    Crop image
    
    Args:
        image_path: Path to input image
        output_path: Path to output image
        x: X coordinate
        y: Y coordinate
        width: Crop width
        height: Crop height
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    if not PILLOW_AVAILABLE:
        return _error_response("Pillow not available. Install with: pip install Pillow", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(path_obj)
        cropped = img.crop((x, y, x + width, y + height))
        cropped.save(output_obj)
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error cropping image {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def rotate_image(image_path: str, output_path: str, degrees: float) -> Dict[str, Any]:
    """
    Rotate image
    
    Args:
        image_path: Path to input image
        output_path: Path to output image
        degrees: Rotation degrees (counter-clockwise)
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    if not PILLOW_AVAILABLE:
        return _error_response("Pillow not available. Install with: pip install Pillow", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(path_obj)
        rotated = img.rotate(degrees, expand=True)
        rotated.save(output_obj)
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error rotating image {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def compress_image(image_path: str, output_path: str, quality: int = 85) -> Dict[str, Any]:
    """
    Compress image
    
    Args:
        image_path: Path to input image
        output_path: Path to output image
        quality: Compression quality (1-100)
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    if not PILLOW_AVAILABLE:
        return _error_response("Pillow not available. Install with: pip install Pillow", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(path_obj)
        img.save(output_obj, optimize=True, quality=quality)
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error compressing image {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def create_thumbnail(image_path: str, output_path: str, size: Tuple[int, int] = (128, 128)) -> Dict[str, Any]:
    """
    Create thumbnail
    
    Args:
        image_path: Path to input image
        output_path: Path to output thumbnail
        size: Thumbnail size (width, height)
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    if not PILLOW_AVAILABLE:
        return _error_response("Pillow not available. Install with: pip install Pillow", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(path_obj)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(output_obj)
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error creating thumbnail {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def extract_image_metadata(image_path: str) -> Dict[str, Any]:
    """
    Extract EXIF/metadata
    
    Args:
        image_path: Path to image
        
    Returns:
        Dict with success, result (metadata dict), error, error_type
    """
    if not PILLOW_AVAILABLE:
        return _error_response("Pillow not available. Install with: pip install Pillow", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        img = Image.open(path_obj)
        
        metadata = {
            'format': img.format,
            'mode': img.mode,
            'size': img.size,
        }
        
        # Extract EXIF if available
        if hasattr(img, '_getexif') and img._getexif():
            exif = img._getexif()
            exif_dict = {}
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                exif_dict[tag] = value
            metadata['exif'] = exif_dict
        
        return _success_response(metadata)
    except Exception as e:
        logger.error(f"Error extracting image metadata {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

