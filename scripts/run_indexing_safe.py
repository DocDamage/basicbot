"""Run indexing with error handling and logging"""

import sys
import os
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from fix_indexing_batch import index_celebrity_database_improved
    
    print("Starting indexing...")
    print("=" * 70)
    
    index_celebrity_database_improved()
    
except KeyboardInterrupt:
    print("\n\nIndexing interrupted by user")
    sys.exit(1)
except Exception as e:
    print(f"\n\n❌ ERROR: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

