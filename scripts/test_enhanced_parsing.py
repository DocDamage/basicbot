"""Test enhanced HTML parsing on downloaded files"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

# Test a few extractors
test_cases = [
    ("RoHS Database", "src.extractors.chemical_compliance.rohs_database_extractor", "RoHSDatabaseExtractor", "rohs_database"),
    ("FDA Orange Book", "src.extractors.healthcare.fda_orange_book_extractor", "FDAOrangeBookExtractor", "fda_orange_book"),
    ("NIOSH Pocket Guide", "src.extractors.safety_health.niosh_pocket_guide_extractor", "NIOSHPocketGuideExtractor", "niosh_pocket_guide"),
]

print("=" * 70)
print("TESTING ENHANCED HTML PARSING")
print("=" * 70)
print()

for name, module_name, class_name, dir_name in test_cases:
    try:
        module = __import__(module_name, fromlist=[class_name])
        extractor_class = getattr(module, class_name)
        extractor = extractor_class()
        
        # Find HTML file
        html_dir = Path(f"data/extracted_docs/compliance/{dir_name}/raw")
        html_files = list(html_dir.glob("*.html"))
        
        if html_files:
            html_file = html_files[0]
            print(f"Testing {name}...")
            print(f"  File: {html_file.name} ({html_file.stat().st_size / 1024:.1f} KB)")
            
            data = extractor.parse(html_file)
            print(f"  ✓ Parsed {len(data)} entries")
            
            if data:
                print(f"  Sample entry keys: {list(data[0].keys())[:5]}")
                if len(data) > 1:
                    print(f"  Sample values: {list(data[0].values())[:3]}")
            print()
        else:
            print(f"  ⚠️  No HTML file found for {name}")
            print()
    except Exception as e:
        print(f"  ⚠️  Error testing {name}: {e}")
        print()

print("=" * 70)
print("TESTING COMPLETE")
print("=" * 70)

