"""Document processing tools"""

import zipfile
import os
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Optional
import markdown
from markdown.extensions import codehilite, fenced_code

# Setup logger for document tools
logger = logging.getLogger('document_tools')


def extract_markdown_from_zip(zip_path: str, output_dir: str) -> List[str]:
    """
    Extract Markdown files from zip archive
    
    Args:
        zip_path: Path to zip file
        output_dir: Directory to extract files to
        
    Returns:
        List of extracted file paths
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.namelist():
                # Only extract .md files
                if file_info.endswith('.md') or file_info.endswith('.markdown'):
                    # Extract to output directory
                    zip_ref.extract(file_info, output_dir)
                    extracted_path = output_path / file_info
                    if extracted_path.exists():
                        extracted_files.append(str(extracted_path))
    except Exception as e:
        error_msg = f"Error extracting {zip_path}: {str(e)}"
        print(error_msg)
        logger.error(error_msg, exc_info=True)
    
    return extracted_files


def parse_markdown_structure(file_path: str) -> Dict:
    """
    Parse Markdown file structure
    
    Args:
        file_path: Path to Markdown file
        
    Returns:
        Dictionary with structure information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse with markdown
        md = markdown.Markdown(extensions=['codehilite', 'fenced_code', 'tables'])
        html = md.convert(content)
        
        # Extract structure
        structure = {
            'file_path': file_path,
            'content': content,
            'html': html,
            'headers': _extract_headers(content),
            'code_blocks': _extract_code_blocks(content),
            'links': _extract_links(content),
            'metadata': _extract_metadata(content)
        }
        
        return structure
    except Exception as e:
        error_msg = f"Error parsing {file_path}: {str(e)}"
        error_details = traceback.format_exc()
        
        # Print to console (truncated)
        print(error_msg)
        
        # Log full details
        logger.error(f"Parse error for {file_path}")
        logger.debug(f"Error type: {type(e).__name__}")
        logger.debug(f"Error message: {str(e)}")
        logger.debug(f"Full traceback:\n{error_details}")
        
        # Try to get file info for debugging
        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            logger.debug(f"File size: {file_size} bytes")
        except:
            pass
        
        return {
            'file_path': file_path,
            'content': '',
            'html': '',
            'headers': [],
            'code_blocks': [],
            'links': [],
            'metadata': {},
            'error': str(e),
            'error_type': type(e).__name__
        }


def _extract_headers(content: str) -> List[Dict]:
    """Extract headers from Markdown content"""
    headers = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            headers.append({
                'level': level,
                'text': text,
                'line': i + 1
            })
    
    return headers


def _extract_code_blocks(content: str) -> List[Dict]:
    """Extract code blocks from Markdown content"""
    code_blocks = []
    lines = content.split('\n')
    in_code_block = False
    current_block = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            if in_code_block:
                # End of code block
                if current_block:
                    current_block['end_line'] = i + 1
                    code_blocks.append(current_block)
                in_code_block = False
                current_block = None
            else:
                # Start of code block
                language = line.strip()[3:].strip()
                in_code_block = True
                current_block = {
                    'language': language,
                    'start_line': i + 1,
                    'content': []
                }
        elif in_code_block and current_block:
            current_block['content'].append(line)
    
    return code_blocks


def _extract_links(content: str) -> List[Dict]:
    """Extract links from Markdown content"""
    import re
    links = []
    
    # Markdown links: [text](url)
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    matches = re.finditer(pattern, content)
    
    for match in matches:
        links.append({
            'text': match.group(1),
            'url': match.group(2)
        })
    
    return links


def _extract_metadata(content: str) -> Dict:
    """Extract frontmatter metadata if present"""
    metadata = {}
    
    if content.startswith('---'):
        lines = content.split('\n')
        if len(lines) > 1:
            end_idx = None
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    end_idx = i
                    break
            
            if end_idx:
                frontmatter = '\n'.join(lines[1:end_idx])
                # Simple key-value parsing
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
    
    return metadata

