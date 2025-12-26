import logging
from typing import Callable, Any, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Tool:
    """
    Represents a tool that can be called by an agent.
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        schema: Dict[str, Any]
    ):
        """
        Initialize a tool.

        Args:
            name: Unique name for the tool
            description: Description of what the tool does
            func: The function to execute
            schema: JSON schema for the tool's parameters
        """
        self.name = name
        self.description = description
        self.func = func
        self.schema = schema

    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with given parameters.

        Args:
            **kwargs: Parameters for the tool function

        Returns:
            Result of the tool execution
        """
        try:
            logger.info(f"Executing tool: {self.name} with params: {kwargs}")
            result = self.func(**kwargs)
            logger.info(f"Tool {self.name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {e}")
            return f"Error: {str(e)}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.schema
        }


class ToolRegistry:
    """
    Registry for managing available tools.
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool in the registry."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Tool:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        return [tool.to_dict() for tool in self.tools.values()]

    def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if tool:
            return tool.execute(**kwargs)
        else:
            raise ValueError(f"Tool '{name}' not found")

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tools.keys())


# Define core tools
def search_knowledge_base(query: str, vector_db=None, k: int = 5) -> str:
    """
    Search the local knowledge base for relevant information.

    Args:
        query: Search query
        vector_db: Vector database instance
        k: Number of results to return

    Returns:
        Formatted search results
    """
    if not vector_db:
        return "Error: Vector database not available"

    try:
        docs, sources = vector_db.similarity_search_with_threshold(query=query, k=k)

        if not docs:
            return "No relevant information found in knowledge base."

        results = []
        for i, (doc, source) in enumerate(zip(docs, sources)):
            results.append(f"Document {i+1}: {doc.page_content[:500]}...")

        return "\n\n".join(results)

    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


def search_web(query: str, search_tool=None, num_results: int = 3) -> str:
    """
    Search the web for information.

    Args:
        query: Search query
        search_tool: Web search tool instance
        num_results: Number of results to fetch

    Returns:
        Formatted web search results
    """
    if not search_tool:
        return "Error: Web search tool not available"

    try:
        results = search_tool.search_and_fetch_content(
            query=query, num_results=num_results, fetch_content=True
        )

        if not results:
            return "No web search results found."

        formatted_results = []
        for i, result in enumerate(results):
            title = result.get("title", "No title")
            snippet = result.get("snippet", "")[:300]
            content = result.get("full_content", "")[:500]

            formatted_results.append(f"Web Result {i+1}: {title}")
            formatted_results.append(f"Snippet: {snippet}")
            if content:
                formatted_results.append(f"Content: {content}...")
            formatted_results.append("")

        return "\n".join(formatted_results)

    except Exception as e:
        return f"Error searching web: {str(e)}"


def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        Result of the calculation
    """
    try:
        # Basic security: only allow safe mathematical operations
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic mathematical operations are allowed"

        result = eval(expression, {"__builtins__": {}})
        return f"Result: {result}"

    except Exception as e:
        return f"Error calculating expression: {str(e)}"


def get_current_date() -> str:
    """
    Get the current date and time.

    Returns:
        Current date and time
    """
    now = datetime.now()
    return f"Current date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}"


def python_repl(code: str) -> str:
    """
    Execute Python code in a sandboxed environment.

    Args:
        code: Python code to execute

    Returns:
        Execution result
    """
    try:
        # Very basic sandbox - in production, use proper sandboxing
        # This is just for demonstration
        allowed_globals = {
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "range": range,
                "sum": sum,
                "max": max,
                "min": min,
                "abs": abs,
                "round": round,
                "print": print
            }
        }

        # Execute code
        exec(f"result = ({code})", allowed_globals)
        result = allowed_globals.get("result", "No result")

        return f"Execution result: {result}"

    except Exception as e:
        return f"Error executing code: {str(e)}"


def create_default_tool_registry(vector_db=None, search_tool=None) -> ToolRegistry:
    """
    Create a tool registry with default tools.

    Args:
        vector_db: Vector database instance for knowledge base search
        search_tool: Web search tool instance

    Returns:
        Configured tool registry
    """
    registry = ToolRegistry()

    # Knowledge base search tool
    kb_tool = Tool(
        name="search_knowledge_base",
        description="Search the local knowledge base for relevant information about documents and data.",
        func=lambda query, k=5: search_knowledge_base(query, vector_db, k),
        schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant information"
                },
                "k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    )

    # Web search tool
    web_tool = Tool(
        name="search_web",
        description="Search the internet for current information and recent developments.",
        func=lambda query, num_results=3: search_web(query, search_tool, num_results),
        schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query for web information"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of web results to fetch",
                    "default": 3
                }
            },
            "required": ["query"]
        }
    )

    # Calculator tool
    calc_tool = Tool(
        name="calculate",
        description="Perform mathematical calculations and computations.",
        func=calculate,
        schema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3')"
                }
            },
            "required": ["expression"]
        }
    )

    # Date/time tool
    date_tool = Tool(
        name="get_current_date",
        description="Get the current date and time information.",
        func=get_current_date,
        schema={
            "type": "object",
            "properties": {},
            "description": "No parameters required"
        }
    )

    # Python REPL tool (use with caution)
    repl_tool = Tool(
        name="python_repl",
        description="Execute Python code for computations and data processing.",
        func=python_repl,
        schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute (limited to safe operations)"
                }
            },
            "required": ["code"]
        }
    )

    # Register all tools
    registry.register(kb_tool)
    registry.register(web_tool)
    registry.register(calc_tool)
    registry.register(date_tool)
    registry.register(repl_tool)

    return registry
