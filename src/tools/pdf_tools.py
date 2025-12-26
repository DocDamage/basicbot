"""PDF operations tools"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .security import validate_path

logger = logging.getLogger('pdf_tools')

# Try to import PyPDF2 or pypdf
try:
    import pypdf
    PDF_AVAILABLE = True
    PDF_LIB = 'pypdf'
except ImportError:
    try:
        import PyPDF2 as pypdf
        PDF_AVAILABLE = True
        PDF_LIB = 'PyPDF2'
    except ImportError:
        PDF_AVAILABLE = False
        PDF_LIB = None


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


def pdf_extract_text(pdf_path: str, page_numbers: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Extract text from PDF
    
    Args:
        pdf_path: Path to PDF file
        page_numbers: Optional list of page numbers to extract (1-indexed)
        
    Returns:
        Dict with success, result (extracted text), error, error_type
    """
    if not PDF_AVAILABLE:
        return _error_response("PDF library not available. Install with: pip install pypdf or pip install PyPDF2", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(pdf_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(pdf_path)
        
        with open(path_obj, 'rb') as f:
            reader = pypdf.PdfReader(f)
            
            if page_numbers:
                pages = [reader.pages[i - 1] for i in page_numbers if 1 <= i <= len(reader.pages)]
            else:
                pages = reader.pages
            
            text_parts = []
            for page in pages:
                text_parts.append(page.extract_text())
            
            text = '\n\n'.join(text_parts)
        
        return _success_response(text)
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def pdf_get_page_count(pdf_path: str) -> Dict[str, Any]:
    """
    Get page count
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dict with success, result (page count), error, error_type
    """
    if not PDF_AVAILABLE:
        return _error_response("PDF library not available. Install with: pip install pypdf or pip install PyPDF2", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(pdf_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(pdf_path)
        
        with open(path_obj, 'rb') as f:
            reader = pypdf.PdfReader(f)
            count = len(reader.pages)
        
        return _success_response(count)
    except Exception as e:
        logger.error(f"Error getting page count {pdf_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def pdf_merge(pdf_files: List[str], output_path: str) -> Dict[str, Any]:
    """
    Merge PDFs
    
    Args:
        pdf_files: List of PDF file paths
        output_path: Output PDF path
        
    Returns:
        Dict with success, result (output path), error, error_type
    """
    if not PDF_AVAILABLE:
        return _error_response("PDF library not available. Install with: pip install pypdf or pip install PyPDF2", 'ImportError')
    
    try:
        # Validate all input files
        for pdf_file in pdf_files:
            is_valid, error_msg = validate_path(pdf_file, operation='read')
            if not is_valid:
                return _error_response(f"Invalid input file {pdf_file}: {error_msg}", 'ValidationError')
        
        # Validate output path
        is_valid, error_msg = validate_path(output_path, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        output_obj = Path(output_path)
        output_obj.parent.mkdir(parents=True, exist_ok=True)
        
        merger = pypdf.PdfMerger()
        
        for pdf_file in pdf_files:
            path_obj = Path(pdf_file)
            merger.append(str(path_obj))
        
        with open(output_obj, 'wb') as f:
            merger.write(f)
        
        merger.close()
        
        return _success_response(str(output_obj))
    except Exception as e:
        logger.error(f"Error merging PDFs: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def pdf_split(pdf_path: str, output_dir: str, page_ranges: Optional[List[tuple]] = None) -> Dict[str, Any]:
    """
    Split PDF
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory
        page_ranges: Optional list of (start, end) tuples for page ranges
        
    Returns:
        Dict with success, result (list of output files), error, error_type
    """
    if not PDF_AVAILABLE:
        return _error_response("PDF library not available. Install with: pip install pypdf or pip install PyPDF2", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(pdf_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_dir, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(pdf_path)
        output_obj = Path(output_dir)
        output_obj.mkdir(parents=True, exist_ok=True)
        
        with open(path_obj, 'rb') as f:
            reader = pypdf.PdfReader(f)
            total_pages = len(reader.pages)
            
            if page_ranges:
                ranges = page_ranges
            else:
                # Split each page
                ranges = [(i, i) for i in range(1, total_pages + 1)]
            
            output_files = []
            for i, (start, end) in enumerate(ranges):
                writer = pypdf.PdfWriter()
                for page_num in range(start - 1, end):
                    if 0 <= page_num < total_pages:
                        writer.add_page(reader.pages[page_num])
                
                output_file = output_obj / f"{path_obj.stem}_pages_{start}-{end}.pdf"
                with open(output_file, 'wb') as out_f:
                    writer.write(out_f)
                output_files.append(str(output_file))
        
        return _success_response(output_files)
    except Exception as e:
        logger.error(f"Error splitting PDF {pdf_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def pdf_convert_to_images(pdf_path: str, output_dir: str, dpi: int = 150) -> Dict[str, Any]:
    """
    Convert PDF to images
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory
        dpi: DPI for images
        
    Returns:
        Dict with success, result (list of image paths), error, error_type
    """
    try:
        # This requires pdf2image which needs poppler
        try:
            from pdf2image import convert_from_path
        except ImportError:
            return _error_response("pdf2image not available. Install with: pip install pdf2image (requires poppler)", 'ImportError')
        
        is_valid, error_msg = validate_path(pdf_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        is_valid, error_msg = validate_path(output_dir, operation='write', allow_absolute=True)
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(pdf_path)
        output_obj = Path(output_dir)
        output_obj.mkdir(parents=True, exist_ok=True)
        
        images = convert_from_path(str(path_obj), dpi=dpi)
        image_paths = []
        
        for i, image in enumerate(images):
            image_path = output_obj / f"{path_obj.stem}_page_{i+1}.png"
            image.save(image_path, 'PNG')
            image_paths.append(str(image_path))
        
        return _success_response(image_paths)
    except Exception as e:
        logger.error(f"Error converting PDF to images {pdf_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)


def pdf_get_metadata(pdf_path: str) -> Dict[str, Any]:
    """
    Get PDF metadata
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dict with success, result (metadata dict), error, error_type
    """
    if not PDF_AVAILABLE:
        return _error_response("PDF library not available. Install with: pip install pypdf or pip install PyPDF2", 'ImportError')
    
    try:
        is_valid, error_msg = validate_path(pdf_path, operation='read')
        if not is_valid:
            return _error_response(error_msg, 'ValidationError')
        
        path_obj = Path(pdf_path)
        
        with open(path_obj, 'rb') as f:
            reader = pypdf.PdfReader(f)
            metadata = reader.metadata or {}
            
            result = {
                'title': metadata.get('/Title', ''),
                'author': metadata.get('/Author', ''),
                'subject': metadata.get('/Subject', ''),
                'creator': metadata.get('/Creator', ''),
                'producer': metadata.get('/Producer', ''),
                'creation_date': str(metadata.get('/CreationDate', '')),
                'modification_date': str(metadata.get('/ModDate', '')),
                'page_count': len(reader.pages),
            }
        
        return _success_response(result)
    except Exception as e:
        logger.error(f"Error getting PDF metadata {pdf_path}: {e}", exc_info=True)
        return _error_response(str(e), type(e).__name__)

