"""Fix for six.moves compatibility issue with Python 3.13"""

import sys
import os
from pathlib import Path

# Find site-packages directory
import site
site_packages = site.getsitepackages()[0] if site.getsitepackages() else None

if not site_packages:
    print("Could not find site-packages directory")
    sys.exit(1)

six_path = Path(site_packages) / "six" / "__init__.py"

if not six_path.exists():
    print(f"six not found at {six_path}")
    sys.exit(1)

# Read the six __init__.py file
with open(six_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if moves is already defined
if 'class _MovedItems' in content or 'moves = Module_six_moves_urllib_parse' in content:
    print("six.moves appears to already be defined")
    sys.exit(0)

# Add moves compatibility for Python 3.13
# This creates a minimal moves module that provides the necessary imports
moves_patch = '''

# Python 3.13 compatibility: six.moves was removed, but dateutil still needs it
try:
    from six.moves import _thread
except ImportError:
    # Create a minimal moves module for Python 3.13
    import types
    moves = types.ModuleType('six.moves')
    sys.modules['six.moves'] = moves
    
    # Add commonly used items from six.moves
    try:
        import _thread as _thread_module
        moves._thread = _thread_module
    except ImportError:
        try:
            import thread as _thread_module
            moves._thread = _thread_module
        except ImportError:
            pass
    
    # Add other common moves imports
    try:
        from urllib.parse import urlparse, urlunparse, urljoin, urlsplit, urlunsplit, quote, unquote
        moves.urllib_parse = types.ModuleType('six.moves.urllib_parse')
        moves.urllib_parse.urlparse = urlparse
        moves.urllib_parse.urlunparse = urlunparse
        moves.urllib_parse.urljoin = urljoin
        moves.urllib_parse.urlsplit = urlsplit
        moves.urllib_parse.urlunsplit = urlunsplit
        moves.urllib_parse.quote = quote
        moves.urllib_parse.unquote = unquote
    except ImportError:
        pass

'''

# Check if we need to add the patch
if 'six.moves' not in content or 'moves = types.ModuleType' not in content:
    # Add the patch at the end of the file
    with open(six_path, 'a', encoding='utf-8') as f:
        f.write(moves_patch)
    print(f"✓ Patched {six_path} for Python 3.13 compatibility")
else:
    print("six.moves compatibility already exists")

