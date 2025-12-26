"""Rohs Database Extractor"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime
import requests
import pandas as pd
import re
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extractors.base_extractor import BaseExtractor

class RoHSDatabaseExtractor(BaseExtractor):
    """Extract RoHS Database data"""

    def __init__(self):
        super().__init__(
            name="RoHS Database",
            source="EU",
            url="https://ec.europa.eu/environment/waste/rohs_eee/"
        )

    def download(self) -> Optional[Path]:
        """Download RoHS Database data"""
        print(f"    Downloading from {self.url}...")
        
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            response = session.get(self.url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for download links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if any(ext in href.lower() for ext in ['.csv', '.xlsx', '.xls', 'download', 'api']):
                        if href.startswith('/'):
                            base_url = '/'.join(self.url.split('/')[:3])
                            href = f"{base_url}{href}"
                        elif not href.startswith('http'):
                            continue
                        
                        try:
                            file_response = session.get(href, timeout=60)
                            if file_response.status_code == 200:
                                ext = '.csv' if '.csv' in href.lower() else ('.xlsx' if '.xlsx' in href.lower() else '.html')
                                raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}{ext}"
                                raw_file.write_bytes(file_response.content)
                                print(f"    ✓ Downloaded to {raw_file.name}")
                                return raw_file
                        except:
                            continue
                
                # Save HTML if no download found
                raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.html"
                raw_file.write_bytes(response.content)
                print(f"    ⚠️  No direct download found, saved HTML")
                return raw_file
            
            return None
        except Exception as e:
            print(f"    ⚠️  Download error: {e}")
            return None

    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse RoHS Database data with enhanced HTML parsing"""
        if not raw_file or not raw_file.exists():
            return []
        
        try:
            data = []
            
            # CSV parsing
            if raw_file.suffix == '.csv':
                df = pd.read_csv(raw_file, encoding='utf-8', low_memory=False, on_bad_lines='skip')
                for _, row in df.iterrows():
                    entry = {}
                    for col in df.columns:
                        val = row.get(col, '')
                        if pd.notna(val):
                            entry[col.lower().replace(' ', '_')] = str(val).strip()
                    if entry:
                        data.append(entry)
            
            # Excel parsing
            elif raw_file.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(raw_file, engine='openpyxl')
                for _, row in df.iterrows():
                    entry = {}
                    for col in df.columns:
                        val = row.get(col, '')
                        if pd.notna(val):
                            entry[col.lower().replace(' ', '_')] = str(val).strip()
                    if entry:
                        data.append(entry)
            
            # Enhanced HTML parsing
            elif raw_file.suffix == '.html':
                html_content = raw_file.read_text(encoding='utf-8', errors='ignore')
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Strategy 1: Try pandas.read_html on entire HTML (like REACH pipeline)
                try:
                    from io import StringIO
                    tables = pd.read_html(StringIO(html_content))
                    if tables:
                        # Use the largest table (most likely to contain data)
                        df = max(tables, key=lambda t: t.shape[0] if t.shape[0] > 0 else 0)
                        if len(df) > 0:
                            for _, row in df.iterrows():
                                entry = {}
                                for col in df.columns:
                                    val = row.get(col, '')
                                    if pd.notna(val) and str(val).strip() and str(val).lower() not in ['nan', 'none', '']:
                                        entry[str(col).lower().replace(' ', '_').replace('-', '_')] = str(val).strip()
                                if entry and len(entry) > 1:  # Must have at least 2 fields
                                    data.append(entry)
                except Exception as e:
                    pass
                
                # Strategy 2: Parse HTML tables manually if pandas failed
                if not data:
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')
                        if len(rows) > 1:
                            # Get headers from first row
                            headers = []
                            header_row = rows[0]
                            for th in header_row.find_all(['th', 'td']):
                                header_text = th.get_text(strip=True)
                                if header_text:
                                    headers.append(header_text.lower().replace(' ', '_').replace('-', '_'))
                            
                            # Parse data rows
                            for row in rows[1:]:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) > 0:
                                    entry = {}
                                    for i, cell in enumerate(cells):
                                        text = cell.get_text(strip=True)
                                        if text and text.lower() not in ['nan', 'none', '']:
                                            key = headers[i] if i < len(headers) else f'field_{i}'
                                            entry[key] = text
                                    if entry and len(entry) > 1:
                                        data.append(entry)
                
                # Strategy 3: Look for JSON-LD structured data
                if not data:
                    try:
                        import json
                        for script in soup.find_all('script', type='application/ld+json'):
                            json_data = json.loads(script.string)
                            if isinstance(json_data, dict):
                                data.append(json_data)
                            elif isinstance(json_data, list):
                                data.extend(json_data)
                    except:
                        pass
                
                # Strategy 4: Extract CAS numbers and chemical names from text
                if not data:
                    text = soup.get_text()
                    # Look for CAS numbers (format: XXX-XX-X)
                    cas_pattern = r'\b\d{2,7}-\d{2}-\d\b'
                    cas_matches = re.findall(cas_pattern, text)
                    if cas_matches:
                        for cas in set(cas_matches[:100]):  # Limit to 100 unique
                            data.append({'cas_number': cas, 'source': 'text_extraction'})
            
            # Remove duplicates based on content
            seen = set()
            unique_data = []
            for entry in data:
                # Create a key from entry values
                key = tuple(sorted((k, str(v)) for k, v in entry.items() if v))
                if key not in seen and len(key) > 0:
                    seen.add(key)
                    unique_data.append(entry)
            
            print(f"    ✓ Parsed {len(unique_data)} entries")
            return unique_data
            
        except Exception as e:
            print(f"    ⚠️  Parse error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def to_markdown(self, data: List[Dict[str, Any]]) -> str:
        """Convert to markdown"""
        md = f"# {self.name}\n\n"
        md += f"**Source:** {self.source}\n"
        md += f"**URL:** {self.url}\n"
        md += f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}\n"
        md += f"**Total Entries:** {len(data)}\n\n"
        md += "---\n\n"
        md += "## Entries\n\n"
        
        for entry in data[:1000]:
            name = entry.get('name', entry.get('chemical_name', entry.get('substance_name', 'Unknown')))
            md += f"### {name}\n\n"
            for key, value in entry.items():
                if key not in ['name', 'chemical_name', 'substance_name'] and value:
                    md += f"- **{key.replace('_', ' ').title()}:** {value}\n"
            md += "\n"
        
        if len(data) > 1000:
            md += f"\n*... and {len(data) - 1000} more entries*\n"
        
        return md
