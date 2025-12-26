"""Update all extractors with enhanced HTML parsing"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent))

# Enhanced parse method template
ENHANCED_PARSE = '''    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse {name} data with enhanced HTML parsing"""
        if not raw_file or not raw_file.exists():
            return []
        
        try:
            data = []
            
            # CSV parsing
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
            
            # Excel parsing
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
                                entry = {{}}
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
                                    entry = {{}}
                                    for i, cell in enumerate(cells):
                                        text = cell.get_text(strip=True)
                                        if text and text.lower() not in ['nan', 'none', '']:
                                            key = headers[i] if i < len(headers) else f'field_{{i}}'
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
                    cas_pattern = r'\\b\\d{{2,7}}-\\d{{2}}-\\d\\b'
                    cas_matches = re.findall(cas_pattern, text)
                    if cas_matches:
                        for cas in set(cas_matches[:100]):
                            data.append({{'cas_number': cas, 'source': 'text_extraction'}})
            
            # Remove duplicates
            seen = set()
            unique_data = []
            for entry in data:
                key = tuple(sorted((k, str(v)) for k, v in entry.items() if v))
                if key not in seen and len(key) > 0:
                    seen.add(key)
                    unique_data.append(entry)
            
            print(f"    ✓ Parsed {{len(unique_data)}} entries")
            return unique_data
            
        except Exception as e:
            print(f"    ⚠️  Parse error: {{e}}")
            import traceback
            traceback.print_exc()
            return []
'''

print("=" * 70)
print("UPDATING ALL EXTRACTORS WITH ENHANCED HTML PARSING")
print("=" * 70)
print()

extractor_files = list(Path("src/extractors").rglob("*_extractor.py"))
extractor_files = [f for f in extractor_files if "base" not in str(f)]

print(f"Found {len(extractor_files)} extractor files")
print()

updated = 0

for extractor_file in extractor_files:
    try:
        content = extractor_file.read_text()
        
        # Check if it has a parse method
        if 'def parse(self, raw_file: Path)' in content:
            # Extract database name
            name_match = re.search(r'name="([^"]+)"', content)
            db_name = name_match.group(1) if name_match else extractor_file.stem.replace('_extractor', '')
            
            # Find parse method boundaries
            parse_start = content.find('    def parse(self, raw_file: Path)')
            if parse_start != -1:
                # Find end of method (next method or class)
                parse_end = content.find('\n    def ', parse_start + 1)
                if parse_end == -1:
                    parse_end = content.find('\nclass ', parse_start + 1)
                if parse_end == -1:
                    parse_end = len(content)
                
                # Replace the method
                new_parse = ENHANCED_PARSE.format(name=db_name)
                new_content = content[:parse_start] + new_parse + '\n' + content[parse_end:]
                
                # Ensure 'import re' is present
                if 'import re' not in new_content and 'BeautifulSoup' in new_content:
                    # Find import section
                    import_section = new_content.find('from bs4 import BeautifulSoup')
                    if import_section != -1:
                        new_content = new_content[:import_section] + 'import re\n' + new_content[import_section:]
                
                extractor_file.write_text(new_content)
                print(f"  ✓ Updated {extractor_file.name}")
                updated += 1
    except Exception as e:
        print(f"  ⚠️  Error updating {extractor_file.name}: {e}")

print()
print("=" * 70)
print(f"COMPLETE: Updated {updated} extractors")
print("=" * 70)

