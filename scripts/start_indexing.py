"""Start indexing with proper error handling"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("STARTING INDEXING PROCESS")
print("=" * 70)
print()

try:
    # Import and run indexing
    from data.epstein_files.index_for_chatbot import index_celebrity_database
    
    print("✓ Imports successful")
    print("Starting celebrity database indexing...")
    print()
    
    index_celebrity_database()
    
    print()
    print("=" * 70)
    print("INDEXING COMPLETE!")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

