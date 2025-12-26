"""Improve HTML parsing for all extractors"""

import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent))

# Enhanced HTML parsing template
ENHANCED_PARSE_TEMPLATE = '''    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
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
                soup = BeautifulSoup(raw_file.read_bytes(), 'html.parser')
                
                # Strategy 1: Try pandas.read_html on all tables
                try:
                    from io import StringIO
                    html_str = str(soup)
                    tables = pd.read_html(StringIO(html_str))
                    for table in tables:
                        if len(table) > 0 and len(table.columns) > 1:
                            for _, row in table.iterrows():
                                entry = {{}}
                                for col in table.columns:
                                    val = row.get(col, '')
                                    if pd.notna(val) and str(val).strip():
                                        entry[col.lower().replace(' ', '_').replace('-', '_')] = str(val).strip()
                                if entry and len(entry) > 1:  # Must have at least 2 fields
                                    data.append(entry)
                except Exception as e:
                    pass
                
                # Strategy 2: Parse structured data (JSON-LD, microdata)
                try:
                    # Look for JSON-LD scripts
                    for script in soup.find_all('script', type='application/ld+json'):
                        import json
                        json_data = json.loads(script.string)
                        if isinstance(json_data, dict):
                            data.append(json_data)
                        elif isinstance(json_data, list):
                            data.extend(json_data)
                except:
                    pass
                
                # Strategy 3: Parse HTML tables manually
                if not data:
                    tables = soup.find_all('table')
                    for table in tables:
                        rows = table.find_all('tr')
                        if len(rows) > 1:
                            # Get headers from first row
                            headers = []
                            header_row = rows[0]
                            for th in header_row.find_all(['th', 'td']):
                                headers.append(th.get_text(strip=True).lower().replace(' ', '_'))
                            
                            # Parse data rows
                            for row in rows[1:]:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= len(headers) or len(cells) > 0:
                                    entry = {{}}
                                    for i, cell in enumerate(cells):
                                        text = cell.get_text(strip=True)
                                        if text:
                                            key = headers[i] if i < len(headers) else f'field_{{i}}'
                                            entry[key] = text
                                    if entry and len(entry) > 1:
                                        data.append(entry)
                
                # Strategy 4: Parse definition lists (dl/dt/dd)
                if not data:
                    dls = soup.find_all('dl')
                    for dl in dls:
                        entry = {{}}
                        dts = dl.find_all('dt')
                        dds = dl.find_all('dd')
                        for dt, dd in zip(dts, dds):
                            key = dt.get_text(strip=True).lower().replace(' ', '_')
                            value = dd.get_text(strip=True)
                            if key and value:
                                entry[key] = value
                        if entry:
                            data.append(entry)
                
                # Strategy 5: Parse structured divs with data attributes
                if not data:
                    data_divs = soup.find_all('div', {'data-': True}) or soup.find_all('div', class_=re.compile(r'item|entry|record|row'))
                    for div in data_divs:
                        entry = {{}}
                        # Look for labeled spans/divs
                        for label_elem in div.find_all(['span', 'div', 'p'], class_=re.compile(r'label|name|title')):
                            label = label_elem.get_text(strip=True).lower().replace(' ', '_')
                            value_elem = label_elem.find_next_sibling()
                            if value_elem:
                                value = value_elem.get_text(strip=True)
                                if label and value:
                                    entry[label] = value
                        if entry:
                            data.append(entry)
                
                # Strategy 6: Extract text content and look for patterns (CAS numbers, etc.)
                if not data:
                    text = soup.get_text()
                    # Look for CAS numbers (format: XXX-XX-X)
                    cas_pattern = r'\\b\\d{{2,7}}-\\d{{2}}-\\d\\b'
                    cas_matches = re.findall(cas_pattern, text)
                    if cas_matches:
                        for cas in cas_matches[:100]:  # Limit to 100
                            data.append({{'cas_number': cas, 'source': 'text_extraction'}})
            
            # Remove duplicates
            seen = set()
            unique_data = []
            for entry in data:
                # Create a key from entry values
                key = tuple(sorted(entry.items()))
                if key not in seen:
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
print("IMPROVING HTML PARSING FOR ALL EXTRACTORS")
print("=" * 70)
print()

# Find all extractor files
extractor_files = list(Path("src/extractors").rglob("*_extractor.py"))
extractor_files = [f for f in extractor_files if "base" not in str(f)]

print(f"Found {len(extractor_files)} extractor files")
print()

updated = 0

for extractor_file in extractor_files:
    try:
        content = extractor_file.read_text()
        
        # Check if it has the old parse method
        if 'def parse(self, raw_file: Path)' in content:
            # Extract database name from class
            class_match = re.search(r'class (\w+Extractor)', content)
            if class_match:
                class_name = class_match.group(1)
                # Try to extract name from __init__
                name_match = re.search(r'name="([^"]+)"', content)
                db_name = name_match.group(1) if name_match else class_name.replace('Extractor', '')
                
                # Replace parse method
                old_parse_pattern = r'def parse\(self, raw_file: Path\) -> List\[Dict\[str, Any\]\]:.*?return \[\]'
                new_parse = ENHANCED_PARSE_TEMPLATE.format(name=db_name)
                
                # Try to find and replace the parse method
                parse_start = content.find('def parse(self, raw_file: Path)')
                if parse_start != -1:
                    # Find the end of the method (next def or end of class)
                    parse_end = content.find('\n    def ', parse_start + 1)
                    if parse_end == -1:
                        parse_end = content.find('\nclass ', parse_start + 1)
                    if parse_end == -1:
                        parse_end = len(content)
                    
                    old_parse = content[parse_start:parse_end]
                    new_content = content[:parse_start] + new_parse + '\n' + content[parse_end:]
                    
                    extractor_file.write_text(new_content)
                    print(f"  ✓ Updated {extractor_file.name}")
                    updated += 1
    except Exception as e:
        print(f"  ⚠️  Error updating {extractor_file.name}: {e}")

print()
print("=" * 70)
print(f"COMPLETE: Updated {updated} extractors with enhanced HTML parsing")
print("=" * 70)

