"""Usda Food Composition Database Extractor"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime
import requests
import pandas as pd
import json
import zipfile
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extractors.base_extractor import BaseExtractor

class USDAFoodCompositionDatabaseExtractor(BaseExtractor):
    """Extract USDA Food Composition Database data"""

    def __init__(self):
        super().__init__(
            name="USDA Food Composition Database",
            source="USDA",
            url="https://fdc.nal.usda.gov/"
        )

    def download(self) -> Optional[Path]:
        """Download USDA Food Composition Database data using API"""
        print(f"    Downloading from {self.url}...")
        
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            })
            
            # USDA FoodData Central API: https://fdc.nal.usda.gov/api-guide.html
            # Try API first - get a sample of foods
            api_urls = [
                "https://api.nal.usda.gov/fdc/v1/foods/list?dataType=Foundation&pageSize=100&api_key=demo",  # Demo key
                "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2023-10-26.zip",  # Full dataset
            ]
            
            for api_url in api_urls:
                try:
                    response = session.get(api_url, timeout=60)
                    if response.status_code == 200:
                        if 'json' in response.headers.get('content-type', '').lower():
                            raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
                            raw_file.write_text(response.text, encoding='utf-8')
                            print(f"    ✓ Downloaded JSON from API to {raw_file.name}")
                            return raw_file
                        elif 'zip' in api_url.lower():
                            raw_file = self.raw_dir / f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.zip"
                            raw_file.write_bytes(response.content)
                            print(f"    ✓ Downloaded ZIP from API to {raw_file.name}")
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
                    if any(ext in href.lower() for ext in ['.csv', '.xlsx', '.xls', 'download', 'api', 'json']):
                        if href.startswith('/'):
                            base_url = '/'.join(self.url.split('/')[:3])
                            href = f"{base_url}{href}"
                        elif not href.startswith('http'):
                            continue
                        
                        try:
                            file_response = session.get(href, timeout=60)
                            if file_response.status_code == 200:
                                ext = '.csv' if '.csv' in href.lower() else ('.xlsx' if '.xlsx' in href.lower() else ('.json' if '.json' in href.lower() else '.html'))
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
                print(f"    Note: USDA API available at https://fdc.nal.usda.gov/api-guide.html")
                return raw_file
            
            return None
        except Exception as e:
            print(f"    ⚠️  Download error: {e}")
            return None

    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse USDA Food Composition Database data (JSON, ZIP, CSV, Excel, HTML)"""
        if not raw_file or not raw_file.exists():
            return []
        
        try:
            data = []
            
            # JSON parsing (from API)
            if raw_file.suffix == '.json':
                json_data = json.loads(raw_file.read_text(encoding='utf-8'))
                
                if isinstance(json_data, dict) and 'foods' in json_data:
                    # API response format
                    data.extend(json_data['foods'])
                elif isinstance(json_data, list):
                    data.extend(json_data)
                elif isinstance(json_data, dict):
                    data.append(json_data)
            
            # ZIP file (extract and parse JSON)
            elif raw_file.suffix == '.zip':
                with zipfile.ZipFile(raw_file, 'r') as zip_ref:
                    for file_info in zip_ref.namelist():
                        if file_info.endswith('.json'):
                            try:
                                json_content = zip_ref.read(file_info).decode('utf-8')
                                json_data = json.loads(json_content)
                                if isinstance(json_data, list):
                                    data.extend(json_data)
                                elif isinstance(json_data, dict):
                                    if 'foods' in json_data:
                                        data.extend(json_data['foods'])
                                    else:
                                        data.append(json_data)
                            except Exception as e:
                                print(f"    ⚠️  Error parsing {file_info}: {e}")
                                continue
            
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
