"""Sec Edgar Database Extractor"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extractors.base_extractor import BaseExtractor

class SECEDGARDatabaseExtractor(BaseExtractor):
    """Extract SEC EDGAR Database data"""

    def __init__(self):
        super().__init__(
            name="SEC EDGAR Database",
            source="SEC",
            url="https://www.sec.gov/edgar/searchedgar/companysearch.html"
        )

    def download(self) -> Optional[Path]:
        """Download SEC EDGAR Database data using API"""
        print(f"    Downloading from {self.url}...")
        
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            })
            
            # Try SEC EDGAR API first
            # SEC EDGAR API: https://www.sec.gov/edgar/sec-api-documentation
            # Company tickers endpoint
            api_urls = [
                "https://www.sec.gov/files/company_tickers.json",  # Company tickers
                "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-K&dateb=&owner=include&count=100&output=atom",  # Recent filings
            ]
            
            for api_url in api_urls:
                try:
                    response = session.get(api_url, timeout=30)
                    if response.status_code == 200:
                        # Check if JSON
                        if 'json' in response.headers.get('content-type', '').lower():
                            raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
                            raw_file.write_text(response.text, encoding='utf-8')
                            print(f"    ✓ Downloaded JSON from API to {raw_file.name}")
                            return raw_file
                        else:
                            # XML or other format
                            ext = '.xml' if 'xml' in response.headers.get('content-type', '').lower() else '.txt'
                            raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}{ext}"
                            raw_file.write_bytes(response.content)
                            print(f"    ✓ Downloaded from API to {raw_file.name}")
                            return raw_file
                except Exception as e:
                    continue
            
            # Fallback to web scraping
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
                print(f"    Note: SEC EDGAR API available at https://www.sec.gov/edgar/sec-api-documentation")
                return raw_file
            
            return None
        except Exception as e:
            print(f"    ⚠️  Download error: {e}")
            return None

    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse SEC EDGAR Database data (JSON, XML, CSV, HTML)"""
        if not raw_file or not raw_file.exists():
            return []
        
        try:
            data = []
            
            # JSON parsing (from API)
            if raw_file.suffix == '.json':
                import json
                json_data = json.loads(raw_file.read_text(encoding='utf-8'))
                
                if isinstance(json_data, dict):
                    # Company tickers format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
                    if all(isinstance(k, str) and k.isdigit() for k in json_data.keys()):
                        for entry in json_data.values():
                            if isinstance(entry, dict):
                                data.append(entry)
                    else:
                        # Other JSON formats
                        data.append(json_data)
                elif isinstance(json_data, list):
                    data.extend(json_data)
            
            # XML parsing (from API feeds)
            elif raw_file.suffix == '.xml':
                try:
                    import xml.etree.ElementTree as ET
                    tree = ET.parse(raw_file)
                    root = tree.getroot()
                    
                    # Parse common SEC EDGAR XML formats
                    for entry_elem in root.findall('.//entry') or root.findall('.//company') or root.findall('.//filing'):
                        entry = {}
                        for child in entry_elem:
                            entry[child.tag.replace('{http://www.w3.org/2005/Atom}', '')] = child.text
                        if entry:
                            data.append(entry)
                except:
                    pass
            
            # CSV parsing
            elif raw_file.suffix == '.csv':
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
            
            # HTML parsing (enhanced)
            elif raw_file.suffix == '.html':
                html_content = raw_file.read_text(encoding='utf-8', errors='ignore')
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Try pandas.read_html
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
                except:
                    pass
            
            print(f"    ✓ Parsed {len(data)} entries")
            return data
        except Exception as e:
            print(f"    ⚠️  Parse error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def to_markdown(self, data: List[Dict[str, Any]]) -> str:
        """Convert to markdown"""
        md = f"# {{self.name}}\n\n"
        md += f"**Source:** {{self.source}}\n"
        md += f"**URL:** {{self.url}}\n"
        md += f"**Last Updated:** {{datetime.now().strftime('%Y-%m-%d')}}\n"
        md += f"**Total Entries:** {{len(data)}}\n\n"
        md += "---\n\n"
        md += "## Entries\n\n"
        
        for entry in data[:1000]:
            name = entry.get('name', entry.get('chemical_name', entry.get('substance_name', 'Unknown')))
            md += f"### {{name}}\n\n"
            for key, value in entry.items():
                if key not in ['name', 'chemical_name', 'substance_name'] and value:
                    md += f"- **{{key.replace('_', ' ').title()}}:** {{value}}\n"
            md += "\n"
        
        if len(data) > 1000:
            md += f"\n*... and {{len(data) - 1000}} more entries*\n"
        
        return md
