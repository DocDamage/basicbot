"""Master script to integrate all industry databases"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any
import subprocess

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("COMPREHENSIVE DATABASE INTEGRATION")
print("=" * 70)
print()

# Load integration plan
plan_file = Path("DATABASE_INTEGRATION_PLAN.json")
if not plan_file.exists():
    print("❌ Integration plan not found. Creating it...")
    subprocess.run([sys.executable, "create_database_integration_plan.py"], check=False)
    if not plan_file.exists():
        print("❌ Failed to create integration plan")
        sys.exit(1)

with open(plan_file, 'r') as f:
    plan = json.load(f)

# Create directory structure
base_dir = Path("data/extracted_docs/compliance")
base_dir.mkdir(parents=True, exist_ok=True)

# Import extraction modules
extraction_modules = {}

print("1. SETTING UP EXTRACTION MODULES")
print("-" * 70)

# Create extraction module directory
extraction_dir = Path("src/extractors")
extraction_dir.mkdir(parents=True, exist_ok=True)
(extraction_dir / "__init__.py").touch()

print("  ✓ Extraction directory created")
print()

# 2. Create extraction scripts for each category
print("2. CREATING EXTRACTION SCRIPTS")
print("-" * 70)

categories = {
    "chemical_compliance": ["TSCA", "RoHS", "GHS"],
    "healthcare": ["FDA_Orange_Book", "FDA_Drug_Approvals", "FDA_Medical_Devices"],
    "safety_health": ["OSHA", "NIOSH", "ACGIH"],
    "financial": ["SEC_EDGAR"],
    "intellectual_property": ["USPTO"],
    "standards": ["ISO", "IEC"],
    "food_agriculture": ["FDA_Food_Code", "USDA_Food"],
    "transportation": ["DOT_Hazmat"]
}

for category, extractors in categories.items():
    category_dir = extraction_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)
    (category_dir / "__init__.py").touch()
    print(f"  ✓ Created {category}/ directory")

print()

# 3. Process all databases
print("3. PROCESSING DATABASES")
print("-" * 70)

all_databases = plan['high_priority'] + plan['medium_priority'] + plan['low_priority']
print(f"  Total databases to integrate: {len(all_databases)}")
print()

# Group by priority
for priority in ['high', 'medium', 'low']:
    dbs = plan[f'{priority}_priority']
    print(f"  {priority.upper()} Priority: {len(dbs)} databases")
    for db in dbs:
        print(f"    - {db['name']} ({db['category']})")

print()

# 4. Create master extraction template
print("4. CREATING EXTRACTION TEMPLATES")
print("-" * 70)

template_code = '''"""Base extraction template for industry databases"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import json
from datetime import datetime

# Add project root
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

