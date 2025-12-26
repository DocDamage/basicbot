import sys
import types

# Mock urllib3.packages.six.moves if it's missing (urllib3 v2.0+)
try:
    import urllib3
    import urllib3.packages
except ImportError:
    pass

try:
    import urllib3.packages.six.moves
except ImportError:
    # Create dummy modules
    six = types.ModuleType("urllib3.packages.six")
    moves = types.ModuleType("urllib3.packages.six.moves")
    http_client = types.ModuleType("urllib3.packages.six.moves.http_client")
    
    moves.http_client = http_client
    six.moves = moves
    
    # Inject
    if 'urllib3.packages' not in sys.modules:
        sys.modules['urllib3.packages'] = types.ModuleType("urllib3.packages")
        
    sys.modules['urllib3.packages.six'] = six
    sys.modules['urllib3.packages.six.moves'] = moves
    sys.modules['urllib3.packages.six.moves.http_client'] = http_client
    
    print("Patched urllib3.packages.six.moves + http_client for legacy compatibility.")
