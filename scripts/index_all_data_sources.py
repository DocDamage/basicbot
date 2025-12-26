"""Index all data sources for chatbot querying"""

import sys
import os
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bmad.framework import BMADFramework
from src.agents import DocumentAgent, RetrievalAgent
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("INDEXING ALL DATA SOURCES")
print("=" * 70)
print()

# Initialize framework
memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
framework = BMADFramework(memory_storage_path=memory_path)

document_agent = DocumentAgent(framework=framework)
retrieval_agent = RetrievalAgent(framework=framework)
framework.register_agent(document_agent)
framework.register_agent(retrieval_agent)

# Track what we're indexing
indexing_summary = {
    "markdown_files": 0,
    "prop65_files": 0,
    "celebrity_database": False,
    "wikiepstein_pdfs": False,
    "total_chunks": 0
}

# 1. Index all markdown files
print("1. INDEXING MARKDOWN FILES")
print("-" * 70)
extracted_dir = Path("data/extracted_docs")
if extracted_dir.exists():
    # Get all markdown files
    md_files = list(extracted_dir.rglob("*.md")) + list(extracted_dir.rglob("*.markdown"))
    
    # Exclude very large directories that might cause issues
    # Focus on important directories first
    important_dirs = [
        "compliance",
        "docs",
        "database_docs/docs/content",
        "database_docs/docs/platform"
    ]
    
    # Filter files
    important_files = []
    other_files = []
    
    for f in md_files:
        rel_path = str(f.relative_to(extracted_dir))
        if any(rel_path.startswith(d) for d in important_dirs):
            important_files.append(f)
        else:
            other_files.append(f)
    
    print(f"  Found {len(md_files)} total markdown files")
    print(f"  - Important directories: {len(important_files)} files")
    print(f"  - Other directories: {len(other_files)} files")
    print()
    
    # Process in batches
    batch_size = 100
    all_chunks = []
    
    # Process important files first
    print("  Processing important files first...")
    for i in range(0, len(important_files), batch_size):
        batch = important_files[i:i+batch_size]
        print(f"    Batch {i//batch_size + 1}/{(len(important_files) + batch_size - 1)//batch_size}: {len(batch)} files...")
        
        try:
            result = document_agent.process({"file_paths": [str(f) for f in batch]})
            chunks = result.get("chunks", [])
            all_chunks.extend(chunks)
            indexing_summary["markdown_files"] += result.get("files_processed", 0)
            print(f"      ✓ {result.get('files_processed', 0)} files, {len(chunks)} chunks")
        except Exception as e:
            print(f"      ⚠️  Error: {e}")
    
    # Index chunks
    if all_chunks:
        print(f"  Indexing {len(all_chunks)} chunks from markdown files...")
        retrieval_agent.index_chunks(all_chunks)
        indexing_summary["total_chunks"] += len(all_chunks)
        print(f"  ✓ Markdown files indexed")
    else:
        print("  ⚠️  No chunks created from markdown files")
else:
    print("  ⚠️  data/extracted_docs directory not found")

print()

# 2. Index Prop 65 files (if not already done)
print("2. INDEXING PROP 65 FILES")
print("-" * 70)
prop65_dir = Path("data/extracted_docs/compliance/prop65")
prop65_files = [
    prop65_dir / "chemicals.md",
    prop65_dir / "thresholds.md",
    prop65_dir / "warning_rules.md",
    prop65_dir / "changelog.md",
    prop65_dir / "sources.md"
]

existing_prop65 = [f for f in prop65_files if f.exists()]
if existing_prop65:
    print(f"  Found {len(existing_prop65)} Prop 65 files")
    try:
        result = document_agent.process({"file_paths": [str(f) for f in existing_prop65]})
        chunks = result.get("chunks", [])
        if chunks:
            retrieval_agent.index_chunks(chunks)
            indexing_summary["prop65_files"] = len(existing_prop65)
            indexing_summary["total_chunks"] += len(chunks)
            print(f"  ✓ Prop 65 files indexed ({len(chunks)} chunks)")
        else:
            print("  ⚠️  No chunks created from Prop 65 files")
    except Exception as e:
        print(f"  ⚠️  Error indexing Prop 65: {e}")
else:
    print("  ⚠️  Prop 65 files not found")

print()

# 3. Check celebrity database
print("3. CELEBRITY DATABASE")
print("-" * 70)
celeb_db = Path("data/epstein_files/celebrity-results.json")
if celeb_db.exists():
    print("  ✓ Celebrity database found")
    print("  Note: Celebrity database should be indexed separately using:")
    print("    python index_with_progress_save.py")
    indexing_summary["celebrity_database"] = True
else:
    print("  ⚠️  Celebrity database not found")

print()

# 4. Check WikiEpstein PDFs
print("4. WIKIEPSTEIN PDFs")
print("-" * 70)
wikiepstein_dir = Path("data/epstein_files/wikiepstein_extracted")
if wikiepstein_dir.exists():
    pdf_files = list(wikiepstein_dir.rglob("*.pdf"))
    print(f"  ✓ Found {len(pdf_files):,} PDF files")
    print("  Note: PDFs should be indexed separately using:")
    print("    python index_pdfs_properly.py")
    indexing_summary["wikiepstein_pdfs"] = len(pdf_files) > 0
else:
    print("  ⚠️  WikiEpstein directory not found")

print()

# 5. Summary
print("=" * 70)
print("INDEXING SUMMARY")
print("=" * 70)
print(f"  Markdown files indexed: {indexing_summary['markdown_files']}")
print(f"  Prop 65 files indexed: {indexing_summary['prop65_files']}")
print(f"  Total chunks created: {indexing_summary['total_chunks']:,}")
print()
print("  Additional data sources:")
print(f"    - Celebrity database: {'✓' if indexing_summary['celebrity_database'] else '⚠️  Not indexed'}")
print(f"    - WikiEpstein PDFs: {'✓' if indexing_summary['wikiepstein_pdfs'] else '⚠️  Not indexed'}")
print()
print("=" * 70)
print("INDEXING COMPLETE")
print("=" * 70)
print()
print("To index additional data sources:")
print("  - Celebrity database: python index_with_progress_save.py")
print("  - WikiEpstein PDFs: python index_pdfs_properly.py")
print()

