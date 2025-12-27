"""Chunking tools for Markdown documents"""

from typing import List, Dict, Optional
import re


def hybrid_chunk_markdown(
    content: str,
    structure: Dict,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict]:
    """
    Hybrid chunking: structure-aware with size limits
    
    Args:
        content: Markdown content
        structure: Parsed structure from parse_markdown_structure
        chunk_size: Maximum chunk size in tokens (approximate)
        chunk_overlap: Overlap between chunks in tokens
        
    Returns:
        List of chunks with metadata
    """
    chunks = []
    headers = structure.get('headers', [])
    
    if not headers:
        # No structure, use fixed-size chunking
        return _fixed_size_chunk(content, chunk_size, chunk_overlap)
    
    # Structure-aware chunking
    lines = content.split('\n')
    current_section = None
    current_chunk_lines = []
    current_chunk_size = 0
    
    for i, line in enumerate(lines):
        # Check if this is a header
        header_info = _get_header_at_line(i, headers)
        
        if header_info:
            # Save current chunk if it exists
            if current_chunk_lines and current_section:
                chunk_text = '\n'.join(current_chunk_lines)
                if len(chunk_text.strip()) > 0:
                    chunks.append({
                        'content': chunk_text,
                        'section': current_section,
                        'start_line': current_section.get('start_line', 0),
                        'end_line': i,
                        'metadata': {
                            'type': 'section',
                            'header_level': current_section.get('level', 0)
                        }
                    })
            
            # Start new section
            current_section = {
                'text': header_info['text'],
                'level': header_info['level'],
                'start_line': i
            }
            current_chunk_lines = [line]
            current_chunk_size = _estimate_tokens(line)
        else:
            # Add line to current chunk
            line_tokens = _estimate_tokens(line)
            
            # Check if adding this line would exceed chunk size
            if current_chunk_size + line_tokens > chunk_size and current_chunk_lines:
                # Save current chunk
                chunk_text = '\n'.join(current_chunk_lines)
                if len(chunk_text.strip()) > 0:
                    chunks.append({
                        'content': chunk_text,
                        'section': current_section,
                        'start_line': current_section.get('start_line', 0) if current_section else 0,
                        'end_line': i,
                        'metadata': {
                            'type': 'section_split',
                            'header_level': current_section.get('level', 0) if current_section else 0
                        }
                    })
                
                # Start new chunk with overlap
                overlap_lines = _get_overlap_lines(current_chunk_lines, chunk_overlap)
                current_chunk_lines = overlap_lines + [line]
                current_chunk_size = sum(_estimate_tokens(l) for l in current_chunk_lines)
            else:
                current_chunk_lines.append(line)
                current_chunk_size += line_tokens
    
    # Save final chunk
    if current_chunk_lines:
        chunk_text = '\n'.join(current_chunk_lines)
        if len(chunk_text.strip()) > 0:
            chunks.append({
                'content': chunk_text,
                'section': current_section,
                'start_line': current_section.get('start_line', 0) if current_section else 0,
                'end_line': len(lines),
                'metadata': {
                    'type': 'section',
                    'header_level': current_section.get('level', 0) if current_section else 0
                }
            })
    
    # Add source file info to each chunk
    # Normalize path to ensure consistent storage (absolute path, normalized separators)
    import os
    file_path = structure.get('file_path', '')
    if file_path:
        try:
            # Convert to absolute path and normalize separators
            normalized_path = os.path.abspath(file_path).replace('\\', '/')
        except Exception:
            # Fallback to original if normalization fails
            normalized_path = file_path.replace('\\', '/')
    else:
        normalized_path = ''
    
    for chunk in chunks:
        chunk['source_file'] = normalized_path
        chunk['metadata']['source_file'] = normalized_path
    
    return chunks


def _fixed_size_chunk(content: str, chunk_size: int, chunk_overlap: int) -> List[Dict]:
    """Fixed-size chunking fallback"""
    chunks = []
    lines = content.split('\n')
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_tokens = _estimate_tokens(line)
        
        if current_size + line_tokens > chunk_size and current_chunk:
            # Save chunk
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                'content': chunk_text,
                'section': None,
                'start_line': 0,
                'end_line': len(lines),
                'source_file': '',
                'metadata': {
                    'type': 'fixed_size',
                    'header_level': 0
                }
            })
            
            # Start new chunk with overlap
            overlap_lines = _get_overlap_lines(current_chunk, chunk_overlap)
            current_chunk = overlap_lines + [line]
            current_size = sum(_estimate_tokens(l) for l in current_chunk)
        else:
            current_chunk.append(line)
            current_size += line_tokens
    
    # Final chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        chunks.append({
            'content': chunk_text,
            'section': None,
            'start_line': 0,
            'end_line': len(lines),
            'source_file': '',
            'metadata': {
                'type': 'fixed_size',
                'header_level': 0
            }
        })
    
    return chunks


