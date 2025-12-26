"""Quick check of indexing status"""

import os
from pathlib import Path
from qdrant_client import QdrantClient

print("=" * 60)
print("INDEXING STATUS CHECK")
print("=" * 60)

# Check if vector DB directory exists
vector_db_dir = "./data/vector_db"
if not os.path.exists(vector_db_dir):
    print("\n❌ Vector database directory does not exist")
    print("   Indexing has not started yet")
    print("\nTo start indexing, run:")
    print("   python data/epstein_files/index_for_chatbot.py")
else:
    print(f"\n✓ Vector database directory exists: {vector_db_dir}")
    
    # Check Qdrant
    try:
        client = QdrantClient(path=vector_db_dir)
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_names:
            print(f"\n✓ Collections found: {collection_names}")
            
            if 'rag_documents' in collection_names:
                info = client.get_collection('rag_documents')
                points = info.points_count
                print(f"\n✅ Indexing Status:")
                print(f"   Collection: rag_documents")
                print(f"   Points indexed: {points:,}")
                
                # Check expected entries
                db_path = Path('data/epstein_files/celebrity-results.json')
                if db_path.exists():
                    import json
                    with open(db_path, 'r') as f:
                        data = json.load(f)
                    total_entries = len(data.get('results', []))
                    if points >= total_entries:
                        print(f"   ✅ Celebrity database: COMPLETE ({points:,} >= {total_entries:,})")
                    else:
                        progress = (points / total_entries) * 100
                        print(f"   ⏳ Celebrity database: {progress:.1f}% ({points:,}/{total_entries:,})")
            else:
                print(f"\n⏳ Collection 'rag_documents' not found")
                print("   Indexing may still be initializing...")
        else:
            print(f"\n⏳ No collections created yet")
            print("   Indexing has not started or is still initializing")
            print("\nTo start indexing, run:")
            print("   python data/epstein_files/index_for_chatbot.py")
            
    except Exception as e:
        print(f"\n⚠️  Error checking Qdrant: {e}")
        print("   This might be normal if indexing hasn't started")

print("\n" + "=" * 60)

