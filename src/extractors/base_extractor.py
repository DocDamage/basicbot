"""Base extraction template for industry databases"""

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
