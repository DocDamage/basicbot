"""Memory Agent for chat history management"""

from typing import Dict, Any, Optional, List
import os
from datetime import datetime

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool


class MemoryAgent(BaseAgent):
    """Agent for managing chat history and context"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="save_conversation",
                description="Save conversation to history",
                func=self._save_conversation
            ),
            AgentTool(
                name="load_conversation",
                description="Load conversation from history",
                func=self._load_conversation
            ),
            AgentTool(
                name="get_history",
                description="Get conversation history",
                func=self._get_history
            )
        ]
        
        super().__init__(
            agent_id="memory_agent",
            role=AgentRole.MEMORY,
            description="Manages chat history and context persistence",
            tools=tools,
            framework=framework
        )
        
        self.chat_history_dir = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
        os.makedirs(self.chat_history_dir, exist_ok=True)
        self.current_session_id = None
    
    def _save_conversation(self, session_id: str, messages: List[Dict]) -> str:
        """Save conversation to file"""
        import json
        
        file_path = os.path.join(self.chat_history_dir, f"{session_id}.json")
        
        conversation = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "messages": messages
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def _load_conversation(self, session_id: str) -> Optional[Dict]:
        """Load conversation from file"""
        import json
        
        file_path = os.path.join(self.chat_history_dir, f"{session_id}.json")
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_history(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get conversation history"""
        if session_id is None:
            session_id = self.current_session_id
        
        if session_id is None:
            return []
        
        if self.framework:
            return self.framework.memory.get_conversation_history(session_id)[-limit:]
        
        return []
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process memory operations
        
        Args:
            input_data: Dict with 'action' and parameters
            **kwargs: Additional parameters
        """
        if isinstance(input_data, dict):
            action = input_data.get('action')
            
            if action == 'save':
                session_id = input_data.get('session_id', self.current_session_id)
                messages = input_data.get('messages', [])
                if session_id:
                    file_path = self.execute_tool("save_conversation", session_id=session_id, messages=messages)
                    return {"status": "saved", "file_path": file_path}
            
            elif action == 'load':
                session_id = input_data.get('session_id')
                if session_id:
                    conversation = self.execute_tool("load_conversation", session_id=session_id)
                    return {"status": "loaded", "conversation": conversation}
            
            elif action == 'get_history':
                session_id = input_data.get('session_id', self.current_session_id)
                limit = input_data.get('limit', 50)
                history = self.execute_tool("get_history", session_id=session_id, limit=limit)
                return {"history": history}
        
        return {"error": "Invalid action"}
    
    def store_message(self, role: str, content: str, session_id: Optional[str] = None, sources: Optional[List] = None):
        """Store a message in memory"""
        if session_id is None:
            session_id = self.current_session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_session_id = session_id
        
        if self.framework:
            self.framework.memory.store(
                self.agent_id,
                content,
                {
                    "type": "conversation",
                    "role": role,
                    "session_id": session_id,
                    "sources": sources or []
                }
            )
    
    def receive_message(self, from_agent_id: str, message: Any, metadata: Optional[Dict] = None):
        """Handle messages from other agents"""
        if isinstance(message, dict) and message.get('type') == 'conversation':
            self.store_message(
                role=message.get('role', 'assistant'),
                content=message.get('content', ''),
                session_id=message.get('session_id'),
                sources=message.get('sources', [])
            )

