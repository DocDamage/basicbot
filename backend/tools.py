import os
import datetime
import sqlite3

# Lazy load complex libs
sympy = None
ddg = None

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate a mathematical expression using Python (SymPy/NumPy). Use this for any math query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate (e.g., 'sin(pi/2)', 'integrate(x**2, x)')."
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the live web for information using DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current system time and date.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in the permissible workspace or library directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Subpath to list (default: root)."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_library",
            "description": "Search the local ebook library database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Title or Author to search for."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def calculate(expression):
    """Safely evaluate mathematical expressions using SymPy."""
    global sympy
    if sympy is None:
        import sympy
    try:
        # Use parse_expr with restricted local_dict for safety
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
        
        # Define allowed symbols
        x, y, z, t, n = sympy.symbols('x y z t n')
        allowed_locals = {
            'x': x, 'y': y, 'z': z, 't': t, 'n': n,
            'pi': sympy.pi, 'e': sympy.E, 'I': sympy.I,
            'sin': sympy.sin, 'cos': sympy.cos, 'tan': sympy.tan,
            'log': sympy.log, 'exp': sympy.exp, 'sqrt': sympy.sqrt,
            'integrate': sympy.integrate, 'diff': sympy.diff,
            'limit': sympy.limit, 'Sum': sympy.Sum, 'Product': sympy.Product
        }
        
        # Parse with safety restrictions
        transformations = standard_transformations + (implicit_multiplication_application,)
        expr = parse_expr(expression, local_dict=allowed_locals, transformations=transformations)
        result = expr.evalf()
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

def web_search(query):
    try:
        from duckduckgo_search import DDGS
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        summary = ""
        for r in results:
            summary += f"- {r['title']}: {r['body']} ({r['href']})\n"
        return summary
    except Exception as e:
        return f"Search failed: {e}"

def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def list_files(path="."):
    """List files in permissible directories only."""
    ALLOWED_ROOTS = [
        r"C:\Users\dferr\Desktop\dareaschatbot\library",
        r"C:\Users\dferr\Desktop\dareaschatbot\workspace",
        r"C:\Users\dferr\Desktop\dareaschatbot\backend\rag_data"
    ]
    try:
        abs_path = os.path.abspath(path)
        # Security check: must be within allowed roots
        if not any(abs_path.startswith(root) for root in ALLOWED_ROOTS):
            return f"Access denied: Path '{path}' is outside allowed directories."
        return str(os.listdir(abs_path))
    except Exception as e:
        return f"Error listing files: {e}"

def search_library(query):
    conn = None
    try:
        conn = sqlite3.connect("backend/library.db")
        conn.row_factory = sqlite3.Row
        q = f"%{query}%"
        rows = conn.execute("SELECT title, author FROM books WHERE title LIKE ? OR author LIKE ? LIMIT 5", (q, q)).fetchall()
        if not rows:
            return "No books found."
        return "\n".join([f"{r['title']} by {r['author']}" for r in rows])
    except Exception as e:
        return f"Library search error: {e}"
    finally:
        if conn:
            conn.close()

# Map names to functions
AVAILABLE_TOOLS = {
    "calculate": calculate,
    "web_search": web_search,
    "get_time": get_time,
    "list_files": list_files,
    "search_library": search_library
}
