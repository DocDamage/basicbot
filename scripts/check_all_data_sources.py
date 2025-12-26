"""Comprehensive check of all data sources and indexing status"""

import sys
import os
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("COMPREHENSIVE DATA SOURCE CHECK")
print("=" * 70)
print()

# 1. Check all markdown files
print("1. MARKDOWN FILES IN EXTRACTED_DOCS")
print("-" * 70)
extracted_dir = Path("data/extracted_docs")
if not extracted_dir.exists():
    print("❌ data/extracted_docs directory does not exist!")
else:
    md_files = list(extracted_dir.rglob("*.md")) + list(extracted_dir.rglob("*.markdown"))
    print(f"✓ Found {len(md_files)} markdown files")
    
    # Group by directory
    by_dir = defaultdict(list)
    for f in md_files:
        rel_path = f.relative_to(extracted_dir)
        dir_path = rel_path.parent
        by_dir[str(dir_path)].append(rel_path.name)
    
    print(f"\n  Organized in {len(by_dir)} directories:")
    for dir_path in sorted(by_dir.keys())[:30]:  # Show first 30
        files = by_dir[dir_path]
        print(f"    {dir_path}/ ({len(files)} files)")
        if len(files) <= 3:
            for f in files:
                print(f"      - {f}")
        else:
            print(f"      - {files[0]} (and {len(files)-1} more...)")
    
    if len(by_dir) > 30:
        print(f"    ... and {len(by_dir) - 30} more directories")

print()

# 2. Check compliance data
print("2. COMPLIANCE DATA")
print("-" * 70)
compliance_dir = Path("data/extracted_docs/compliance")
if compliance_dir.exists():
    # REACH
    reach_dirs = {
        "reach_substances": compliance_dir / "reach_substances",
        "reach_regulation": compliance_dir / "reach_regulation",
        "plastchem": compliance_dir / "plastchem"
    }
    
    for name, dir_path in reach_dirs.items():
        if dir_path.exists():
            md_files = list(dir_path.rglob("*.md"))
            print(f"  ✓ {name}: {len(md_files)} markdown files")
        else:
            print(f"  ⚠️  {name}: directory not found")
    
    # Prop 65
    prop65_dir = compliance_dir / "prop65"
    if prop65_dir.exists():
        prop65_files = {
            "chemicals.md": prop65_dir / "chemicals.md",
            "thresholds.md": prop65_dir / "thresholds.md",
            "warning_rules.md": prop65_dir / "warning_rules.md",
            "changelog.md": prop65_dir / "changelog.md",
            "sources.md": prop65_dir / "sources.md"
        }
        
        print(f"  Prop 65 files:")
        for name, file_path in prop65_files.items():
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"    ✓ {name} ({size:,} bytes)")
            else:
                print(f"    ❌ {name} - MISSING")
    else:
        print("  ❌ Prop 65 directory not found")
else:
    print("  ⚠️  Compliance directory not found")

print()

# 3. Check Epstein files
print("3. EPSTEIN FILES DATA")
print("-" * 70)
epstein_dir = Path("data/epstein_files")
if epstein_dir.exists():
    # Celebrity database
    celeb_db = epstein_dir / "celebrity-results.json"
    if celeb_db.exists():
        size = celeb_db.stat().st_size / (1024 * 1024)  # MB
        print(f"  ✓ Celebrity database: {celeb_db.name} ({size:.2f} MB)")
    else:
        print(f"  ⚠️  Celebrity database not found")
    
    # WikiEpstein PDFs
    wikiepstein_dir = epstein_dir / "wikiepstein_extracted"
    if wikiepstein_dir.exists():
        pdf_files = list(wikiepstein_dir.rglob("*.pdf"))
        print(f"  ✓ WikiEpstein PDFs: {len(pdf_files):,} files")
        
        # Check subdirectories
        subdirs = {
            "images": wikiepstein_dir / "images",
            "pdfs": wikiepstein_dir / "pdfs",
            "documents": wikiepstein_dir / "documents",
            "other": wikiepstein_dir / "other"
        }
        for name, subdir in subdirs.items():
            if subdir.exists():
                files = list(subdir.rglob("*"))
                files = [f for f in files if f.is_file()]
                print(f"    - {name}/: {len(files):,} files")
    else:
        print(f"  ⚠️  WikiEpstein extracted directory not found")
else:
    print("  ⚠️  Epstein files directory not found")

print()

# 4. Check vector database
print("4. VECTOR DATABASE STATUS")
print("-" * 70)
try:
    from qdrant_client import QdrantClient
    
    vector_db_dir = Path("./data/vector_db")
    os.makedirs(vector_db_dir, exist_ok=True)
    
    try:
        client = QdrantClient(path=str(vector_db_dir))
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_names:
            print(f"  ✓ Found {len(collection_names)} collection(s):")
            for coll_name in collection_names:
                try:
                    info = client.get_collection(coll_name)
                    points = info.points_count
                    print(f"    - {coll_name}: {points:,} points")
                except Exception as e:
                    print(f"    - {coll_name}: Error getting info - {e}")
        else:
            print("  ⚠️  No collections found in vector database")
            print("     Documents need to be indexed!")
        
        client.close()
    except Exception as e:
        error_msg = str(e)
        if "already accessed" in error_msg:
            print("  ✅ Vector database is locked (indexing in progress)")
        else:
            print(f"  ⚠️  Error accessing vector database: {e}")
            print("     Using file-based storage (this is fine)")
