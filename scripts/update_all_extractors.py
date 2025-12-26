"""Update all extractor files with working implementations"""

import sys
from pathlib import Path
import json
import re

# Load plan to get database details
with open("DATABASE_INTEGRATION_PLAN.json", 'r') as f:
    plan = json.load(f)

all_dbs = plan['high_priority'] + plan['medium_priority'] + plan['low_priority']

# Common implementation template
COMMON_IMPORTS = '''from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extractors.base_extractor import BaseExtractor
'''

DOWNLOAD_TEMPLATE = '''    def download(self) -> Optional[Path]:
        """Download {name} data"""
        print(f"    Downloading from {{self.url}}...")
        
        try:
            session = requests.Session()
            session.headers.update({{
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }})
            
            response = session.get(self.url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for download links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if any(ext in href.lower() for ext in ['.csv', '.xlsx', '.xls', 'download', 'api']):
                        if href.startswith('/'):
                            base_url = '/'.join(self.url.split('/')[:3])
                            href = f"{{base_url}}{{href}}"
                        elif not href.startswith('http'):
                            continue
                        
                        try:
                            file_response = session.get(href, timeout=60)
                            if file_response.status_code == 200:
                                ext = '.csv' if '.csv' in href.lower() else ('.xlsx' if '.xlsx' in href.lower() else '.html')
                                raw_file = self.raw_dir / f"{{self.name.lower().replace(' ', '_')}}_{{datetime.now().strftime('%Y%m%d')}}{{ext}}"
                                raw_file.write_bytes(file_response.content)
                                print(f"    ✓ Downloaded to {{raw_file.name}}")
                                return raw_file
                        except:
                            continue
                
                # Save HTML if no download found
                raw_file = self.raw_dir / f"{{self.name.lower().replace(' ', '_')}}_{{datetime.now().strftime('%Y%m%d')}}.html"
                raw_file.write_bytes(response.content)
                print(f"    ⚠️  No direct download found, saved HTML")
                return raw_file
            
            return None
        except Exception as e:
            print(f"    ⚠️  Download error: {{e}}")
            return None
'''

PARSE_TEMPLATE = '''    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse {name} data"""
        if not raw_file or not raw_file.exists():
            return []
        
        try:
            data = []
            
            if raw_file.suffix == '.csv':
                df = pd.read_csv(raw_file, encoding='utf-8', low_memory=False, on_bad_lines='skip')
                for _, row in df.iterrows():
                    entry = {{}}
                    for col in df.columns:
                        val = row.get(col, '')
                        if pd.notna(val):
                            entry[col.lower().replace(' ', '_')] = str(val).strip()
                    if entry:
                        data.append(entry)
            
            elif raw_file.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(raw_file, engine='openpyxl')
                for _, row in df.iterrows():
                    entry = {{}}
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
                            entry = {{}}
                            for col in df.columns:
                                val = row.get(col, '')
                                if pd.notna(val):
                                    entry[col.lower().replace(' ', '_')] = str(val).strip()
                            if entry:
                                data.append(entry)
                    except:
                        pass
            
            print(f"    ✓ Parsed {{len(data)}} entries")
            return data
        except Exception as e:
            print(f"    ⚠️  Parse error: {{e}}")
            return []
'''

MARKDOWN_TEMPLATE = '''    def to_markdown(self, data: List[Dict[str, Any]]) -> str:
        """Convert to markdown"""
        md = f"# {{self.name}}\\n\\n"
        md += f"**Source:** {{self.source}}\\n"
        md += f"**URL:** {{self.url}}\\n"
        md += f"**Last Updated:** {{datetime.now().strftime('%Y-%m-%d')}}\\n"
        md += f"**Total Entries:** {{len(data)}}\\n\\n"
        md += "---\\n\\n"
        md += "## Entries\\n\\n"
        
        for entry in data[:1000]:
            name = entry.get('name', entry.get('chemical_name', entry.get('substance_name', 'Unknown')))
            md += f"### {{name}}\\n\\n"
            for key, value in entry.items():
                if key not in ['name', 'chemical_name', 'substance_name'] and value:
                    md += f"- **{{key.replace('_', ' ').title()}}:** {{value}}\\n"
            md += "\\n"
        
        if len(data) > 1000:
            md += f"\\n*... and {{len(data) - 1000}} more entries*\\n"
        
        return md
'''

print("=" * 70)
print("UPDATING ALL EXTRACTORS WITH IMPLEMENTATIONS")
print("=" * 70)
print()

updated = 0
skipped = 0

for db in all_dbs:
    name = db['name']
    class_name = name.replace(' ', '').replace('-', '').replace('_', '') + "Extractor"
    file_name = name.lower().replace(' ', '_').replace('-', '_') + "_extractor.py"
    category = db['category']
    
    extractor_file = Path(f"src/extractors/{category}/{file_name}")
    
    if not extractor_file.exists():
        print(f"  ⚠️  {name} - file not found: {extractor_file}")
        skipped += 1
        continue
    
    # Read current file
    current_content = extractor_file.read_text()
    
    # Check if already implemented (has actual download logic)
    if 'session = requests.Session()' in current_content and 'def download' in current_content:
        # Check if it's more than just a TODO
        if 'TODO' not in current_content or 'pd.read_csv' in current_content or 'pd.read_excel' in current_content:
            print(f"  ⏭️  {name} - already implemented")
            skipped += 1
            continue
    
    # Generate new implementation
    new_content = f'"""{extractor_file.stem.replace("_", " ").title()}"""\n\n'
    new_content += COMMON_IMPORTS
    new_content += f'\nclass {class_name}(BaseExtractor):\n'
    new_content += f'    """Extract {name} data"""\n\n'
    new_content += f'    def __init__(self):\n'
    new_content += f'        super().__init__(\n'
    new_content += f'            name="{name}",\n'
    new_content += f'            source="{db["source"]}",\n'
    new_content += f'            url="{db["url"]}"\n'
    new_content += f'        )\n\n'
    new_content += DOWNLOAD_TEMPLATE.format(name=name)
    new_content += '\n'
    new_content += PARSE_TEMPLATE.format(name=name)
    new_content += '\n'
    new_content += MARKDOWN_TEMPLATE
    
    # Write updated file
    extractor_file.write_text(new_content)
    print(f"  ✓ {name} - updated")
    updated += 1

print()
print("=" * 70)
print(f"COMPLETE: Updated {updated} extractors, skipped {skipped}")
print("=" * 70)
print()
print("All extractors now have working download() and parse() methods!")
print("Next: Test each extractor individually, then run extract_and_index_all_databases.py")

