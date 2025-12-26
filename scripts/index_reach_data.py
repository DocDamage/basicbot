"""Index REACH data - handles pipeline output or existing files"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bmad.framework import BMADFramework
from src.agents import DocumentAgent, RetrievalAgent
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("INDEXING REACH DATA")
print("=" * 70)
print()

# 1. Check for REACH pipeline output
print("1. CHECKING FOR REACH DATA")
print("-" * 70)

reach_files = []

# Check pipeline output
pipeline_output = Path("data/reach_pipeline/output/md")
if pipeline_output.exists():
    pipeline_files = list(pipeline_output.rglob("*.md"))
    if pipeline_files:
        print(f"  ✓ Found {len(pipeline_files)} files from REACH pipeline")
        reach_files.extend(pipeline_files)

# Check existing compliance directory
compliance_reach = Path("data/extracted_docs/compliance/reach_substances")
if compliance_reach.exists():
    existing_files = list(compliance_reach.rglob("*.md"))
    if existing_files:
        print(f"  ✓ Found {len(existing_files)} existing REACH files")
        reach_files.extend(existing_files)

# Check reach_regulation directory
reach_regulation = Path("data/extracted_docs/compliance/reach_regulation")
if reach_regulation.exists():
    regulation_files = list(reach_regulation.rglob("*.md"))
    if regulation_files:
        print(f"  ✓ Found {len(regulation_files)} REACH regulation files")
        reach_files.extend(regulation_files)

if not reach_files:
    print("  ⚠️  No REACH markdown files found")
    print()
    print("  To generate REACH data:")
    print("    1. Run the REACH pipeline: python run_reach_pipeline_and_index.py")
    print("    2. Note: ECHA may block automated scraping (403 error)")
    print("    3. You may need to manually download data from ECHA")
    print("    4. Place markdown files in: data/extracted_docs/compliance/reach_substances/")
    print()
    print("  REACH data sources:")
    print("    - SVHC Candidate List: https://echa.europa.eu/candidate-list-table")
    print("    - Annex XIV Authorization: https://echa.europa.eu/authorisation-list")
    print("    - Annex XVII Restrictions: https://echa.europa.eu/substances-restricted-under-reach")
    print("    - CL Inventory: https://echa.europa.eu/regulations/clp/cl-inventory")
    sys.exit(0)

# Remove duplicates
reach_files = list(set(reach_files))
print(f"\n  Total unique REACH files: {len(reach_files)}")
print()

# 2. Copy pipeline files to compliance directory if needed
print("2. ORGANIZING REACH FILES")
print("-" * 70)

compliance_reach.mkdir(parents=True, exist_ok=True)
final_files = []

for src_file in reach_files:
    # If from pipeline, copy to compliance directory
    if "reach_pipeline" in str(src_file):
        if "per_substance" in str(src_file):
            # Keep per-substance structure
            rel_path = src_file.relative_to(pipeline_output)
            dst_file = compliance_reach / "per_substance" / rel_path
        else:
            # Copy consolidated files
            dst_file = compliance_reach / src_file.name
        
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not dst_file.exists():
            import shutil
            shutil.copy2(src_file, dst_file)
            print(f"  ✓ Copied {src_file.name}")
        
        final_files.append(dst_file)
    else:
        # Already in compliance directory
        final_files.append(src_file)

print(f"  ✓ {len(final_files)} files ready for indexing")
print()

# 3. Index REACH files
print("3. INDEXING REACH FILES")
print("-" * 70)

try:
    memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
    framework = BMADFramework(memory_storage_path=memory_path)
    
    document_agent = DocumentAgent(framework=framework)
    retrieval_agent = RetrievalAgent(framework=framework)
    framework.register_agent(document_agent)
    framework.register_agent(retrieval_agent)
    
    # Process in batches
    batch_size = 50
    total_chunks = 0
    total_processed = 0
    
    print(f"  Processing {len(final_files)} files in batches of {batch_size}...")
    print()
    
    for i in range(0, len(final_files), batch_size):
        batch = final_files[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(final_files) + batch_size - 1) // batch_size
        
        print(f"  Batch {batch_num}/{total_batches}: {len(batch)} files...", end="", flush=True)
        
        try:
            result = document_agent.process({"file_paths": [str(f) for f in batch]})
            chunks = result.get("chunks", [])
            if chunks:
                retrieval_agent.index_chunks(chunks)
                total_chunks += len(chunks)
            total_processed += result.get("files_processed", 0)
            print(f" ✓ ({result.get('files_processed', 0)} files, {len(chunks)} chunks)")
        except Exception as e:
            print(f" ⚠️  Error: {e}")
    
    print()
    print(f"  ✓ REACH data indexed: {total_processed} files, {total_chunks:,} chunks")
    
except Exception as e:
    print(f"  ⚠️  Error indexing: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("REACH INDEXING COMPLETE")
print("=" * 70)
print()
print("REACH data is now queryable in your chatbot!")
print("You can ask questions like:")
print("  - 'What substances are on the SVHC candidate list?'")
print("  - 'Show me REACH Annex XIV authorization requirements'")
print("  - 'What are the REACH restrictions for phthalates?'")
print("  - 'Is CAS 117-81-7 on the REACH SVHC list?'")
print()

