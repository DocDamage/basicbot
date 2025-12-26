"""Check if indexing process is actually working"""

import psutil
import time
import os

print("=" * 70)
print("PROCESS STATUS CHECK")
print("=" * 70)
print()

# Find Python processes
python_procs = []
for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status', 'num_threads']):
    try:
        if 'python' in proc.info['name'].lower():
            # Get current CPU usage (need to wait a moment for accurate reading)
            proc.cpu_percent(interval=0.1)
            python_procs.append(proc)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if not python_procs:
    print("No Python processes found")
else:
    print(f"Found {len(python_procs)} Python process(es):\n")
    
    for proc in python_procs:
        try:
            # Get more detailed info
            cpu = proc.cpu_percent(interval=1.0)  # Wait 1 second for accurate reading
            mem = proc.memory_info()
            status = proc.status()
            threads = proc.num_threads()
            
            # Check if it's the indexing process (high memory usage)
            is_indexing = mem.rss > 500 * 1024 * 1024  # > 500MB
            
            print(f"PID: {proc.pid}")
            print(f"  CPU: {cpu:.1f}%")
            print(f"  RAM: {mem.rss / 1024 / 1024:.1f} MB")
            print(f"  Status: {status}")
            print(f"  Threads: {threads}")
            
            if is_indexing:
                print(f"  🔍 Likely indexing process (high RAM usage)")
                
                # Check I/O
                try:
                    io_counters = proc.io_counters()
                    print(f"  I/O Read: {io_counters.read_bytes / 1024 / 1024:.1f} MB")
                    print(f"  I/O Write: {io_counters.write_bytes / 1024 / 1024:.1f} MB")
                except:
                    pass
                
                # Check if it's actually doing work
                if cpu < 1.0 and status == 'sleeping':
                    print(f"  ⚠️  WARNING: Low CPU usage and sleeping status")
                    print(f"     Process might be stuck or waiting")
                elif cpu > 1.0:
                    print(f"  ✅ Process is using CPU (working)")
                elif status == 'running':
                    print(f"  ✅ Process is running (may be I/O bound)")
            
            print()
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"  Error getting info: {e}\n")

print("=" * 70)
print("\n💡 If CPU is 0% and status is 'sleeping':")
print("   - Process might be stuck waiting for I/O")
print("   - Or waiting for embedding model to process")
print("   - Check again in 30 seconds to see if it progresses")
print("\n💡 If RAM is high but CPU is low:")
print("   - Model is loaded in memory")
print("   - May be processing embeddings (CPU spikes briefly)")
print("   - Or writing to disk (I/O bound)")

