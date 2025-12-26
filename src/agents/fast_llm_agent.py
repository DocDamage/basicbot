"""Fast LLM Agent for simple queries"""

from typing import Dict, Any, Optional, Iterator
import os
import json

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.llm_tools import call_llm, stream_llm


class FastLLMAgent(BaseAgent):
    """Agent for handling simple, factual queries with fast LLM"""
    
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
            ),
            AgentTool(
                name="classify_query",
                description="Classify query complexity",
                func=self._classify_query
            )
        ]
        
        super().__init__(
            agent_id="fast_llm_agent",
            role=AgentRole.LLM_FAST,
            description="Handles simple, factual queries with fast lightweight models",
            tools=tools,
            framework=framework
        )
        
        # Load config
        if config:
            self.model = config.get('model', 'llama3.2:1b')
            self.provider = config.get('provider', 'ollama')
            self.endpoint = config.get('endpoint', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
        else:
            self.model = os.getenv('FAST_LLM_MODEL', 'llama3.2:1b')
            self.provider = os.getenv('FAST_LLM_PROVIDER', 'ollama')
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
    
    def _classify_query(self, query: str) -> Dict[str, Any]:
        """Classify query complexity"""
        classification_prompt = f"""Classify this query as either "simple" or "complex":
Query: "{query}"

A simple query is:
- Direct factual questions
- Simple lookups
- Definitions
- Single-step questions

A complex query is:
- Multi-step reasoning
- Comparisons
- Analysis
- Synthesis
- Requires multiple pieces of information

Respond with only "simple" or "complex"."""
        
        try:
            response = self._call_llm(classification_prompt, temperature=0.1)
            classification = "simple" if "simple" in response.lower() else "complex"
            
            return {
                "query": query,
                "classification": classification,
                "confidence": 0.8  # Default confidence for heuristic classification
            }
        except Exception as e:
            # Default to simple on error
            return {
                "query": query,
                "classification": "simple",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process query with fast LLM
        
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
        
        # Build prompt with context
        if context:
            prompt = f"""Context:
{context}

Question: {query}

Answer based on the context above. If the context doesn't contain enough information, say so."""
        else:
            prompt = query
        
        system_prompt = kwargs.get('system_prompt', "You are a helpful assistant that provides accurate, concise answers.")
        
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
                {"type": "llm_response", "agent": "fast"}
            )
        
        return result
    
    def process_stream(self, input_data: Any, **kwargs):
        """
        Process query with streaming response
        
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
        
        # Build prompt with context
        if context:
            prompt = f"""Context:
{context}

Question: {query}

Answer based on the context above. If the context doesn't contain enough information, say so."""
        else:
            prompt = query
        
        system_prompt = kwargs.get('system_prompt', "You are a helpful assistant that provides accurate, concise answers.")
        
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
                {"type": "llm_response", "agent": "fast", "streamed": True}
            )

