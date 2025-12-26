"""Detailed indexing status check"""

import os
import json
from pathlib import Path
from qdrant_client import QdrantClient

print("=" * 70)
print("DETAILED INDEXING STATUS")
print("=" * 70)
print()

# Check database
db_path = Path('data/epstein_files/celebrity-results.json')
if db_path.exists():
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    total_entries = len(data.get('results', []))
    print(f"✓ Celebrity database found: {total_entries:,} entries")
    print(f"  File size: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
else:
    print("❌ Celebrity database not found!")
    total_entries = 0

print()

# Check vector DB
vector_db_dir = "./data/vector_db"
if os.path.exists(vector_db_dir):
    print(f"✓ Vector DB directory exists: {vector_db_dir}")
    
    # Count files in vector_db
    files = list(Path(vector_db_dir).rglob('*'))
    file_count = len([f for f in files if f.is_file()])
    print(f"  Files in vector_db: {file_count}")
    
    # Check Qdrant
    try:
        client = QdrantClient(path=vector_db_dir)
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        print(f"\n✓ Qdrant client connected")
        print(f"  Collections found: {len(collection_names)}")
        
        if collection_names:
            for coll_name in collection_names:
                print(f"\n  Collection: {coll_name}")
                try:
                    info = client.get_collection(coll_name)
                    points = info.points_count
                    vectors = info.vectors_count
                    print(f"    Points: {points:,}")
                    print(f"    Vectors: {vectors:,}")
                    
                    if total_entries > 0:
                        progress = (points / total_entries) * 100
                        print(f"    Progress: {progress:.1f}% ({points:,}/{total_entries:,})")
                        
                        if points >= total_entries:
                            print(f"    ✅ INDEXING COMPLETE!")
                        elif points > 0:
                            print(f"    ⏳ Indexing in progress...")
                except Exception as e:
                    print(f"    ⚠️  Error getting info: {e}")
        else:
            print(f"\n  ⏳ No collections created yet")
            print(f"     This means indexing is still initializing...")
            print(f"     (Loading embedding model can take 30-60 seconds)")
            print(f"     (Processing {total_entries:,} entries will take 10-15 minutes)")
        
        client.close()
        
    except Exception as e:
        error_msg = str(e)
        if "already accessed by another instance" in error_msg:
            print(f"\n✅ INDEXING IS RUNNING!")
            print(f"   The database is locked by the indexing process")
            print(f"   This means indexing is actively working")
            print(f"   Please wait for it to complete...")
            print(f"   (This can take 10-15 minutes for 8,408 entries)")
        else:
            print(f"\n⚠️  Error connecting to Qdrant: {e}")
            print(f"   This might be normal if indexing hasn't started yet")
else:
    print(f"❌ Vector DB directory does not exist")
    print(f"   Indexing has not started")

print()
print("=" * 70)
print("\n💡 Tip: The indexing process:")
print("   1. Loads embedding model (~30-60 seconds)")
print("   2. Initializes Qdrant collection")
print("   3. Processes all entries and creates embeddings")
print("   4. Stores in vector database")
print("\n   Total time: ~10-15 minutes for 8,408 entries")
print("=" * 70)

