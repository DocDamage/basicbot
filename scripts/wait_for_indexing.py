"""Wait for indexing to complete"""

import time
import os
from pathlib import Path
from qdrant_client import QdrantClient

print("=" * 70)
print("WAITING FOR INDEXING TO COMPLETE")
print("=" * 70)
print()

vector_db_dir = "./data/vector_db"
collection_name = "rag_documents"

# Get expected count
db_path = Path('data/epstein_files/celebrity-results.json')
total_entries = 0
if db_path.exists():
    import json
    with open(db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    total_entries = len(data.get('results', []))

print(f"Waiting for {total_entries:,} entries to be indexed...")
print("(Indexing is running - database is locked, which is good!)")
print()
print("Checking every 30 seconds...")
print("Press Ctrl+C to stop monitoring")
print()

last_status = None
check_count = 0

try:
    while True:
        check_count += 1
        try:
            client = QdrantClient(path=vector_db_dir)
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_name in collection_names:
                info = client.get_collection(collection_name)
                points = info.points_count
                progress = (points / total_entries * 100) if total_entries > 0 else 0
                
                status = f"Indexed: {points:,}/{total_entries:,} ({progress:.1f}%)"
                
                if status != last_status:
                    print(f"[{time.strftime('%H:%M:%S')}] {status}")
                    last_status = status
                
                if points >= total_entries and total_entries > 0:
                    print()
                    print("=" * 70)
                    print("✅ INDEXING COMPLETE!")
                    print(f"   Total points indexed: {points:,}")
                    print("=" * 70)
                    break
            else:
                if last_status != "Initializing...":
                    print(f"[{time.strftime('%H:%M:%S')}] Initializing... (collection not created yet)")
                    last_status = "Initializing..."
            
            client.close()
            
        except Exception as e:
            error_msg = str(e)
            if "already accessed by another instance" in error_msg:
                if last_status != "Running...":
                    print(f"[{time.strftime('%H:%M:%S')}] ✅ Indexing is running... (database locked)")
                    last_status = "Running..."
            else:
                if last_status != f"Error: {error_msg[:50]}":
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️  {error_msg[:80]}")
                    last_status = f"Error: {error_msg[:50]}"
        
        time.sleep(30)
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped by user")
    print("\nIndexing is still running in the background.")
    print("You can check status later with: python check_indexing_detailed.py")

print("\nTo check status manually, run: python check_indexing_detailed.py")

