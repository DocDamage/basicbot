"""Fix missing imports in all extractors"""

from pathlib import Path
import re

extractor_files = list(Path("src/extractors").rglob("*_extractor.py"))
extractor_files = [f for f in extractor_files if "base" not in str(f)]

print(f"Fixing imports in {len(extractor_files)} extractors...")

for extractor_file in extractor_files:
    try:
        content = extractor_file.read_text()
        original = content
        
        # Add 'import re' if BeautifulSoup is used but re is not imported
        if 'BeautifulSoup' in content or 're.findall' in content or 're.' in content:
            if 'import re' not in content[:1000]:  # Check first 1000 chars for imports
                # Find where to insert (after other imports)
                lines = content.split('\n')
                import_end = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        import_end = i + 1
                    elif line.strip() and not line.strip().startswith('#') and import_end > 0:
                        break
                
                # Insert import re
                if import_end > 0:
                    lines.insert(import_end, 'import re')
                    content = '\n'.join(lines)
        
        # Add 'from bs4 import BeautifulSoup' if BeautifulSoup is used but not imported
        if 'BeautifulSoup' in content and 'from bs4 import BeautifulSoup' not in content and 'import BeautifulSoup' not in content:
            lines = content.split('\n')
            import_end = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    import_end = i + 1
                elif line.strip() and not line.strip().startswith('#') and import_end > 0:
                    break
            
            if import_end > 0:
                lines.insert(import_end, 'from bs4 import BeautifulSoup')
                content = '\n'.join(lines)
        
        if content != original:
            extractor_file.write_text(content)
            print(f"  ✓ Fixed {extractor_file.name}")
    except Exception as e:
        print(f"  ⚠️  Error fixing {extractor_file.name}: {e}")

print("Done!")

