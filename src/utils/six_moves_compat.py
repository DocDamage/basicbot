"""
Python 3.13 compatibility shim for six.moves

Python 3.13 removed six.moves because it's no longer needed (Python 3 doesn't need
Python 2/3 compatibility). However, many packages still try to import from six.moves.
This module creates a compatibility shim to make those imports work.
"""

import sys
import types
import io
import queue

# Only set up if six.moves doesn't exist
if 'six.moves' not in sys.modules:
    # Create six module if it doesn't exist
    if 'six' not in sys.modules:
        six_module = types.ModuleType('six')
        # Add common six attributes
        six_module.string_types = str
        six_module.text_type = str
        six_module.binary_type = bytes
        six_module.integer_types = int
        six_module.class_types = type
        six_module.PY2 = False
        six_module.PY3 = True
        
        # Add utility functions
        def b(s):
            """Convert string to bytes (Python 3 compatibility)"""
            if isinstance(s, bytes):
                return s
            return s.encode('utf-8')
        six_module.b = b
        
        def u(s):
            """Convert bytes to string (Python 3 compatibility)"""
            if isinstance(s, str):
                return s
            return s.decode('utf-8')
        six_module.u = u
        
        # Add add_metaclass decorator
        def add_metaclass(metaclass):
            """Class decorator for creating a class with a metaclass."""
            def wrapper(cls):
                orig_vars = cls.__dict__.copy()
                slots = orig_vars.get('__slots__')
                if slots is not None:
                    if isinstance(slots, str):
                        slots = [slots]
                    for slots_var in slots:
                        orig_vars.pop(slots_var, None)
                orig_vars.pop('__dict__', None)
                orig_vars.pop('__weakref__', None)
                return metaclass(cls.__name__, cls.__bases__, orig_vars)
            return wrapper
        six_module.add_metaclass = add_metaclass
        
        # Add StringIO directly to six (some packages import it from six, not six.moves)
        six_module.StringIO = io.StringIO
        
        sys.modules['six'] = six_module
    else:
        six_module = sys.modules['six']
        # Ensure common attributes exist
        if not hasattr(six_module, 'string_types'):
            six_module.string_types = str
        if not hasattr(six_module, 'text_type'):
            six_module.text_type = str
        if not hasattr(six_module, 'binary_type'):
            six_module.binary_type = bytes
        if not hasattr(six_module, 'add_metaclass'):
            def add_metaclass(metaclass):
                def wrapper(cls):
                    orig_vars = cls.__dict__.copy()
                    slots = orig_vars.get('__slots__')
                    if slots is not None:
                        if isinstance(slots, str):
                            slots = [slots]
                        for slots_var in slots:
                            orig_vars.pop(slots_var, None)
                    orig_vars.pop('__dict__', None)
                    orig_vars.pop('__weakref__', None)
                    return metaclass(cls.__name__, cls.__bases__, orig_vars)
                return wrapper
            six_module.add_metaclass = add_metaclass
        if not hasattr(six_module, 'StringIO'):
            six_module.StringIO = io.StringIO
    
    # Create six.moves as a package
    moves = types.ModuleType('six.moves')
    moves.__path__ = []  # Make it a package
    sys.modules['six.moves'] = moves
    
    # Add _thread
    try:
        import _thread
        moves._thread = _thread
    except ImportError:
        try:
            import thread as _thread
            moves._thread = _thread
        except ImportError:
            pass
    
    # Add StringIO/cStringIO compatibility
    moves.StringIO = io.StringIO
    moves.cStringIO = io.StringIO
    
    # Add queue
    moves.queue = queue
    moves.Queue = queue.Queue
    
    # Create urllib subpackage
    urllib = types.ModuleType('six.moves.urllib')
    urllib.__path__ = []
    sys.modules['six.moves.urllib'] = urllib
    
    # Add urllib.parse (both formats)
    try:
        from urllib import parse as urllib_parse_module
        # six.moves.urllib_parse
        urllib_parse = types.ModuleType('six.moves.urllib_parse')
        urllib_parse.urlparse = urllib_parse_module.urlparse
        urllib_parse.urlunparse = urllib_parse_module.urlunparse
        urllib_parse.urljoin = urllib_parse_module.urljoin
        urllib_parse.urlsplit = urllib_parse_module.urlsplit
        urllib_parse.urlunsplit = urllib_parse_module.urlunsplit
        urllib_parse.quote = urllib_parse_module.quote
        urllib_parse.unquote = urllib_parse_module.unquote
        sys.modules['six.moves.urllib_parse'] = urllib_parse
        
        # six.moves.urllib.parse (nested)
        urllib_parse_nested = types.ModuleType('six.moves.urllib.parse')
        urllib_parse_nested.urlparse = urllib_parse_module.urlparse
        urllib_parse_nested.urlunparse = urllib_parse_module.urlunparse
        urllib_parse_nested.urljoin = urllib_parse_module.urljoin
        urllib_parse_nested.urlsplit = urllib_parse_module.urlsplit
        urllib_parse_nested.urlunsplit = urllib_parse_module.urlunsplit
        urllib_parse_nested.quote = urllib_parse_module.quote
        urllib_parse_nested.unquote = urllib_parse_module.unquote
        sys.modules['six.moves.urllib.parse'] = urllib_parse_nested
        urllib.parse = urllib_parse_nested
    except ImportError:
        pass
    
    # Add urllib.request (both formats)
    try:
        from urllib import request as urllib_request_module
        # six.moves.urllib_request
        urllib_request = types.ModuleType('six.moves.urllib_request')
        urllib_request.urlopen = urllib_request_module.urlopen
        urllib_request.Request = urllib_request_module.Request
        sys.modules['six.moves.urllib_request'] = urllib_request
        
        # six.moves.urllib.request (nested)
        urllib_request_nested = types.ModuleType('six.moves.urllib.request')
        urllib_request_nested.urlopen = urllib_request_module.urlopen
        urllib_request_nested.Request = urllib_request_module.Request
        sys.modules['six.moves.urllib.request'] = urllib_request_nested
        urllib.request = urllib_request_nested
    except ImportError:
        pass
    
    # Add configparser
    try:
        import configparser
        moves.configparser = configparser
        sys.modules['six.moves.configparser'] = configparser
    except ImportError:
        try:
            import ConfigParser as configparser
            moves.configparser = configparser
            sys.modules['six.moves.configparser'] = configparser
        except ImportError:
            pass
    
    # Add html_parser
    try:
        import html.parser as html_parser
        moves.html_parser = html_parser
        sys.modules['six.moves.html_parser'] = html_parser
    except ImportError:
        try:
            import HTMLParser as html_parser
            moves.html_parser = html_parser
            sys.modules['six.moves.html_parser'] = html_parser
        except ImportError:
            pass

