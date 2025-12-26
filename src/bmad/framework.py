"""BMAD Framework - Agent registry and communication system"""

from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
from .agent_base import BaseAgent, AgentRole
from .memory import MemorySystem


class BMADFramework:
    """BMAD Framework for managing agents and their interactions"""
    
    def __init__(self, memory_storage_path: Optional[str] = None):
        """
        Initialize BMAD framework
        
        Args:
            memory_storage_path: Path for persistent memory storage
        """
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_registry: Dict[AgentRole, List[str]] = defaultdict(list)
        self.message_queue: List[Dict[str, Any]] = []
        self.memory = MemorySystem(memory_storage_path)
        self.message_handlers: Dict[str, List[Callable]] = defaultdict(list)
    
    def register_agent(self, agent: BaseAgent):
        """
        Register an agent with the framework
        
        Args:
            agent: Agent instance to register
        """
        agent.framework = self
        self.agents[agent.agent_id] = agent
        self.agent_registry[agent.role].append(agent.agent_id)
        agent.activate()
        print(f"Registered agent: {agent.agent_id} ({agent.role.value})")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def get_agents_by_role(self, role: AgentRole) -> List[BaseAgent]:
        """Get all agents with a specific role"""
        agent_ids = self.agent_registry.get(role, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message: Any,
        metadata: Optional[Dict] = None
    ):
        """
        Send a message between agents
        
        Args:
            from_agent: Sender agent ID
            to_agent: Receiver agent ID
            message: Message content
            metadata: Optional metadata
        """
        if to_agent not in self.agents:
            raise ValueError(f"Agent '{to_agent}' not found")
        
        message_data = {
            "from": from_agent,
            "to": to_agent,
            "message": message,
            "metadata": metadata or {}
        }
        
        # Deliver immediately
        target_agent = self.agents[to_agent]
        target_agent.receive_message(from_agent, message, metadata)
        
        # Store in queue for logging
        self.message_queue.append(message_data)
        
        # Trigger message handlers
        for handler in self.message_handlers.get("all", []):
            handler(message_data)
    
    def broadcast(self, from_agent: str, message: Any, metadata: Optional[Dict] = None):
        """
        Broadcast a message to all agents
        
        Args:
            from_agent: Sender agent ID
            message: Message content
            metadata: Optional metadata
        """
        for agent_id in self.agents:
            if agent_id != from_agent:
                self.send_message(from_agent, agent_id, message, metadata)
    
    def register_message_handler(self, event_type: str, handler: Callable):
        """
        Register a message handler
        
        Args:
            event_type: Event type (e.g., "all", "query", "response")
            handler: Handler function
        """
        self.message_handlers[event_type].append(handler)
    
    def get_framework_status(self) -> Dict[str, Any]:
        """Get framework status"""
        return {
            "agents": {
                agent_id: agent.get_status()
                for agent_id, agent in self.agents.items()
            },
            "message_queue_size": len(self.message_queue),
            "memory_entries": len(self.memory.memories)
        }
    
    def shutdown(self):
        """Shutdown framework and all agents"""
        for agent in self.agents.values():
            agent.deactivate()
        self.agents.clear()
        self.agent_registry.clear()
        print("BMAD Framework shut down")

