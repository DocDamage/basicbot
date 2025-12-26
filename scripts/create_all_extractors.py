"""Create extractors for all databases"""

import json
from pathlib import Path

# Load plan
with open("DATABASE_INTEGRATION_PLAN.json", 'r') as f:
    plan = json.load(f)

extraction_dir = Path("src/extractors")
extraction_dir.mkdir(parents=True, exist_ok=True)

# Base extractor template
base_template = '''"""Extractor for {name} database"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.extractors.base_extractor import BaseExtractor

class {class_name}(BaseExtractor):
    """Extract {name} data"""
    
    def __init__(self):
        super().__init__(
            name="{name}",
            source="{source}",
            url="{url}"
        )
    
    def download(self) -> Optional[Path]:
        """Download {name} data"""
        # TODO: Implement download logic
        # Check for API, CSV download, or web scraping
        print(f"    Downloading from {{self.url}}...")
        # Example implementations:
        # - API: requests.get(url).json()
        # - CSV: requests.get(url).content -> save to raw_dir
        # - Web scraping: BeautifulSoup, Selenium, etc.
        return None
    
    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse {name} data"""
        # TODO: Implement parsing logic based on data_format
        # Formats: CSV, Excel, JSON, XML, PDF, HTML
        return []
    
    def to_markdown(self, data: List[Dict[str, Any]]) -> str:
        """Convert to markdown"""
        md = f"# {{self.name}}\\n\\n"
        md += f"**Source:** {{self.source}}\\n"
        md += f"**URL:** {{self.url}}\\n"
        md += f"**Last Updated:** {{datetime.now().strftime('%Y-%m-%d')}}\\n\\n"
        md += "## Entries\\n\\n"
        
        for entry in data:
            md += f"### {{entry.get('name', 'Unknown')}}\\n"
            for key, value in entry.items():
                if key != 'name':
                    md += f"- **{{key}}:** {{value}}\\n"
            md += "\\n"
        
        return md
'''

print("=" * 70)
print("CREATING EXTRACTORS FOR ALL DATABASES")
print("=" * 70)
print()

all_dbs = plan['high_priority'] + plan['medium_priority'] + plan['low_priority']
created = 0
skipped = 0

for db in all_dbs:
    # Generate class name and file name
    name = db['name']
    class_name = name.replace(' ', '').replace('-', '').replace('_', '') + "Extractor"
    file_name = name.lower().replace(' ', '_').replace('-', '_') + "_extractor.py"
    category = db['category']
    
    # Create category directory
    category_dir = extraction_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)
    (category_dir / "__init__.py").touch()
    
    extractor_file = category_dir / file_name
    
    # Skip if already exists
    if extractor_file.exists():
        print(f"  ⏭️  {name} - already exists")
        skipped += 1
        continue
    
    # Generate extractor code
    extractor_code = base_template.format(
        name=name,
        class_name=class_name,
        source=db['source'],
        url=db['url']
    )
    
    extractor_file.write_text(extractor_code)
    print(f"  ✓ {name} - {file_name}")
    created += 1

print()
print("=" * 70)
print(f"COMPLETE: Created {created} extractors, skipped {skipped} existing")
print("=" * 70)
print()
print("Next steps:")
print("  1. Implement download() and parse() methods for each extractor")
print("  2. Test extractors individually")
print("  3. Run: python extract_and_index_all_databases.py")
print()

