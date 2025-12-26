"""Extractor for RoHS database"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime
import re
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extractors.base_extractor import BaseExtractor

class RoHSExtractor(BaseExtractor):
    """Extract RoHS data"""
    
    def __init__(self):
        super().__init__(
            name="RoHS",
            source="Unknown",
            url="https://ec.europa.eu/environment/waste/rohs_eee/"
        )
    
    def download(self) -> Optional[Path]:
        """Download RoHS data"""
        # TODO: Implement download logic
        # Check for API, CSV download, or web scraping
        print(f"    Downloading from {self.url}...")
        return None
    
    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse RoHS data with enhanced HTML parsing"""
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
                
                # Strategy 1: Try pandas.read_html on entire HTML
                try:
                    from io import StringIO
                    tables = pd.read_html(StringIO(html_content))
                    if tables:
                        df = max(tables, key=lambda t: t.shape[0] if t.shape[0] > 0 else 0)
                        if len(df) > 0:
                            for _, row in df.iterrows():
                                entry = {}
                                for col in df.columns:
                                    val = row.get(col, '')
                                    if pd.notna(val) and str(val).strip() and str(val).lower() not in ['nan', 'none', '']:
                                        entry[str(col).lower().replace(' ', '_').replace('-', '_')] = str(val).strip()
                                if entry and len(entry) > 1:
                                    data.append(entry)
                except Exception:
                    pass
                
                # Strategy 2: Parse HTML tables manually
                if not data:
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')
                        if len(rows) > 1:
                            headers = []
                            header_row = rows[0]
                            for th in header_row.find_all(['th', 'td']):
                                header_text = th.get_text(strip=True)
                                if header_text:
                                    headers.append(header_text.lower().replace(' ', '_').replace('-', '_'))
                            
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
                    except Exception:
                        pass
                
                # Strategy 4: Extract CAS numbers from text
                if not data:
                    text = soup.get_text()
                    cas_pattern = r'\b\d{2,7}-\d{2}-\d\b'
                    cas_matches = re.findall(cas_pattern, text)
                    if cas_matches:
                        for cas in set(cas_matches[:100]):
                            data.append({'cas_number': cas, 'source': 'text_extraction'})
            
            # Remove duplicates
            seen = set()
            unique_data = []
            for entry in data:
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
        md += f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        md += "## Entries\n\n"
        
        for entry in data:
            md += f"### {entry.get('name', 'Unknown')}\n"
            for key, value in entry.items():
                if key != 'name':
                    md += f"- **{key}:** {value}\n"
            md += "\n"
        
        return md
