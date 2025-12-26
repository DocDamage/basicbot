"""Router Agent for coordinating queries"""

from typing import Dict, Any, Optional

from ..bmad.agent_base import BaseAgent, AgentRole


class RouterAgent(BaseAgent):
    """Agent for routing queries to appropriate LLM agents"""
    
    def __init__(self, framework=None):
        super().__init__(
            agent_id="router_agent",
            role=AgentRole.ROUTER,
            description="Routes queries to fast or complex LLM based on complexity",
            framework=framework
        )
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Route query to appropriate LLM agent
        
        Args:
            input_data: Query string or dict with 'query' and 'retrieval_results'
            **kwargs: Additional parameters (force_agent, skip_classification, stream)
        """
        if isinstance(input_data, str):
            query = input_data
            retrieval_results = kwargs.get('retrieval_results', [])
        elif isinstance(input_data, dict):
            query = input_data.get('query', '')
            retrieval_results = input_data.get('retrieval_results', kwargs.get('retrieval_results', []))
        else:
            return {"error": "Invalid input"}
        
        # Build context from retrieval results
        context = self._build_context(retrieval_results)
        
        # Determine which agent to use
        force_agent = kwargs.get('force_agent')  # 'fast' or 'complex'
        skip_classification = kwargs.get('skip_classification', False)
        stream = kwargs.get('stream', False)
        
        if force_agent:
            agent_type = force_agent
        elif skip_classification:
            # Use heuristics
            agent_type = self._heuristic_classification(query)
        else:
            # Use fast LLM to classify
            agent_type = self._llm_classification(query)
        
        # Route to appropriate agent
        if agent_type == "complex":
            target_agent_id = "complex_llm_agent"
        else:
            target_agent_id = "fast_llm_agent"
        
        # Get target agent
        if not self.framework:
            return {"error": "Framework not initialized"}
        
        target_agent = self.framework.get_agent(target_agent_id)
        if not target_agent:
            return {"error": f"Agent {target_agent_id} not found"}
        
        # Process with target agent (with streaming if requested)
        if stream:
            # Return generator for streaming
            return {
                "stream": target_agent.process_stream(
                    {"query": query, "context": context},
                    **kwargs
                ),
                "routing": {
                    "agent_used": target_agent_id,
                    "classification": agent_type,
                    "context_chunks": len(retrieval_results)
                }
            }
        else:
            # Process normally
            result = target_agent.process(
                {"query": query, "context": context},
                **kwargs
            )
            
            # Add routing metadata
            result["routing"] = {
                "agent_used": target_agent_id,
                "classification": agent_type,
                "context_chunks": len(retrieval_results)
            }
            
            return result
    
    def _build_context(self, retrieval_results: list) -> str:
        """Build context string from retrieval results"""
        if not retrieval_results:
            return ""
        
        context_parts = []
        for i, result in enumerate(retrieval_results, 1):
            text = result.get('text', '')
            metadata = result.get('metadata', {})
            source = metadata.get('source_file', 'Unknown')
            
            context_parts.append(f"[Source {i}: {source}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def _heuristic_classification(self, query: str) -> str:
        """Classify query using heuristics"""
        query_lower = query.lower()
        
        # Complex indicators
        complex_keywords = [
            "compare", "analyze", "explain why", "how does", "what is the relationship",
            "synthesize", "evaluate", "discuss", "multiple", "several"
        ]
        
        # Simple indicators
        simple_keywords = [
            "what is", "define", "list", "name", "when", "where", "who"
        ]
        
        # Check for complex keywords
        for keyword in complex_keywords:
            if keyword in query_lower:
                return "complex"
        
        # Check length and complexity
        if len(query.split()) > 15:
            return "complex"
        
        # Default to simple
        return "simple"
    
    def _llm_classification(self, query: str) -> str:
        """Classify query using fast LLM"""
        fast_llm = self.framework.get_agent("fast_llm_agent")
        if not fast_llm:
            return self._heuristic_classification(query)
        
        try:
            classification_result = fast_llm.execute_tool("classify_query", query=query)
            return classification_result.get("classification", "simple")
        except:
            return self._heuristic_classification(query)
    
    def receive_message(self, from_agent_id: str, message: Any, metadata: Optional[Dict] = None):
        """
        Handle messages from other agents
        
        Args:
            from_agent_id: ID of sending agent
            message: Message content (dict with 'action' and data)
            metadata: Optional metadata
        """
        if not isinstance(message, dict):
            return
        
        action = message.get('action')
        
        if action == 'route_query':
            # Route a query request
            query = message.get('query', '')
            retrieval_results = message.get('retrieval_results', [])
            result = self.process({
                'query': query,
                'retrieval_results': retrieval_results
            }, **message.get('kwargs', {}))
            
            # Send result back to requesting agent
            if self.framework and 'reply_to' in message:
                self.send_message(
                    message['reply_to'],
                    {
                        'action': 'query_result',
                        'result': result
                    }
                )
        
        elif action == 'coordinate_agents':
            # Coordinate multiple agents for complex task
            agents_needed = message.get('agents', [])
            task = message.get('task', {})
            
            # Route to appropriate agents
            for agent_id in agents_needed:
                agent = self.framework.get_agent(agent_id) if self.framework else None
                if agent:
                    agent.process(task)
        
        elif action == 'broadcast':
            # Broadcast message to multiple agents
            target_agents = message.get('target_agents', [])
            broadcast_message = message.get('message', {})
            
            for agent_id in target_agents:
                if self.framework:
                    self.send_message(agent_id, broadcast_message)

