"""Media file operations tools (video and audio)"""

import logging
import base64
from pathlib import Path
from typing import Dict, Optional, Any

from .security import validate_path

logger = logging.getLogger('media_tools')

# Try to import optional dependencies
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import mutagen
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


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


def read_image(image_path: str, return_base64: bool = False) -> Dict[str, Any]:
    """
    Read/open image file
    
    Args:
        image_path: Path to image file
        return_base64: If True, return image as base64 string
        
    Returns:
        Dict with success, result (image info or base64), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(image_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(image_path)
        
        if not path_obj.exists():
            return _error_response(f"Image file does not exist: {image_path}", 'FileNotFoundError')
        
        result = {
            'path': str(path_obj),
            'size': path_obj.stat().st_size,
        }
        
        # Try to get image info using Pillow
        try:
            from PIL import Image
            img = Image.open(path_obj)
            result.update({
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
            })
            
            if return_base64:
                import io
                buffer = io.BytesIO()
                img.save(buffer, format=img.format or 'PNG')
                result['base64'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
                result['mime_type'] = f"image/{img.format.lower() if img.format else 'png'}"
        except ImportError:
            result['note'] = 'Pillow not available for detailed image info'
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error reading image {image_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def read_video(video_path: str, extract_metadata: bool = True) -> Dict[str, Any]:
    """
    Read/open video file and extract metadata
    
    Args:
        video_path: Path to video file
        extract_metadata: Extract video metadata (duration, resolution, etc.)
        
    Returns:
        Dict with success, result (video info), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(video_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(video_path)
        
        if not path_obj.exists():
            return _error_response(f"Video file does not exist: {video_path}", 'FileNotFoundError')
        
        result = {
            'path': str(path_obj),
            'size': path_obj.stat().st_size,
            'extension': path_obj.suffix.lower(),
        }
        
        # Extract metadata if requested
        if extract_metadata:
            if MOVIEPY_AVAILABLE:
                try:
                    clip = VideoFileClip(str(path_obj))
                    result.update({
                        'duration': clip.duration,
                        'fps': clip.fps,
                        'size': clip.size,
                        'width': clip.w,
                        'height': clip.h,
                    })
                    clip.close()
                except Exception as e:
                    result['metadata_error'] = str(e)
            elif OPENCV_AVAILABLE:
                try:
                    cap = cv2.VideoCapture(str(path_obj))
                    if cap.isOpened():
                        result.update({
                            'fps': cap.get(cv2.CAP_PROP_FPS),
                            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                        })
                        if result.get('fps') and result.get('frame_count'):
                            result['duration'] = result['frame_count'] / result['fps']
                    cap.release()
                except Exception as e:
                    result['metadata_error'] = str(e)
            else:
                result['note'] = 'No video library available for metadata extraction'
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error reading video {video_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def read_audio(audio_path: str, extract_metadata: bool = True) -> Dict[str, Any]:
    """
    Read/open audio file and extract metadata
    
    Args:
        audio_path: Path to audio file
        extract_metadata: Extract audio metadata (duration, bitrate, etc.)
        
    Returns:
        Dict with success, result (audio info), error, error_type
    """
    try:
        is_valid, error_msg = validate_path(audio_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(audio_path)
        
        if not path_obj.exists():
            return _error_response(f"Audio file does not exist: {audio_path}", 'FileNotFoundError')
        
        result = {
            'path': str(path_obj),
            'size': path_obj.stat().st_size,
            'extension': path_obj.suffix.lower(),
        }
        
        # Extract metadata if requested
        if extract_metadata:
            if PYDUB_AVAILABLE:
                try:
                    audio = AudioSegment.from_file(str(path_obj))
                    result.update({
                        'duration': len(audio) / 1000.0,  # Convert to seconds
                        'channels': audio.channels,
                        'frame_rate': audio.frame_rate,
                        'sample_width': audio.sample_width,
                        'frame_width': audio.frame_width,
                    })
                except Exception as e:
                    result['metadata_error'] = str(e)
            
            # Try to get ID3 tags and other metadata
            if MUTAGEN_AVAILABLE:
                try:
                    file = mutagen.File(str(path_obj))
                    if file:
                        result['tags'] = {}
                        for key, value in file.items():
                            if isinstance(value, list) and len(value) > 0:
                                result['tags'][key] = value[0] if len(value) == 1 else value
                        result['bitrate'] = getattr(file.info, 'bitrate', None)
                        result['length'] = getattr(file.info, 'length', None)
                except Exception as e:
                    if 'tags' not in result:
                        result['tags_error'] = str(e)
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error reading audio {audio_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def get_video_info(video_path: str) -> Dict[str, Any]:
    """
    Get video file information
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dict with success, result (video info), error, error_type
    """
    return read_video(video_path, extract_metadata=True)


def get_audio_info(audio_path: str) -> Dict[str, Any]:
    """
    Get audio file information
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Dict with success, result (audio info), error, error_type
    """
    return read_audio(audio_path, extract_metadata=True)


def extract_video_frame(video_path: str, timestamp: float, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract a frame from video at specific timestamp
    
    Args:
        video_path: Path to video file
        timestamp: Timestamp in seconds
        output_path: Optional path to save frame image
        
    Returns:
        Dict with success, result (frame info or saved path), error, error_type
    """
    if not OPENCV_AVAILABLE and not MOVIEPY_AVAILABLE:
        return _error_response("OpenCV or MoviePy required. Install with: pip install opencv-python or pip install moviepy", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(video_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(video_path)
        
        if OPENCV_AVAILABLE:
            cap = cv2.VideoCapture(str(path_obj))
            if not cap.isOpened():
                return _error_response("Could not open video file", 'VideoError')
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return _error_response(f"Could not read frame at timestamp {timestamp}", 'VideoError')
            
            if output_path:
                is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
                if not is_valid:
                    return _error_response(error_msg, 'ValidationError')
                
                output_obj = Path(output_path)
                output_obj.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(output_obj), frame)
                return _success_response(str(output_obj))
            else:
                # Return frame as base64
                import base64
                import numpy as np
                from PIL import Image
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                import io
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                frame_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return _success_response({
                    'timestamp': timestamp,
                    'frame_number': frame_number,
                    'base64': frame_base64,
                    'mime_type': 'image/png',
                })
        else:
            # Use MoviePy
            clip = VideoFileClip(str(path_obj))
            frame = clip.get_frame(timestamp)
            clip.close()
            
            if output_path:
                from PIL import Image
                img = Image.fromarray(frame)
                output_obj = Path(output_path)
                output_obj.parent.mkdir(parents=True, exist_ok=True)
                img.save(output_obj)
                return _success_response(str(output_obj))
            else:
                import base64
                from PIL import Image
                import io
                img = Image.fromarray(frame)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                frame_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return _success_response({
                    'timestamp': timestamp,
                    'base64': frame_base64,
                    'mime_type': 'image/png',
                })
    except Exception as e:
        logger.error(f"Error extracting video frame {video_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