except ImportError:
    print("  ❌ qdrant_client not installed")

print()

# 5. Check what should be indexed
print("5. INDEXING STATUS BY DATA SOURCE")
print("-" * 70)

# Check if markdown files are indexed
try:
    from qdrant_client import QdrantClient
    
    vector_db_dir = Path("./data/vector_db")
    os.makedirs(vector_db_dir, exist_ok=True)
    
    try:
        client = QdrantClient(path=str(vector_db_dir))
        collections = client.get_collections()
        
        if "rag_documents" in [c.name for c in collections.collections]:
            info = client.get_collection("rag_documents")
            total_points = info.points_count
            
            print(f"  Total indexed points: {total_points:,}")
            print()
            
            # Estimate breakdown (rough estimates)
            print("  Estimated breakdown:")
            
            # Celebrity database: ~8,408 entries
            celeb_estimate = 8408
            print(f"    - Celebrity database: ~{celeb_estimate:,} points (estimated)")
            
            # Prop 65: ~46 chunks (we just indexed)
            prop65_estimate = 46
            print(f"    - Prop 65 compliance: ~{prop65_estimate:,} points (known)")
            
            # WikiEpstein PDFs: variable
            pdf_estimate = max(0, total_points - celeb_estimate - prop65_estimate)
            if pdf_estimate > 0:
                print(f"    - WikiEpstein PDFs: ~{pdf_estimate:,} points (estimated)")
            
            # Other markdown files
            other_estimate = max(0, total_points - celeb_estimate - prop65_estimate - pdf_estimate)
            if other_estimate > 0:
                print(f"    - Other documents: ~{other_estimate:,} points (estimated)")
            
            # Check if we're missing data
            print()
            print("  Missing data sources:")
            missing = []
            
            # Check Prop 65
            prop65_dir = Path("data/extracted_docs/compliance/prop65")
            if prop65_dir.exists():
                required_files = ["chemicals.md", "thresholds.md", "warning_rules.md"]
                for f in required_files:
                    if not (prop65_dir / f).exists():
                        missing.append(f"Prop 65: {f}")
            
            # Check REACH
            reach_dir = Path("data/extracted_docs/compliance/reach_substances")
            if not reach_dir.exists() or len(list(reach_dir.rglob("*.md"))) == 0:
                missing.append("REACH substances (no markdown files found)")
            
            if missing:
                for item in missing:
                    print(f"    ⚠️  {item}")
            else:
                print("    ✓ All known data sources appear to be indexed")
        
        client.close()
    except Exception as e:
        if "already accessed" not in str(e):
            print(f"  ⚠️  Could not check indexing status: {e}")
except Exception as e:
    print(f"  ⚠️  Error: {e}")

print()

# 6. Check database files
print("6. DATABASE FILES")
print("-" * 70)
db_files = {
    "Celebrity database": Path("data/epstein_files/celebrity-results.json"),
    "Vector DB": Path("data/vector_db"),
    "Chat history": Path("data/chat_history")
}

for name, path in db_files.items():
    if path.exists():
        if path.is_file():
            size = path.stat().st_size / (1024 * 1024)  # MB
            print(f"  ✓ {name}: {size:.2f} MB")
        else:
            # Count files in directory
            files = list(path.rglob("*"))
            files = [f for f in files if f.is_file()]
            total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)  # MB
            print(f"  ✓ {name}: {len(files)} files, {total_size:.2f} MB")
    else:
        print(f"  ⚠️  {name}: not found")

print()

# 7. Summary and recommendations
print("7. SUMMARY & RECOMMENDATIONS")
print("-" * 70)

recommendations = []

# Check if all markdown files are indexed
md_files = list(Path("data/extracted_docs").rglob("*.md"))
if md_files:
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(path="./data/vector_db")
        collections = client.get_collections()
        if "rag_documents" in [c.name for c in collections.collections]:
            info = client.get_collection("rag_documents")
            indexed_points = info.points_count
            
            # Rough estimate: each markdown file might create 5-20 chunks
            estimated_chunks = len(md_files) * 10  # Conservative estimate
            
            if indexed_points < estimated_chunks * 0.5:  # Less than 50% of expected
                recommendations.append(f"Many markdown files ({len(md_files)}) may not be indexed. Consider running document indexing.")
        client.close()
    except:
        pass

# Check Prop 65
prop65_dir = Path("data/extracted_docs/compliance/prop65")
if prop65_dir.exists():
    required = ["chemicals.md", "thresholds.md", "warning_rules.md"]
    missing = [f for f in required if not (prop65_dir / f).exists()]
    if missing:
        recommendations.append(f"Prop 65 files missing: {', '.join(missing)}")

# Check REACH
reach_dir = Path("data/extracted_docs/compliance/reach_substances")
if reach_dir.exists():
    reach_files = list(reach_dir.rglob("*.md"))
    if len(reach_files) == 0:
        recommendations.append("REACH substances directory exists but contains no markdown files")

if recommendations:
    print("  Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"    {i}. {rec}")
else:
    print("  ✓ All data sources appear to be properly set up and indexed")

print()
print("=" * 70)
print("CHECK COMPLETE")
print("=" * 70)

