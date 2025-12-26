"""Check PDF indexing status"""

import os
import json
from pathlib import Path
from qdrant_client import QdrantClient

print("=" * 70)
print("PDF INDEXING STATUS")
print("=" * 70)
print()

# Check progress file
progress_file = "pdf_indexing_progress.json"
if os.path.exists(progress_file):
    with open(progress_file, 'r') as f:
        progress = json.load(f)
    
    files_processed = progress.get('files_processed', 0)
    total_files = progress.get('total_files', 0)
    chunks_created = progress.get('chunks_created', 0)
    last_update = progress.get('timestamp', 0)
    
    import time
    elapsed = time.time() - last_update if last_update > 0 else 0
    
    print(f"✓ Progress file found")
    print(f"  Files processed: {files_processed:,}/{total_files:,} ({files_processed/total_files*100:.1f}%)")
    print(f"  Chunks created: {chunks_created:,}")
    print(f"  Last update: {elapsed/60:.1f} minutes ago")
    
    if elapsed > 300:  # 5 minutes
        print(f"  ⚠️  WARNING: No update in {elapsed/60:.1f} minutes - process may have stopped")
    else:
        print(f"  ✅ Process is active (updated recently)")
else:
    print("❌ No progress file found")
    print("   Indexing may not have started or completed")

print()

# Check vector database
vector_db_dir = "./data/vector_db"
if os.path.exists(vector_db_dir):
    try:
        client = QdrantClient(path=vector_db_dir)
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if 'rag_documents' in collection_names:
            info = client.get_collection('rag_documents')
            points = info.points_count
            
            print(f"✓ Vector database status:")
            print(f"  Collection: rag_documents")
            print(f"  Total points: {points:,}")
            
            # Estimate PDF chunks (celebrity DB has ~8,408, rest should be PDFs)
            pdf_chunks = max(0, points - 8408)
            print(f"  Estimated PDF chunks: {pdf_chunks:,}")
            
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    p = json.load(f)
                expected_chunks = p.get('chunks_created', 0)
                if pdf_chunks > 0:
                    print(f"  ✓ PDFs are being indexed!")
        else:
            print("⏳ Collection 'rag_documents' not found yet")
        
        client.close()
    except Exception as e:
        error_msg = str(e)
        if "already accessed by another instance" in error_msg:
            print("✅ INDEXING IS RUNNING!")
            print("   Database is locked - process is actively working")
        else:
            print(f"⚠️  Error checking database: {e}")

print()
print("=" * 70)

