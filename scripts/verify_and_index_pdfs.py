"""Verify celebrity DB is indexed, then start PDF indexing with visible output"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient

print("=" * 70)
print("VERIFICATION AND PDF INDEXING")
print("=" * 70)
print()

# First, check if celebrity database was indexed
vector_db_dir = "./data/vector_db"
os.makedirs(vector_db_dir, exist_ok=True)

try:
    client = QdrantClient(path=vector_db_dir)
    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]
    
    if 'rag_documents' in collection_names:
        info = client.get_collection('rag_documents')
        points = info.points_count
        print(f"✓ Celebrity database indexed: {points:,} points in collection")
        
        if points >= 8408:
            print(f"  ✅ Celebrity database complete!")
        else:
            print(f"  ⚠️  Celebrity database incomplete ({points:,}/8,408)")
    else:
        print("❌ No collection found - celebrity database may not be indexed")
        print("   You may need to run: python index_with_progress_save.py first")
    
    client.close()
except Exception as e:
    error_msg = str(e)
    if "already accessed by another instance" in error_msg:
        print("✅ Indexing is running (database locked)")
    else:
        print(f"⚠️  Error checking database: {e}")

print()
print("=" * 70)
print("Starting PDF indexing...")
print("=" * 70)
print()

# Now start PDF indexing
from index_pdfs_properly import index_wikiepstein_pdfs_properly

try:
    index_wikiepstein_pdfs_properly()
except KeyboardInterrupt:
    print("\n\nIndexing interrupted by user")
except Exception as e:
    print(f"\n\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

