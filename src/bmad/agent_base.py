"""Base Agent Class for BMAD Framework"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from ..tools.tool_registry import get_tool_registry, call_any_tool


class AgentRole(Enum):
    """Agent role types"""
    DOCUMENT_PROCESSOR = "document_processor"
    RETRIEVAL = "retrieval"
    LLM_FAST = "llm_fast"
    LLM_COMPLEX = "llm_complex"
    ROUTER = "router"
    GUI = "gui"
    MEMORY = "memory"
    VECTOR_STORE = "vector_store"
    REACH_EXTRACTION = "reach_extraction"
    COMPLIANCE_TAGGING = "compliance_tagging"
    BOOK_PROCESSOR = "book_processor"
    WRITING = "writing"
    STYLE_ANALYSIS = "style_analysis"
    CONTINUITY = "continuity"
    PROJECT_MANAGEMENT = "project_management"


@dataclass
class AgentTool:
    """Tool definition for agents"""
    name: str
    description: str
    func: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConstraint:
    """Constraint definition for agents"""
    type: str  # e.g., "rate_limit", "token_limit", "timeout"
    value: Any
    description: str = ""


class BaseAgent(ABC):
    """Base class for all BMAD agents"""
    
    def __init__(
        self,
        agent_id: str,
        role: AgentRole,
        description: str,
        tools: Optional[List[AgentTool]] = None,
        constraints: Optional[List[AgentConstraint]] = None,
        framework: Optional[Any] = None
    ):
        """
        Initialize base agent
        
        Args:
            agent_id: Unique identifier for the agent
            role: Agent role
            description: Agent description
            tools: List of tools available to the agent
            constraints: List of constraints on the agent
            framework: Reference to BMAD framework
        """
        self.agent_id = agent_id
        self.role = role
        self.description = description
        self.tools: Dict[str, AgentTool] = {
            tool.name: tool for tool in (tools or [])
        }
        self.constraints = constraints or []
        self.framework = framework
        self.status = "initialized"
        self.metrics: Dict[str, Any] = {}
    
    def register_tool(self, tool: AgentTool):
        """Register a new tool"""
        self.tools[tool.name] = tool
    
    def get_tool(self, tool_name: str) -> Optional[AgentTool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool (checks local tools first, then global registry)
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        # First check local tools
        tool = self.get_tool(tool_name)
        if tool:
            try:
                return tool.func(**kwargs)
            except Exception as e:
                raise RuntimeError(f"Error executing tool '{tool_name}': {e}")
        
        # Then check global tool registry
        registry = get_tool_registry()
        if registry.has_tool(tool_name):
            try:
                return registry.call_tool(tool_name, **kwargs)
            except Exception as e:
                raise RuntimeError(f"Error executing tool '{tool_name}': {e}")
        
        raise ValueError(f"Tool '{tool_name}' not found. Available local tools: {list(self.tools.keys())}, Available global tools: {list(registry.tools.keys())}")
    
    def call_python_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call any Python tool from the global registry
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        return call_any_tool(tool_name, **kwargs)
    
    def list_available_tools(self) -> Dict[str, List[str]]:
        """
        List all available tools (local + global)
        
        Returns:
            Dict with 'local' and 'global' tool lists
        """
        registry = get_tool_registry()
        return {
            'local': list(self.tools.keys()),
            'global': list(registry.tools.keys()),
            'all': list(self.tools.keys()) + list(registry.tools.keys())
        }
    
    def send_message(self, target_agent_id: str, message: Any, metadata: Optional[Dict] = None):
        """
        Send a message to another agent via framework
        
        Args:
            target_agent_id: ID of target agent
            message: Message content
            metadata: Optional metadata
        """
        if self.framework:
            self.framework.send_message(
                from_agent=self.agent_id,
                to_agent=target_agent_id,
                message=message,
                metadata=metadata
            )
        else:
            raise RuntimeError("Framework not initialized")
    
    def receive_message(self, from_agent_id: str, message: Any, metadata: Optional[Dict] = None):
        """
        Receive a message from another agent
        
        Args:
            from_agent_id: ID of sending agent
            message: Message content
            metadata: Optional metadata
        """
        # Override in subclasses to handle messages
        pass
    
    @abstractmethod
    def process(self, input_data: Any, **kwargs) -> Any:
        """
        Process input data (main agent logic)
        
        Args:
            input_data: Input to process
            **kwargs: Additional parameters
            
        Returns:
            Processing result
        """
        pass
    
    def activate(self):
        """Activate the agent"""
        self.status = "active"
    
    def deactivate(self):
        """Deactivate the agent"""
        self.status = "inactive"
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "role": self.role.value,
            "status": self.status,
            "tools": list(self.tools.keys()),
            "metrics": self.metrics
        }

