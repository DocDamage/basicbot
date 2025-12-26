"""Monitor indexing progress"""

import time
import os
from pathlib import Path
from qdrant_client import QdrantClient

print("=" * 70)
print("INDEXING MONITOR")
print("=" * 70)
print()

vector_db_dir = "./data/vector_db"
collection_name = "rag_documents"

# Check expected entries
db_path = Path('data/epstein_files/celebrity-results.json')
total_entries = 0
if db_path.exists():
    import json
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    total_entries = len(data.get('results', []))

print(f"Expected entries: {total_entries:,}")
print(f"Collection: {collection_name}")
print()
print("Monitoring progress (checking every 10 seconds)...")
print("Press Ctrl+C to stop monitoring")
print()

last_count = 0
check_count = 0

try:
    while True:
        check_count += 1
        try:
            if os.path.exists(vector_db_dir):
                client = QdrantClient(path=vector_db_dir)
                collections = client.get_collections()
                collection_names = [c.name for c in collections.collections]
                
                if collection_name in collection_names:
                    info = client.get_collection(collection_name)
                    points = info.points_count
                    
                    if points > last_count or check_count == 1:
                        progress = (points / total_entries * 100) if total_entries > 0 else 0
                        rate = points - last_count if last_count > 0 else 0
                        
                        print(f"[{time.strftime('%H:%M:%S')}] Points indexed: {points:,} / {total_entries:,} ({progress:.1f}%)", end='')
                        if rate > 0:
                            print(f" | Rate: +{rate:,} since last check")
                        else:
                            print()
                        
                        if points >= total_entries and total_entries > 0:
                            print()
                            print("=" * 70)
                            print("✅ INDEXING COMPLETE!")
                            print(f"   Total points indexed: {points:,}")
                            print("=" * 70)
                            break
                        
                        last_count = points
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] Waiting for indexing to start...")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Collection '{collection_name}' not created yet... (initializing)")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Vector DB directory not found...")
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Error: {e}")
            time.sleep(10)

except KeyboardInterrupt:
    print("\n\nMonitoring stopped")

print("\nTo check status manually, run: python check_index_status.py")

