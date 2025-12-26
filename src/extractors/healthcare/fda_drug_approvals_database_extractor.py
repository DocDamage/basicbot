"""Fda Drug Approvals Database Extractor"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime
import requests
import pandas as pd
import json
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extractors.base_extractor import BaseExtractor

class FDADrugApprovalsDatabaseExtractor(BaseExtractor):
    """Extract FDA Drug Approvals Database data"""

    def __init__(self):
        super().__init__(
            name="FDA Drug Approvals Database",
            source="FDA",
            url="https://www.fda.gov/drugs/drug-approvals-and-databases"
        )

    def download(self) -> Optional[Path]:
        """Download FDA Drug Approvals Database data using OpenFDA API"""
        print(f"    Downloading from {self.url}...")
        
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            })
            
            # Try OpenFDA API first
            # OpenFDA API: https://open.fda.gov/
            # Drug Approvals endpoint
            api_urls = [
                "https://api.fda.gov/drug/event.json?limit=100",  # Drug events (sample)
                "https://api.fda.gov/drug/label.json?limit=100",  # Drug labels (sample)
                "https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files",  # Drugs@FDA data files
            ]
            
            for api_url in api_urls:
                try:
                    response = session.get(api_url, timeout=30)
                    if response.status_code == 200:
                        if 'json' in response.headers.get('content-type', '').lower():
                            raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
                            raw_file.write_text(response.text, encoding='utf-8')
                            print(f"    ✓ Downloaded JSON from OpenFDA API to {raw_file.name}")
                            return raw_file
                        else:
                            # HTML page with download links
                            soup = BeautifulSoup(response.content, 'html.parser')
                            for link in soup.find_all('a', href=True):
                                href = link['href']
                                if any(ext in href.lower() for ext in ['.csv', '.xlsx', '.xls', '.zip', 'download']):
                                    if href.startswith('/'):
                                        base_url = '/'.join(api_url.split('/')[:3])
                                        href = f"{base_url}{href}"
                                    elif not href.startswith('http'):
                                        continue
                                    
                                    try:
                                        file_response = session.get(href, timeout=60)
                                        if file_response.status_code == 200:
                                            ext = '.csv' if '.csv' in href.lower() else ('.xlsx' if '.xlsx' in href.lower() else ('.zip' if '.zip' in href.lower() else '.html'))
                                            raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}{ext}"
                                            raw_file.write_bytes(file_response.content)
                                            print(f"    ✓ Downloaded to {raw_file.name}")
                                            return raw_file
                                    except:
                                        continue
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
                print(f"    Note: OpenFDA API available at https://open.fda.gov/")
                return raw_file
            
            return None
        except Exception as e:
            print(f"    ⚠️  Download error: {e}")
            return None

    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse FDA Drug Approvals Database data (JSON, CSV, Excel, HTML)"""
        if not raw_file or not raw_file.exists():
            return []
        
        try:
            data = []
            
            # JSON parsing (from OpenFDA API)
            if raw_file.suffix == '.json':
                json_data = json.loads(raw_file.read_text(encoding='utf-8'))
                
                if isinstance(json_data, dict):
                    # OpenFDA format: {"meta": {...}, "results": [...]}
                    if 'results' in json_data:
                        data.extend(json_data['results'])
                    elif 'data' in json_data:
                        data.extend(json_data['data'])
                    else:
                        data.append(json_data)
                elif isinstance(json_data, list):
                    data.extend(json_data)
            
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
            
            elif raw_file.suffix == '.html':
                soup = BeautifulSoup(raw_file.read_bytes(), 'html.parser')
                tables = soup.find_all('table')
                if tables:
                    try:
                        df = pd.read_html(str(tables[0]))[0]
                        for _, row in df.iterrows():
                            entry = {}
                            for col in df.columns:
                                val = row.get(col, '')
                                if pd.notna(val):
                                    entry[col.lower().replace(' ', '_')] = str(val).strip()
                            if entry:
                                data.append(entry)
                    except:
                        pass
            
            print(f"    ✓ Parsed {len(data)} entries")
            return data
        except Exception as e:
            print(f"    ⚠️  Parse error: {e}")
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
