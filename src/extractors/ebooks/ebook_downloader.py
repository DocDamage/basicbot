"""Ebook downloader and converter for chatbot integration"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime
import requests
import json
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extractors.base_extractor import BaseExtractor

class EbookDownloader(BaseExtractor):
    """Download and convert ebooks from various free sources"""
    
    def __init__(self):
        super().__init__(
            name="Ebooks Collection",
            source="Multiple Free Sources",
            url="https://www.gutenberg.org/"
        )
        # Override output directory
        self.output_dir = Path("data/extracted_docs/ebooks")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.output_dir / "raw"
        self.raw_dir.mkdir(exist_ok=True)
        self.md_dir = self.output_dir / "md"
        self.md_dir.mkdir(exist_ok=True)
    
    def get_ebook_sources(self) -> List[Dict[str, str]]:
        """Get list of free ebook sources"""
        return [
            {
                "name": "Project Gutenberg",
                "url": "https://www.gutenberg.org/",
                "api": "https://gutendex.com/books/",
                "format": "epub, html, txt"
            },
            {
                "name": "Internet Archive",
                "url": "https://archive.org/details/texts",
                "api": "https://archive.org/advancedsearch.php",
                "format": "pdf, epub, txt"
            },
            {
                "name": "Standard Ebooks",
                "url": "https://standardebooks.org/",
                "api": None,
                "format": "epub"
            },
            {
                "name": "ManyBooks",
                "url": "https://manybooks.net/",
                "api": None,
                "format": "epub, pdf, txt"
            },
            {
                "name": "Feedbooks",
                "url": "https://www.feedbooks.com/publicdomain",
                "api": None,
                "format": "epub, pdf"
            }
        ]
    
    def download_from_gutenberg(self, limit: int = 50) -> List[Path]:
        """Download ebooks from Project Gutenberg using Gutendex API"""
        downloaded_files = []
        
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Get popular books from Gutendex API
            api_url = f"https://gutendex.com/books/?languages=en&mime_type=text%2Fplain&page=1"
            
            response = session.get(api_url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                books = data.get('results', [])[:limit]
                
                print(f"    Found {len(books)} books from Project Gutenberg")
                
                for i, book in enumerate(books, 1):
                    try:
                        book_id = book.get('id')
                        title = book.get('title', 'Unknown')
                        authors = ', '.join([a.get('name', '') for a in book.get('authors', [])])
                        
                        # Get text download link
                        download_links = book.get('formats', {})
                        text_url = download_links.get('text/plain; charset=utf-8') or download_links.get('text/plain')
                        
                        if text_url:
                            print(f"    [{i}/{len(books)}] Downloading: {title[:50]}...")
                            
                            file_response = session.get(text_url, timeout=60)
                            if file_response.status_code == 200:
                                # Clean filename
                                safe_title = re.sub(r'[^\w\s-]', '', title)[:100]
                                filename = f"gutenberg_{book_id}_{safe_title}.txt"
                                raw_file = self.raw_dir / filename
                                raw_file.write_bytes(file_response.content)
                                downloaded_files.append(raw_file)
                                print(f"      ✓ Saved: {filename}")
                    except Exception as e:
                        print(f"      ⚠️  Error downloading book {i}: {e}")
                        continue
            
        except Exception as e:
            print(f"    ⚠️  Error accessing Gutenberg API: {e}")
        
        return downloaded_files
    
    def download_from_archive(self, limit: int = 20) -> List[Path]:
        """Download ebooks from Internet Archive"""
        downloaded_files = []
        
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            # Internet Archive API search for public domain texts
            api_url = "https://archive.org/advancedsearch.php"
            params = {
                'q': 'collection:texts AND mediatype:texts AND language:eng',
                'fl': 'identifier,title,creator',
                'sort': 'downloads desc',
                'rows': limit,
                'page': 1,
                'output': 'json'
            }
            
            response = session.get(api_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                docs = data.get('response', {}).get('docs', [])
                
                print(f"    Found {len(docs)} books from Internet Archive")
                
                for i, doc in enumerate(docs, 1):
                    try:
                        identifier = doc.get('identifier')
                        title = doc.get('title', 'Unknown')
                        
                        # Try to get PDF or text file
                        download_url = f"https://archive.org/download/{identifier}/{identifier}.pdf"
                        
                        print(f"    [{i}/{len(docs)}] Downloading: {title[:50]}...")
                        
                        file_response = session.get(download_url, timeout=60, allow_redirects=True)
                        if file_response.status_code == 200 and 'pdf' in file_response.headers.get('content-type', '').lower():
                            safe_title = re.sub(r'[^\w\s-]', '', title)[:100]
                            filename = f"archive_{identifier}_{safe_title}.pdf"
                            raw_file = self.raw_dir / filename
                            raw_file.write_bytes(file_response.content)
                            downloaded_files.append(raw_file)
                            print(f"      ✓ Saved: {filename}")
                        else:
                            # Try text version
                            text_url = f"https://archive.org/download/{identifier}/{identifier}_djvu.txt"
                            text_response = session.get(text_url, timeout=60)
                            if text_response.status_code == 200:
                                safe_title = re.sub(r'[^\w\s-]', '', title)[:100]
                                filename = f"archive_{identifier}_{safe_title}.txt"
                                raw_file = self.raw_dir / filename
                                raw_file.write_bytes(text_response.content)
                                downloaded_files.append(raw_file)
                                print(f"      ✓ Saved: {filename}")
                    except Exception as e:
                        print(f"      ⚠️  Error downloading book {i}: {e}")
                        continue
            
        except Exception as e:
            print(f"    ⚠️  Error accessing Internet Archive: {e}")
        
        return downloaded_files
    
    def download(self) -> Optional[Path]:
        """Download ebooks from multiple sources"""
        print(f"    Downloading ebooks from free sources...")
        
        all_files = []
        
        # Download from Project Gutenberg
        print("  Downloading from Project Gutenberg...")
        gutenberg_files = self.download_from_gutenberg(limit=30)
        all_files.extend(gutenberg_files)
        
        # Download from Internet Archive
        print("  Downloading from Internet Archive...")
        archive_files = self.download_from_archive(limit=20)
        all_files.extend(archive_files)
        
        if all_files:
            print(f"    ✓ Downloaded {len(all_files)} ebooks")
            # Return a marker file to indicate download completed
            marker_file = self.raw_dir / f"download_complete_{datetime.now().strftime('%Y%m%d')}.txt"
            marker_file.write_text(f"Downloaded {len(all_files)} ebooks on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return marker_file
        
        return None
    
    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse ebook files (TXT, PDF, EPUB)"""
        if not raw_file or not raw_file.exists():
            return []
        
        # Skip marker files
        if raw_file.name.startswith('download_complete'):
            return []
        
        try:
            data = []
            
            # Text file parsing
            if raw_file.suffix == '.txt':
                content = raw_file.read_text(encoding='utf-8', errors='ignore')
                
                # Clean up Gutenberg header/footer
                # Remove Project Gutenberg boilerplate
                lines = content.split('\n')
                start_idx = 0
                end_idx = len(lines)
                
                # Find actual content start (after Gutenberg header)
                for i, line in enumerate(lines):
                    if '*** START' in line.upper() or '***START' in line.upper():
                        start_idx = i + 1
                        break
                
                # Find content end (before Gutenberg footer)
                for i in range(len(lines) - 1, -1, -1):
                    if '*** END' in lines[i].upper() or '***END' in lines[i].upper():
                        end_idx = i
                        break
                
                content = '\n'.join(lines[start_idx:end_idx])
                
                # Extract metadata from filename or content
                title = raw_file.stem.replace('gutenberg_', '').replace('archive_', '')
                title = re.sub(r'_\d+$', '', title)  # Remove ID suffix
                
                entry = {
                    'title': title,
                    'content': content,
                    'source': 'Project Gutenberg' if 'gutenberg' in raw_file.name else 'Internet Archive',
                    'file_type': 'txt',
                    'file_path': str(raw_file)
                }
                data.append(entry)
            
            # PDF parsing (use existing PDF tools)
            elif raw_file.suffix == '.pdf':
                try:
                    from src.tools.pdf_tools import pdf_extract_text
                    content = pdf_extract_text(str(raw_file))
                    
                    if content:
                        title = raw_file.stem.replace('archive_', '')
                        entry = {
                            'title': title,
                            'content': content,
                            'source': 'Internet Archive',
                            'file_type': 'pdf',
                            'file_path': str(raw_file)
                        }
                        data.append(entry)
                except Exception as e:
                    print(f"    ⚠️  Error parsing PDF {raw_file.name}: {e}")
            
            # EPUB parsing (would need epub library)
            elif raw_file.suffix == '.epub':
                try:
                    import zipfile
                    from bs4 import BeautifulSoup
                    
                    with zipfile.ZipFile(raw_file, 'r') as epub:
                        # Read content.opf for metadata
                        content_opf = None
                        for file_info in epub.namelist():
                            if file_info.endswith('content.opf'):
                                content_opf = epub.read(file_info).decode('utf-8')
                                break
                        
                        # Extract text from HTML files
                        text_parts = []
                        for file_info in epub.namelist():
                            if file_info.endswith('.html') or file_info.endswith('.xhtml'):
                                html_content = epub.read(file_info).decode('utf-8')
                                soup = BeautifulSoup(html_content, 'html.parser')
                                text_parts.append(soup.get_text())
                        
                        content = '\n\n'.join(text_parts)
                        
                        if content:
                            title = raw_file.stem
                            entry = {
                                'title': title,
                                'content': content,
                                'source': 'Ebook',
                                'file_type': 'epub',
                                'file_path': str(raw_file)
                            }
                            data.append(entry)
                except Exception as e:
                    print(f"    ⚠️  Error parsing EPUB {raw_file.name}: {e}")
            
            return data
            
        except Exception as e:
            print(f"    ⚠️  Parse error for {raw_file.name}: {e}")
            return []
    
    def to_markdown(self, data: List[Dict[str, Any]]) -> str:
        """Convert ebook data to markdown"""
        if not data:
            return ""
        
        md = f"# {self.name}\n\n"
        md += f"**Source:** {self.source}\n"
        md += f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}\n"
        md += f"**Total Books:** {len(data)}\n\n"
        md += "---\n\n"
        
        for entry in data:
            title = entry.get('title', 'Unknown Title')
            content = entry.get('content', '')
            source = entry.get('source', 'Unknown')
            
            md += f"## {title}\n\n"
            md += f"**Source:** {source}\n"
            md += f"**File Type:** {entry.get('file_type', 'unknown')}\n\n"
            md += "---\n\n"
            
            # Add content (limit to first 10000 chars per book to avoid huge files)
            content_preview = content[:10000] if len(content) > 10000 else content
            md += content_preview
            
            if len(content) > 10000:
                md += f"\n\n*[Content truncated - full text available in source file]*\n"
            
            md += "\n\n---\n\n"
        
        return md
    
    def extract(self) -> Optional[Path]:
        """Main extraction workflow for ebooks"""
        print(f"  Extracting {self.name}...")
        
        # Download ebooks
        marker_file = self.download()
        if not marker_file:
            print(f"    ⚠️  Failed to download ebooks")
            return None
        
        # Parse all downloaded ebook files
        raw_files = list(self.raw_dir.glob("*.txt")) + list(self.raw_dir.glob("*.pdf")) + list(self.raw_dir.glob("*.epub"))
        raw_files = [f for f in raw_files if not f.name.startswith('download_complete')]
        
        if not raw_files:
            print(f"    ⚠️  No ebook files found to parse")
            return None
        
        print(f"    Parsing {len(raw_files)} ebook files...")
        all_data = []
        
        for raw_file in raw_files:
            file_data = self.parse(raw_file)
            all_data.extend(file_data)
        
        if not all_data:
            print(f"    ⚠️  Failed to parse ebooks")
            return None
        
        # Convert to markdown
        md_content = self.to_markdown(all_data)
        
        # Save markdown file
        md_file = self.md_dir / f"ebooks_collection_{datetime.now().strftime('%Y%m%d')}.md"
        md_file.write_text(md_content, encoding='utf-8')
        
        print(f"    ✓ Extracted {len(all_data)} ebooks to {md_file}")
        return md_file

