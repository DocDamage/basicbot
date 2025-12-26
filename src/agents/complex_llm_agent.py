"""Complex LLM Agent for complex queries"""

from typing import Dict, Any, Optional, Iterator
import os

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.llm_tools import call_llm, stream_llm


class ComplexLLMAgent(BaseAgent):
    """Agent for handling complex queries with advanced LLM"""
    
    def __init__(self, framework=None, config: Optional[Dict] = None):
        tools = [
            AgentTool(
                name="call_llm",
                description="Call LLM with prompt",
                func=self._call_llm
            ),
            AgentTool(
                name="stream_llm",
                description="Stream LLM response",
                func=self._stream_llm
            )
        ]
        
        super().__init__(
            agent_id="complex_llm_agent",
            role=AgentRole.LLM_COMPLEX,
            description="Handles complex queries requiring multi-step reasoning",
            tools=tools,
            framework=framework
        )
        
        # Load config
        if config:
            self.model = config.get('model', 'mixtral:8x7b')
            self.provider = config.get('provider', 'ollama')
            self.endpoint = config.get('endpoint', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
        else:
            self.model = os.getenv('COMPLEX_LLM_MODEL', 'mixtral:8x7b')
            self.provider = os.getenv('COMPLEX_LLM_PROVIDER', 'ollama')
            self.endpoint = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Call LLM"""
        return call_llm(
            prompt=prompt,
            model=self.model,
            provider=self.provider,
            system_prompt=system_prompt,
            **kwargs
        )
    
    def _stream_llm(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Iterator[str]:
        """Stream LLM response"""
        return stream_llm(
            prompt=prompt,
            model=self.model,
            provider=self.provider,
            system_prompt=system_prompt,
            **kwargs
        )
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process complex query with advanced LLM
        
        Args:
            input_data: Query string or dict with 'query' and 'context'
            **kwargs: Additional parameters
        """
        if isinstance(input_data, str):
            query = input_data
            context = kwargs.get('context', '')
        elif isinstance(input_data, dict):
            query = input_data.get('query', '')
            context = input_data.get('context', kwargs.get('context', ''))
        else:
            return {"error": "Invalid input"}
        
        # Build comprehensive prompt with context
        if context:
            prompt = f"""You are an advanced AI assistant. Use the following context to provide a comprehensive, well-reasoned answer.

Context:
{context}

Question: {query}

Provide a detailed answer that:
1. Synthesizes information from the context
2. Shows reasoning steps if needed
3. Cites specific parts of the context when relevant
4. Acknowledges limitations if the context is insufficient"""
        else:
            prompt = query
        
        system_prompt = kwargs.get(
            'system_prompt',
            "You are an advanced AI assistant capable of complex reasoning, analysis, and synthesis."
        )
        
        # Call LLM
        response = self.execute_tool(
            "call_llm",
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=kwargs.get('temperature', 0.7)
        )
        
        result = {
            "query": query,
            "response": response,
            "model": self.model,
            "provider": self.provider
        }
        
        # Store in memory
        if self.framework:
            self.framework.memory.store(
                self.agent_id,
                result,
                {"type": "llm_response", "agent": "complex"}
            )
        
        return result
    
    def process_stream(self, input_data: Any, **kwargs):
        """
        Process complex query with streaming response
        
        Yields:
            Chunks of response text
        """
        if isinstance(input_data, str):
            query = input_data
            context = kwargs.get('context', '')
        elif isinstance(input_data, dict):
            query = input_data.get('query', '')
            context = input_data.get('context', kwargs.get('context', ''))
        else:
            yield {"error": "Invalid input"}
            return
        
        # Build comprehensive prompt with context
        if context:
            prompt = f"""You are an advanced AI assistant. Use the following context to provide a comprehensive, well-reasoned answer.

Context:
{context}

Question: {query}

Provide a detailed answer that:
1. Synthesizes information from the context
2. Shows reasoning steps if needed
3. Cites specific parts of the context when relevant
4. Acknowledges limitations if the context is insufficient"""
        else:
            prompt = query
        
        system_prompt = kwargs.get(
            'system_prompt',
            "You are an advanced AI assistant capable of complex reasoning, analysis, and synthesis."
        )
        
        # Stream LLM response
        full_response = ""
        for chunk in self.execute_tool(
            "stream_llm",
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=kwargs.get('temperature', 0.7)
        ):
            full_response += chunk
            yield {"chunk": chunk, "full_response": full_response}
        
        # Store in memory after completion
        if self.framework:
            self.framework.memory.store(
                self.agent_id,
                {"query": query, "response": full_response, "model": self.model},
                {"type": "llm_response", "agent": "complex", "streamed": True}
            )

