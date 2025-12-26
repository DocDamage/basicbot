"""Watch progress in real-time"""

import time
import os
from pathlib import Path

progress_file = Path("data/logs/progress.txt")

def watch_progress():
    """Watch and display progress updates"""
    print("Watching progress... (Press Ctrl+C to stop)")
    print("=" * 60)
    
    last_size = 0
    
    while True:
        try:
            if progress_file.exists():
                with open(progress_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Clear screen and show progress
                os.system('cls' if os.name == 'nt' else 'clear')
                print(content)
            else:
                print("Waiting for progress file to be created...")
                print(f"Looking for: {progress_file}")
            
            time.sleep(1)  # Update every second
            
        except KeyboardInterrupt:
            print("\nStopped watching progress.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    watch_progress()

