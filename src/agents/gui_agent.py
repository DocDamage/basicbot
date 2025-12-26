"""GUI Agent for managing user interface"""

from typing import Dict, Any, Optional
import threading

from ..bmad.agent_base import BaseAgent, AgentRole
from ..gui.app import ChatApp


class GUIAgent(BaseAgent):
    """Agent for managing GUI and user interactions"""
    
    def __init__(self, framework=None):
        super().__init__(
            agent_id="gui_agent",
            role=AgentRole.GUI,
            description="Manages user interface and user interactions",
            framework=framework
        )
        
        self.app: Optional[ChatApp] = None
        self.app_thread: Optional[threading.Thread] = None
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process GUI operations
        
        Args:
            input_data: Dict with 'action' and parameters
            **kwargs: Additional parameters
        """
        if isinstance(input_data, dict):
            action = input_data.get('action')
            
            if action == 'start':
                return self._start_gui()
            elif action == 'stop':
                return self._stop_gui()
            elif action == 'display_message':
                return self._display_message(
                    input_data.get('role', 'assistant'),
                    input_data.get('content', ''),
                    input_data.get('sources', [])
                )
        
        return {"error": "Invalid action"}
    
    def _start_gui(self) -> Dict[str, Any]:
        """Start GUI application"""
        if self.app is not None:
            return {"status": "already_running"}
        
        def run_gui():
            self.app = ChatApp(self.framework)
            self.app.mainloop()
        
        self.app_thread = threading.Thread(target=run_gui, daemon=True)
        self.app_thread.start()
        
        return {"status": "started"}
    
    def _stop_gui(self) -> Dict[str, Any]:
        """Stop GUI application"""
        if self.app:
            self.app.quit()
            self.app = None
            return {"status": "stopped"}
        return {"status": "not_running"}
    
    def _display_message(self, role: str, content: str, sources: list) -> Dict[str, Any]:
        """Display message in GUI"""
        if self.app:
            self.app.after(0, lambda: self.app._add_message(role, content, sources))
            return {"status": "displayed"}
        return {"status": "gui_not_running"}