class BaseExtractor:
    """Base class for database extractors"""
    
    def __init__(self, name: str, source: str, url: str, output_dir: Optional[Path] = None):
        self.name = name
        self.source = source
        self.url = url
        self.output_dir = output_dir or Path("data/extracted_docs/compliance") / self.name.lower().replace(" ", "_")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.output_dir / "raw"
        self.raw_dir.mkdir(exist_ok=True)
        self.md_dir = self.output_dir / "md"
        self.md_dir.mkdir(exist_ok=True)
    
    def download(self) -> Optional[Path]:
        """Download raw data from source"""
        raise NotImplementedError
    
    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse raw data into structured format"""
        raise NotImplementedError
    
    def to_markdown(self, data: List[Dict[str, Any]]) -> str:
        """Convert structured data to markdown"""
        raise NotImplementedError
    
    def extract(self) -> Path:
        """Main extraction workflow"""
        print(f"  Extracting {self.name}...")
        
        # Download
        raw_file = self.download()
        if not raw_file:
            print(f"    ⚠️  Failed to download {self.name}")
            return None
        
        # Parse
        data = self.parse(raw_file)
        if not data:
            print(f"    ⚠️  Failed to parse {self.name}")
            return None
        
        # Convert to markdown
        md_content = self.to_markdown(data)
        
        # Save
        md_file = self.md_dir / f"{self.name.lower().replace(' ', '_')}.md"
        md_file.write_text(md_content, encoding='utf-8')
        
        print(f"    ✓ Extracted {len(data)} entries to {md_file}")
        return md_file
'''

template_file = extraction_dir / "base_extractor.py"
template_file.write_text(template_code)
print("  ✓ Created base extraction template")

print()

# 5. Create specific extractors
print("5. CREATING DATABASE-SPECIFIC EXTRACTORS")
print("-" * 70)

# This will be done incrementally - create framework first
extractor_scripts = {}

# High priority extractors
high_priority_extractors = {
    "TSCA": {
        "module": "chemical_compliance.tsca_extractor",
        "class": "TSCAExtractor",
        "url": "https://www.epa.gov/tsca-inventory",
        "format": "CSV/Excel"
    },
    "RoHS": {
        "module": "chemical_compliance.rohs_extractor",
        "class": "RoHSExtractor",
        "url": "https://ec.europa.eu/environment/waste/rohs_eee/",
        "format": "PDF/Excel"
    },
    "FDA_Orange_Book": {
        "module": "healthcare.fda_orange_book_extractor",
        "class": "FDAOrangeBookExtractor",
        "url": "https://www.fda.gov/drugs/drug-approvals-and-databases/approved-drug-products-therapeutic-equivalence-evaluations-orange-book",
        "format": "Excel/API"
    },
    "OSHA": {
        "module": "safety_health.osha_extractor",
        "class": "OSHAExtractor",
        "url": "https://www.osha.gov/laws-regs/regulations/standardnumber",
        "format": "HTML/PDF"
    },
    "NIOSH": {
        "module": "safety_health.niosh_extractor",
        "class": "NIOSHExtractor",
        "url": "https://www.cdc.gov/niosh/npg/",
        "format": "Web database"
    }
}

print(f"  Creating {len(high_priority_extractors)} high-priority extractors...")

for name, config in high_priority_extractors.items():
    category = config["module"].split(".")[0]
    extractor_file = extraction_dir / category / f"{name.lower()}_extractor.py"
    
    class_name = config["class"]
    extractor_code = f'''"""Extractor for {name} database"""

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
            source="{config.get('source', 'Unknown')}",
            url="{config['url']}"
        )
    
    def download(self) -> Optional[Path]:
        """Download {name} data"""
        # TODO: Implement download logic
        # Check for API, CSV download, or web scraping
        print(f"    Downloading from {{self.url}}...")
        return None
    
    def parse(self, raw_file: Path) -> List[Dict[str, Any]]:
        """Parse {name} data"""
        # TODO: Implement parsing logic
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
    
    extractor_file.write_text(extractor_code)
    print(f"    ✓ Created {name} extractor")

print()

# 6. Create master orchestrator
print("6. CREATING MASTER ORCHESTRATOR")
print("-" * 70)

orchestrator_code = f'''"""Master orchestrator for all database extractions"""

import sys
from pathlib import Path
import json
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent))

from src.bmad.framework import BMADFramework
from src.agents import DocumentAgent, RetrievalAgent
from dotenv import load_dotenv
import os

load_dotenv()

def extract_all_databases():
    """Extract all databases"""
    print("=" * 70)
    print("EXTRACTING ALL DATABASES")
    print("=" * 70)
    print()
    
    # Load plan
    with open("DATABASE_INTEGRATION_PLAN.json", 'r') as f:
        plan = json.load(f)
    
    all_dbs = plan['high_priority'] + plan['medium_priority'] + plan['low_priority']
    
    extracted_files = []
    
    # Import and run extractors
    for priority in ['high', 'medium', 'low']:
        dbs = plan[f'{{priority}}_priority']
        print(f"{{priority.upper()}} PRIORITY DATABASES")
        print("-" * 70)
        
        for db in dbs:
            try:
                # Map database name to extractor
                extractor_name = db['name'].replace(' ', '_').replace('-', '_')
                category = db['category']
                
                # Try to import extractor
                try:
                    module_name = f"src.extractors.{{category}}.{{extractor_name.lower()}}_extractor"
                    module = __import__(module_name, fromlist=[extractor_name])
                    extractor_class = getattr(module, f"{{extractor_name}}Extractor")
                    
                    # Run extractor
                    extractor = extractor_class()
                    md_file = extractor.extract()
                    
                    if md_file:
                        extracted_files.append(md_file)
                except (ImportError, AttributeError):
                    print(f"  ⚠️  {{db['name']}}: Extractor not yet implemented")
                    print(f"     URL: {{db['url']}}")
                    print(f"     Format: {{db['data_format']}}")
            except Exception as e:
                print(f"  ⚠️  Error processing {{db['name']}}: {{e}}")
        
        print()
    
    return extracted_files

def index_extracted_files(files: List[Path]):
    """Index extracted markdown files"""
    if not files:
        print("No files to index")
        return
    
    print("=" * 70)
    print("INDEXING EXTRACTED FILES")
    print("=" * 70)
    print()
    
    memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
    framework = BMADFramework(memory_storage_path=memory_path)
    
    document_agent = DocumentAgent(framework=framework)
    retrieval_agent = RetrievalAgent(framework=framework)
    framework.register_agent(document_agent)
    framework.register_agent(retrieval_agent)
    
    # Process in batches
    batch_size = 50
    total_chunks = 0
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        print(f"  Processing batch {{i//batch_size + 1}}/{{(len(files) + batch_size - 1)//batch_size}}...", end="", flush=True)
        
        try:
            result = document_agent.process({{"file_paths": [str(f) for f in batch]}})
            chunks = result.get("chunks", [])
            if chunks:
                retrieval_agent.index_chunks(chunks)
                total_chunks += len(chunks)
            print(f" ✓ ({{len(chunks)}} chunks)")
        except Exception as e:
            print(f" ⚠️  Error: {{e}}")
    
    print()
    print(f"✓ Indexed {{total_chunks:,}} chunks from {{len(files)}} files")

if __name__ == "__main__":
    files = extract_all_databases()
    index_extracted_files(files)
'''

orchestrator_file = Path("extract_and_index_all_databases.py")
orchestrator_file.write_text(orchestrator_code)
print("  ✓ Created master orchestrator")

print()

# 7. Create quick-start guide
print("7. CREATING DOCUMENTATION")
print("-" * 70)

quick_start = f'''# Quick Start: Integrating All Databases

## Overview

This system integrates {len(all_databases)} databases from multiple industries into your chatbot.

## Current Status

- **High Priority:** {len(plan['high_priority'])} databases
- **Medium Priority:** {len(plan['medium_priority'])} databases  
- **Low Priority:** {len(plan['low_priority'])} databases

## Quick Start

### 1. Run All Extractions

```bash
python extract_and_index_all_databases.py
```

This will:
- Extract data from all databases
- Convert to markdown format
- Index in vector database

### 2. Run Individual Extractors

Each database has its own extractor in `src/extractors/`:

```python
from src.extractors.chemical_compliance.tsca_extractor import TSCAExtractor

extractor = TSCAExtractor()
md_file = extractor.extract()
```

### 3. Manual Integration

For databases that require manual setup:

1. Download data from source URL
2. Place in `data/extracted_docs/compliance/[database_name]/raw/`
3. Run extractor or convert manually to markdown
4. Index using: `python index_reach_data.py` (or similar)

## Database Status

### Implemented Extractors

- (To be filled as extractors are implemented)

### Pending Implementation

All databases need extractor implementation. See `INDUSTRY_DATABASES_RESEARCH.md` for details.

## Next Steps

1. **Implement High Priority Extractors First**
   - TSCA Chemical Inventory
   - RoHS Database
   - FDA Orange Book
   - OSHA CFR Database
   - NIOSH Pocket Guide

2. **Test Each Extractor**
   - Verify data download
   - Check markdown conversion
   - Test indexing

3. **Add Specialized Search Tools**
   - CAS number search (chemical databases)
   - Drug name search (FDA databases)
   - Regulation number search (OSHA, etc.)

## Notes

- Some databases may require API keys or authentication
- Some may block automated scraping (like ECHA)
- Manual downloads may be required for some sources
- Update mechanisms should be implemented for regularly updated databases
'''

quick_start_file = Path("DATABASE_INTEGRATION_QUICKSTART.md")
quick_start_file.write_text(quick_start)
print("  ✓ Created quick-start guide")

print()

print("=" * 70)
print("INTEGRATION FRAMEWORK CREATED")
print("=" * 70)
print()
print(f"✓ Created extraction framework for {len(all_databases)} databases")
print(f"✓ Created {len(high_priority_extractors)} high-priority extractor templates")
print(f"✓ Created master orchestrator script")
print(f"✓ Created documentation")
print()
print("Next steps:")
print("  1. Implement extractors for each database (see src/extractors/)")
print("  2. Test each extractor individually")
print("  3. Run: python extract_and_index_all_databases.py")
print("  4. Add specialized search tools as needed")
print()
print("Files created:")
print("  - src/extractors/ - Extraction modules")
print("  - extract_and_index_all_databases.py - Master orchestrator")
print("  - DATABASE_INTEGRATION_QUICKSTART.md - Quick start guide")
print()

