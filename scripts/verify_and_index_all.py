"""Verify all data sources and ensure they're indexed and queryable"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bmad.framework import BMADFramework
from src.agents import DocumentAgent, RetrievalAgent
from src.tools.vector_tools import initialize_collection, search_vectors
from src.tools.embedding_tools import get_embedding_dimension
from src.config import get_settings
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

print("=" * 70)
print("VERIFYING AND INDEXING ALL DATA SOURCES")
print("=" * 70)
print()

# 1. Check vector database status
print("1. CHECKING VECTOR DATABASE")
print("-" * 70)
vector_db_dir = Path("./data/vector_db")
os.makedirs(vector_db_dir, exist_ok=True)

try:
    client = QdrantClient(path=str(vector_db_dir))
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]
    
    if "rag_documents" in collection_names:
        info = client.get_collection("rag_documents")
        points = info.points_count
        print(f"  ✓ Collection 'rag_documents' exists: {points:,} points")
    else:
        print("  ⚠️  Collection 'rag_documents' not found - needs indexing")
    
    client.close()
except Exception as e:
    error_msg = str(e)
    if "already accessed" in error_msg:
        print("  ✅ Vector database is locked (indexing in progress)")
        print("     Wait for indexing to complete, then run this script again")
        sys.exit(0)
    else:
        print(f"  ⚠️  Error: {e}")
        print("     Will initialize new collection")

print()

# 2. Initialize framework
print("2. INITIALIZING FRAMEWORK")
print("-" * 70)
memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
framework = BMADFramework(memory_storage_path=memory_path)

document_agent = DocumentAgent(framework=framework)
retrieval_agent = RetrievalAgent(framework=framework)
framework.register_agent(document_agent)
framework.register_agent(retrieval_agent)

# Initialize vector store
settings = get_settings()
embedding_model = settings.get_embedding_model()
vector_size = get_embedding_dimension(embedding_model)
collection_name = os.getenv("QDRANT_COLLECTION_NAME", "rag_documents")

try:
    initialize_collection(collection_name, vector_size)
    print(f"  ✓ Vector store initialized: {collection_name}")
except Exception as e:
    print(f"  ⚠️  Note: {e} (using file-based storage)")

print()

# 3. Check what needs indexing
print("3. CHECKING DATA SOURCES")
print("-" * 70)

# Markdown files
extracted_dir = Path("data/extracted_docs")
md_files = []
if extracted_dir.exists():
    md_files = list(extracted_dir.rglob("*.md")) + list(extracted_dir.rglob("*.markdown"))
    print(f"  ✓ Found {len(md_files):,} markdown files")

# Prop 65
prop65_dir = Path("data/extracted_docs/compliance/prop65")
prop65_files = []
if prop65_dir.exists():
    prop65_files = [
        prop65_dir / "chemicals.md",
        prop65_dir / "thresholds.md",
        prop65_dir / "warning_rules.md",
        prop65_dir / "changelog.md",
        prop65_dir / "sources.md"
    ]
    prop65_files = [f for f in prop65_files if f.exists()]
    print(f"  ✓ Found {len(prop65_files)} Prop 65 files")

# Celebrity database
celeb_db = Path("data/epstein_files/celebrity-results.json")
has_celeb = celeb_db.exists()
if has_celeb:
    print(f"  ✓ Celebrity database found")

# WikiEpstein PDFs
wikiepstein_dir = Path("data/epstein_files/wikiepstein_extracted")
pdf_files = []
if wikiepstein_dir.exists():
    pdf_files = list(wikiepstein_dir.rglob("*.pdf"))
    print(f"  ✓ Found {len(pdf_files):,} WikiEpstein PDF files")

print()

# 4. Index Prop 65 files (small, quick to index)
if prop65_files:
    print("4. INDEXING PROP 65 FILES")
    print("-" * 70)
    try:
        result = document_agent.process({"file_paths": [str(f) for f in prop65_files]})
        chunks = result.get("chunks", [])
        if chunks:
            retrieval_agent.index_chunks(chunks)
            print(f"  ✓ Prop 65 files indexed: {len(chunks)} chunks")
        else:
            print(f"  ⚠️  No chunks created from Prop 65 files")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
    print()

# 5. Index markdown files (in batches)
if md_files:
    print("5. INDEXING MARKDOWN FILES")
    print("-" * 70)
    print(f"  Processing {len(md_files):,} files in batches...")
    print("  (This will take a while - progress will be shown)")
    print()
    
    # Process in batches of 50
    batch_size = 50
    total_processed = 0
    total_chunks = 0
    
    for i in range(0, len(md_files), batch_size):
        batch = md_files[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(md_files) + batch_size - 1) // batch_size
        
        print(f"  Batch {batch_num}/{total_batches}: Processing {len(batch)} files...", end="", flush=True)
        
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
    
    print(f"  ✓ Markdown files indexed: {total_processed} files, {total_chunks:,} chunks")
    print()

# 6. Verify indexing
print("6. VERIFYING INDEXING")
print("-" * 70)
try:
    client = QdrantClient(path=str(vector_db_dir))
    collections = client.get_collections()
    
    if "rag_documents" in [c.name for c in collections.collections]:
        info = client.get_collection("rag_documents")
        points = info.points_count
        
        print(f"  ✓ Collection 'rag_documents': {points:,} points indexed")
        
        # Test query
        print("  Testing query capability...")
        try:
            results = search_vectors("test query", top_k=1)
            if results:
                print(f"  ✓ Query test successful - {len(results)} results")
            else:
                print("  ⚠️  Query returned no results (may be normal if collection is new)")
        except Exception as e:
            print(f"  ⚠️  Query test error: {e}")
    else:
        print("  ❌ Collection 'rag_documents' still not found")
    
    client.close()
except Exception as e:
    print(f"  ⚠️  Error verifying: {e}")

print()

# 7. Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("Data sources status:")
print(f"  - Markdown files: {len(md_files):,} files")
print(f"  - Prop 65 files: {len(prop65_files)} files")
print(f"  - Celebrity database: {'✓' if has_celeb else '⚠️  Not found'}")
print(f"  - WikiEpstein PDFs: {len(pdf_files):,} files")
print()
print("Note: Celebrity database and PDFs need separate indexing:")
print("  - Celebrity database: python index_with_progress_save.py")
print("  - WikiEpstein PDFs: python index_pdfs_properly.py")
print()
print("=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)

