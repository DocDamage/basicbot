"""Dynamic Tool Registry for Python tools"""

import importlib
import inspect
from typing import Dict, List, Any, Optional, Callable, Type
from pathlib import Path
import sys


class ToolRegistry:
    """Registry for dynamically discovering and calling Python tools"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
    
    def register_tool(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Register a Python function as a tool
        
        Args:
            func: Python function to register
            name: Tool name (defaults to function name)
            description: Tool description (defaults to docstring)
            parameters: Parameter schema
        """
        tool_name = name or func.__name__
        
        # Get function signature
        sig = inspect.signature(func)
        param_info = {}
        for param_name, param in sig.parameters.items():
            param_info[param_name] = {
                'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                'default': param.default if param.default != inspect.Parameter.empty else None,
                'required': param.default == inspect.Parameter.empty
            }
        
        # Get description from docstring
        if description is None:
            description = inspect.getdoc(func) or f"Tool: {tool_name}"
        
        self.tools[tool_name] = func
        self.tool_metadata[tool_name] = {
            'name': tool_name,
            'description': description,
            'parameters': parameters or param_info,
            'signature': str(sig)
        }
    
    def register_module(self, module_path: str, prefix: str = ""):
        """
        Register all callable functions from a module
        
        Args:
            module_path: Path to Python module (e.g., 'src.tools.document_tools')
            prefix: Optional prefix for tool names
        """
        try:
            module = importlib.import_module(module_path)
            
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and not name.startswith('_'):
                    tool_name = f"{prefix}{name}" if prefix else name
                    self.register_tool(obj, name=tool_name)
        except Exception as e:
            print(f"Error registering module {module_path}: {e}")
    
    def register_directory(self, directory: str, package: str = ""):
        """
        Register all Python functions from files in a directory
        
        Args:
            directory: Directory path
            package: Package name (e.g., 'src.tools')
        """
        dir_path = Path(directory)
        
        for py_file in dir_path.glob("*.py"):
            if py_file.name.startswith('_'):
                continue
            
            module_name = py_file.stem
            if package:
                full_module_path = f"{package}.{module_name}"
            else:
                full_module_path = module_name
            
            try:
                self.register_module(full_module_path)
            except Exception as e:
                print(f"Error registering {full_module_path}: {e}")
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a registered tool
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
        
        tool_func = self.tools[tool_name]
        
        # Get function signature to validate arguments
        sig = inspect.signature(tool_func)
        bound_args = sig.bind_partial(**kwargs)
        bound_args.apply_defaults()
        
        # Call the function
        try:
            return tool_func(**bound_args.arguments)
        except Exception as e:
            raise RuntimeError(f"Error calling tool '{tool_name}': {e}")
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a tool"""
        return self.tool_metadata.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with metadata"""
        return [
            {
                'name': name,
                **metadata
            }
            for name, metadata in self.tool_metadata.items()
        ]
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is registered"""
        return tool_name in self.tools


# Global tool registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_python_tool(func: Callable, name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator to register a Python function as a tool
    
    Usage:
        @register_python_tool(description="My tool description")
        def my_tool(param1: str, param2: int = 10):
            return f"{param1}: {param2}"
    """
    registry = get_tool_registry()
    registry.register_tool(func, name=name, description=description)
    return func


def call_any_tool(tool_name: str, **kwargs) -> Any:
    """
    Call any registered tool by name
    
    Args:
        tool_name: Name of the tool
        **kwargs: Tool arguments
        
    Returns:
        Tool execution result
    """
    registry = get_tool_registry()
    return registry.call_tool(tool_name, **kwargs)