def _estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: 1 token ≈ 4 characters)"""
    return len(text) // 4


def _get_header_at_line(line_num: int, headers: List[Dict]) -> Optional[Dict]:
    """Get header information at a specific line number"""
    for header in headers:
        if header['line'] == line_num + 1:  # Headers are 1-indexed
            return header
    return None


def _get_overlap_lines(lines: List[str], overlap_tokens: int) -> List[str]:
    """Get overlap lines from the end of a chunk"""
    overlap_lines = []
    overlap_size = 0
    
    for line in reversed(lines):
        line_tokens = _estimate_tokens(line)
        if overlap_size + line_tokens <= overlap_tokens:
            overlap_lines.insert(0, line)
            overlap_size += line_tokens
        else:
            break
    
    return overlap_lines


def chunk_by_chapters(
    content: str,
    chapters: List[Dict],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict]:
    """
    Chunk book by chapters (preserve chapter boundaries)
    
    Args:
        content: Book content text
        chapters: List of chapter dictionaries with start_line, end_line, title, etc.
        chunk_size: Maximum chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens
        
    Returns:
        List of chunks with chapter metadata
    """
    chunks = []
    lines = content.split('\n')
    
    if not chapters:
        # No chapters detected, use fixed-size chunking
        return _fixed_size_chunk(content, chunk_size, chunk_overlap)
    
    for chapter_idx, chapter in enumerate(chapters):
        chapter_num = chapter.get('chapter_number', chapter_idx + 1)
        chapter_title = chapter.get('chapter_title', f"Chapter {chapter_num}")
        start_line = chapter.get('start_line', 0)
        end_line = chapter.get('end_line', len(lines))
        
        # Extract chapter content
        chapter_lines = lines[start_line:end_line]
        chapter_content = '\n'.join(chapter_lines)
        
        # If chapter is small enough, use as single chunk
        chapter_tokens = _estimate_tokens(chapter_content)
        if chapter_tokens <= chunk_size:
            chunks.append({
                'content': chapter_content,
                'section': {
                    'text': chapter_title,
                    'level': 2,
                    'start_line': start_line
                },
                'start_line': start_line,
                'end_line': end_line,
                'metadata': {
                    'type': 'chapter',
                    'chapter_number': chapter_num,
                    'chapter_title': chapter_title,
                    'header_level': 2
                }
            })
        else:
            # Chapter is too long, sub-chunk it
            sub_chunks = _fixed_size_chunk(chapter_content, chunk_size, chunk_overlap)
            for sub_idx, sub_chunk in enumerate(sub_chunks):
                chunks.append({
                    'content': sub_chunk['content'],
                    'section': {
                        'text': chapter_title,
                        'level': 2,
                        'start_line': start_line
                    },
                    'start_line': start_line + sub_chunk.get('start_line', 0),
                    'end_line': start_line + sub_chunk.get('end_line', len(chapter_lines)),
                    'metadata': {
                        'type': 'chapter_subsection',
                        'chapter_number': chapter_num,
                        'chapter_title': chapter_title,
                        'sub_chunk_index': sub_idx,
                        'header_level': 2
                    }
                })
    
    return chunks


def hybrid_chunk_book(
    content: str,
    chapters: List[Dict],
    book_metadata: Dict,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict]:
    """
    Hybrid chunking for books: Chapter-based with sub-chunking for long chapters
    
    Args:
        content: Book content text
        chapters: List of chapter dictionaries
        book_metadata: Book metadata dictionary
        chunk_size: Maximum chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens
        
    Returns:
        List of chunks with book and chapter metadata
    """
    # Use chapter-based chunking
    chunks = chunk_by_chapters(content, chapters, chunk_size, chunk_overlap)
    
    # Add book metadata to each chunk
    book_id = book_metadata.get('book_id', '')
    book_title = book_metadata.get('title', '')
    author = book_metadata.get('author', '')
    series = book_metadata.get('series', '')
    
    for chunk in chunks:
        # Add book metadata
        chunk['metadata']['book_id'] = book_id
        chunk['metadata']['book_title'] = book_title
        chunk['metadata']['author'] = author
        chunk['metadata']['series'] = series
        chunk['metadata']['content_type'] = 'book'
        
        # Add chapter info if available
        if 'chapter_number' in chunk['metadata']:
            chunk['metadata']['chapter_number'] = chunk['metadata'].get('chapter_number')
            chunk['metadata']['chapter_title'] = chunk['metadata'].get('chapter_title')
    
    return chunks
