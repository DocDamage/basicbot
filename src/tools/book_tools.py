"""Book processing tools for PDF, EPUB, MOBI, and TXT formats"""

import logging
import zipfile
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import shutil

from .security import validate_path
from .pdf_tools import pdf_extract_text, pdf_get_metadata

logger = logging.getLogger('book_tools')

# EPUB support
try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

# MOBI support
try:
    import mobi
    MOBI_AVAILABLE = True
    # Try to get read function
    if hasattr(mobi, 'read'):
        mobi_read = mobi.read
    else:
        mobi_read = None
except ImportError:
    MOBI_AVAILABLE = False
    mobi_read = None

# ISBN support
try:
    import isbnlib
    ISBN_AVAILABLE = True
except ImportError:
    ISBN_AVAILABLE = False


def extract_book_metadata(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from book file
    
    Args:
        file_path: Path to book file
        file_type: File type ('pdf', 'epub', 'mobi', 'txt')
        
    Returns:
        Dictionary with metadata
    """
    metadata = {
        'title': '',
        'author': '',
        'authors': [],
        'series': '',
        'series_number': None,
        'isbn': '',
        'publication_date': None,
        'genre': [],
        'language': 'en',
        'publisher': '',
        'page_count': 0,
        'word_count': 0,
        'file_path': file_path,
        'file_type': file_type,
        'processing_date': datetime.now().isoformat()
    }
    
    try:
        path_obj = Path(file_path)
        
        if file_type == 'pdf':
            result = pdf_get_metadata(file_path)
            if result.get('success'):
                pdf_meta = result.get('result', {})
                metadata['title'] = pdf_meta.get('title', '') or path_obj.stem
                metadata['author'] = pdf_meta.get('author', '')
                if metadata['author']:
                    metadata['authors'] = [metadata['author']]
                metadata['page_count'] = pdf_meta.get('page_count', 0)
                metadata['subject'] = pdf_meta.get('subject', '')
                if metadata['subject']:
                    metadata['genre'] = [metadata['subject']]
                
        elif file_type == 'epub':
            if EPUB_AVAILABLE:
                try:
                    book = epub.read_epub(file_path)
                    # Extract metadata from OPF
                    # Navigation items are handled separately if needed
                    # Most metadata comes from Dublin Core metadata below
                    
                    # Get Dublin Core metadata
                    dc_metadata = book.get_metadata('DC', 'title')
                    if dc_metadata:
                        metadata['title'] = dc_metadata[0][0] if dc_metadata else path_obj.stem
                    
                    dc_author = book.get_metadata('DC', 'creator')
                    if dc_author:
                        authors = [a[0] for a in dc_author]
                        metadata['authors'] = authors
                        metadata['author'] = authors[0] if authors else ''
                    
                    dc_date = book.get_metadata('DC', 'date')
                    if dc_date:
                        try:
                            date_str = dc_date[0][0]
                            # Try to parse date
                            metadata['publication_date'] = date_str
                        except Exception:
                            # Date parsing failed, skip
                            pass
                    
                    dc_language = book.get_metadata('DC', 'language')
                    if dc_language:
                        metadata['language'] = dc_language[0][0]
                    
                    dc_publisher = book.get_metadata('DC', 'publisher')
                    if dc_publisher:
                        metadata['publisher'] = dc_publisher[0][0]
                    
                    dc_subject = book.get_metadata('DC', 'subject')
                    if dc_subject:
                        metadata['genre'] = [s[0] for s in dc_subject]
                    
                    dc_identifier = book.get_metadata('DC', 'identifier')
                    if dc_identifier:
                        for ident in dc_identifier:
                            ident_value = ident[0]
                            if ISBN_AVAILABLE and isbnlib.is_isbn10(ident_value) or isbnlib.is_isbn13(ident_value):
                                metadata['isbn'] = ident_value
                                break
                    
                    # Try to extract series info from title or metadata
                    title = metadata.get('title', '')
                    series_match = re.search(r'\(([^)]+)\s*#?\s*(\d+)\)', title)
                    if series_match:
                        metadata['series'] = series_match.group(1).strip()
                        try:
                            metadata['series_number'] = int(series_match.group(2))
                        except (ValueError, IndexError):
                            # Series number parsing failed, skip
                            pass
                    
                except Exception as e:
                    logger.warning(f"Error extracting EPUB metadata: {e}")
                    metadata['title'] = path_obj.stem
            else:
                metadata['title'] = path_obj.stem
                
        elif file_type == 'mobi':
            if MOBI_AVAILABLE:
                try:
                    # MOBI files contain metadata in header
                    with open(file_path, 'rb') as f:
                        mobi_data = mobi_read(f)
                        if mobi_data:
                            # Extract metadata from MOBI structure
                            metadata['title'] = mobi_data.get('title', path_obj.stem)
                            metadata['author'] = mobi_data.get('author', '')
                            if metadata['author']:
                                metadata['authors'] = [metadata['author']]
                except Exception as e:
                    logger.warning(f"Error extracting MOBI metadata: {e}")
                    metadata['title'] = path_obj.stem
            else:
                metadata['title'] = path_obj.stem
                
        elif file_type == 'txt':
            # For TXT files, try to extract from filename or content
            metadata['title'] = path_obj.stem
            # Try to parse author from filename (e.g., "Author - Title.txt")
            filename = path_obj.stem
            if ' - ' in filename:
                parts = filename.split(' - ', 1)
                metadata['author'] = parts[0].strip()
                metadata['title'] = parts[1].strip()
                metadata['authors'] = [metadata['author']]
        
        # If title is still empty, use filename
        if not metadata['title']:
            metadata['title'] = path_obj.stem
            
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {e}", exc_info=True)
        # Return basic metadata with filename as title
        metadata['title'] = Path(file_path).stem
    
    return metadata


def extract_epub_content(epub_path: str) -> Dict[str, Any]:
    """
    Parse EPUB file and extract content with enhanced metadata
    
    Args:
        epub_path: Path to EPUB file
        
    Returns:
        Dictionary with content, metadata, and structure
    """
    if not EPUB_AVAILABLE:
        return {
            'success': False,
            'error': 'ebooklib not available. Install with: pip install ebooklib',
            'content': '',
            'metadata': {}
        }
    
    try:
        is_valid, error_msg = validate_path(epub_path, operation='read')
        if not is_valid:
            return {'success': False, 'error': error_msg, 'content': '', 'metadata': {}}
        
        book = epub.read_epub(epub_path)
        content_parts = []
        chapters = []
        
        # Extract all text content
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Get HTML content
                html_content = item.get_content().decode('utf-8')
                
                # Simple HTML to text conversion
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                text = soup.get_text(separator='\n', strip=True)
                
                if text.strip():
                    content_parts.append(text)
                    
                    # Try to identify chapter titles
                    headings = soup.find_all(['h1', 'h2', 'h3'])
                    for heading in headings:
                        heading_text = heading.get_text(strip=True)
                        if heading_text and len(heading_text) < 200:  # Likely a chapter title
                            chapters.append({
                                'title': heading_text,
                                'position': len(content_parts) - 1
                            })
        
        full_content = '\n\n'.join(content_parts)
        
        # Extract metadata
        metadata = extract_book_metadata(epub_path, 'epub')
        metadata['word_count'] = len(full_content.split())
        
        return {
            'success': True,
            'content': full_content,
            'metadata': metadata,
            'chapters': chapters,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Error extracting EPUB content from {epub_path}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'content': '',
            'metadata': {},
            'chapters': []
        }


def extract_mobi_content(mobi_path: str) -> Dict[str, Any]:
    """
    Parse MOBI file and extract content
    
    Args:
        mobi_path: Path to MOBI file
        
    Returns:
        Dictionary with content, metadata, and structure
    """
    if not MOBI_AVAILABLE or not mobi_read:
        return {
            'success': False,
            'error': 'mobi library not available. Install with: pip install mobi',
            'content': '',
            'metadata': {}
        }
    
    try:
        is_valid, error_msg = validate_path(mobi_path, operation='read')
        if not is_valid:
            return {'success': False, 'error': error_msg, 'content': '', 'metadata': {}}
        
        with open(mobi_path, 'rb') as f:
            mobi_data = mobi_read(f)
            
            if not mobi_data:
                return {
                    'success': False,
                    'error': 'Failed to read MOBI file',
                    'content': '',
                    'metadata': {}
                }
            
            # mobi.read returns a dict with 'content' and metadata
            if isinstance(mobi_data, dict):
                content = mobi_data.get('content', '')
            else:
                # If it's a string or other format
                content = str(mobi_data) if mobi_data else ''
            metadata = extract_book_metadata(mobi_path, 'mobi')
            metadata['word_count'] = len(content.split()) if content else 0
            
            return {
                'success': True,
                'content': content,
                'metadata': metadata,
                'chapters': [],  # MOBI chapters would need additional parsing
                'error': None
            }
            
    except Exception as e:
        logger.error(f"Error extracting MOBI content from {mobi_path}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'content': '',
            'metadata': {},
            'chapters': []
        }


def extract_pdf_content(pdf_path: str) -> Dict[str, Any]:
    """
    Enhanced PDF extraction with better formatting
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dictionary with content, metadata, and structure
    """
    try:
        is_valid, error_msg = validate_path(pdf_path, operation='read')
        if not is_valid:
            return {'success': False, 'error': error_msg, 'content': '', 'metadata': {}}
        
        # Extract text
        result = pdf_extract_text(pdf_path)
        if not result.get('success'):
            return {
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'content': '',
                'metadata': {}
            }
        
        content = result.get('result', '')
        
        # Extract metadata
        metadata = extract_book_metadata(pdf_path, 'pdf')
        metadata['word_count'] = len(content.split()) if content else 0
        
        # Try to detect chapters (look for common chapter patterns)
        chapters = detect_chapters(content, 'pdf')
        
        return {
            'success': True,
            'content': content,
            'metadata': metadata,
            'chapters': chapters,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Error extracting PDF content from {pdf_path}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'content': '',
            'metadata': {},
            'chapters': []
        }


def extract_txt_content(txt_path: str) -> Dict[str, Any]:
    """
    Extract content from TXT file
    
    Args:
        txt_path: Path to TXT file
        
    Returns:
        Dictionary with content, metadata, and structure
    """
    try:
        is_valid, error_msg = validate_path(txt_path, operation='read')
        if not is_valid:
            return {'success': False, 'error': error_msg, 'content': '', 'metadata': {}}
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(txt_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            return {
                'success': False,
                'error': 'Could not decode text file with any encoding',
                'content': '',
                'metadata': {}
            }
        
        # Extract metadata
        metadata = extract_book_metadata(txt_path, 'txt')
        metadata['word_count'] = len(content.split())
        
        # Detect chapters
        chapters = detect_chapters(content, 'txt')
        
        return {
            'success': True,
            'content': content,
            'metadata': metadata,
            'chapters': chapters,
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Error extracting TXT content from {txt_path}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'content': '',
            'metadata': {},
            'chapters': []
        }


def detect_chapters(content: str, file_type: str) -> List[Dict[str, Any]]:
    """
    Identify chapter boundaries in content
    
    Args:
        content: Book content text
        file_type: File type for context
        
    Returns:
        List of chapter dictionaries with title and position
    """
    chapters = []
    
    if not content:
        return chapters
    
    # Common chapter patterns
    chapter_patterns = [
        r'^Chapter\s+(\d+)[\s:]+(.+)$',  # Chapter 1: Title
        r'^CHAPTER\s+(\d+)[\s:]+(.+)$',  # CHAPTER 1: Title
        r'^Chapter\s+(\d+)$',  # Chapter 1
        r'^CHAPTER\s+(\d+)$',  # CHAPTER 1
        r'^(\d+)\.\s+(.+)$',  # 1. Title
        r'^Part\s+(\d+)[\s:]+(.+)$',  # Part 1: Title
        r'^PART\s+(\d+)[\s:]+(.+)$',  # PART 1: Title
        r'^Book\s+(\d+)[\s:]+(.+)$',  # Book 1: Title
    ]
    
    lines = content.split('\n')
    current_chapter = None
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Check each pattern
        for pattern in chapter_patterns:
            match = re.match(pattern, line_stripped, re.IGNORECASE)
            if match:
                chapter_num = match.group(1) if match.groups() else None
                chapter_title = match.group(2) if len(match.groups()) > 1 else None
                
                if current_chapter:
                    # Close previous chapter
                    current_chapter['end_line'] = i - 1
                    current_chapter['word_count'] = len(' '.join(lines[current_chapter['start_line']:i]).split())
                
                # Start new chapter
                current_chapter = {
                    'chapter_number': int(chapter_num) if chapter_num and chapter_num.isdigit() else len(chapters) + 1,
                    'chapter_title': chapter_title or f"Chapter {len(chapters) + 1}",
                    'start_line': i,
                    'end_line': len(lines),
                    'word_count': 0
                }
                chapters.append(current_chapter)
                break
    
    # Finalize last chapter
    if current_chapter:
        current_chapter['end_line'] = len(lines)
        current_chapter['word_count'] = len(' '.join(lines[current_chapter['start_line']:]).split())
    
    return chapters


def merge_book_formats(book_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge content from multiple formats of the same book
    
    Args:
        book_entries: List of book data dictionaries from different formats
        
    Returns:
        Merged book data dictionary
    """
    if not book_entries:
        return {}
    
    if len(book_entries) == 1:
        return book_entries[0]
    
    # Use the first entry as base
    merged = book_entries[0].copy()
    
    # Merge metadata - prefer non-empty values
    for entry in book_entries[1:]:
        entry_meta = entry.get('metadata', {})
        merged_meta = merged.get('metadata', {})
        
        # Merge fields, preferring more complete data
        for key in ['title', 'author', 'isbn', 'publisher', 'publication_date']:
            if not merged_meta.get(key) and entry_meta.get(key):
                merged_meta[key] = entry_meta[key]
        
        # Merge lists
        for key in ['authors', 'genre']:
            existing = set(merged_meta.get(key, []))
            new = set(entry_meta.get(key, []))
            merged_meta[key] = list(existing | new)
        
        # Use longest content
        entry_content = entry.get('content', '')
        merged_content = merged.get('content', '')
        if len(entry_content) > len(merged_content):
            merged['content'] = entry_content
            merged['chapters'] = entry.get('chapters', [])
            merged_meta['word_count'] = entry_meta.get('word_count', 0)
        
        # Merge formats
        if 'formats' not in merged_meta:
            merged_meta['formats'] = []
        merged_meta['formats'].append(entry_meta.get('file_type', ''))
        merged_meta['formats'] = list(set(merged_meta['formats']))
    
    merged['metadata'] = merged_meta
    return merged


def archive_original_file(file_path: str, archive_dir: str) -> Dict[str, Any]:
    """
    Move processed file to archive directory
    
    Args:
        file_path: Path to original file
        archive_dir: Archive directory path
        
    Returns:
        Dictionary with success status and archive path
    """
    try:
        is_valid, error_msg = validate_path(file_path, operation='read')
        if not is_valid:
            return {'success': False, 'error': error_msg, 'archive_path': None}
        
        path_obj = Path(file_path)
        archive_path_obj = Path(archive_dir)
        archive_path_obj.mkdir(parents=True, exist_ok=True)
        
        # Create archive path preserving directory structure
        relative_path = path_obj.relative_to(path_obj.anchor) if path_obj.is_absolute() else path_obj
        archive_file_path = archive_path_obj / relative_path.name
        
        # If file exists in archive, add timestamp
        if archive_file_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_file_path = archive_path_obj / f"{path_obj.stem}_{timestamp}{path_obj.suffix}"
        
        # Move file
        shutil.move(str(path_obj), str(archive_file_path))
        
        return {
            'success': True,
            'archive_path': str(archive_file_path),
            'error': None
        }
        
    except Exception as e:
        logger.error(f"Error archiving file {file_path}: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'archive_path': None
        }


def extract_book_content(file_path: str) -> Dict[str, Any]:
    """
    Extract content from book file (auto-detect format)
    
    Args:
        file_path: Path to book file
        
    Returns:
        Dictionary with content, metadata, and structure
    """
    path_obj = Path(file_path)
    file_ext = path_obj.suffix.lower()
    
    if file_ext == '.pdf':
        return extract_pdf_content(file_path)
    elif file_ext == '.epub':
        return extract_epub_content(file_path)
    elif file_ext == '.mobi':
        return extract_mobi_content(file_path)
    elif file_ext == '.txt':
        return extract_txt_content(file_path)
    else:
        return {
            'success': False,
            'error': f'Unsupported file format: {file_ext}',
            'content': '',
            'metadata': {},
            'chapters': []
        }

