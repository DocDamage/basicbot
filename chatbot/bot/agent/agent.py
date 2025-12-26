import logging
import json
from typing import Dict, Any, List, Optional
from bot.client.lama_cpp_client import LamaCppClient
from bot.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class Agent:
    """
    An agent that can use tools to accomplish tasks through function calling.
    """

    def __init__(
        self,
        llm: LamaCppClient,
        tool_registry: ToolRegistry,
        max_iterations: int = 5
    ):
        """
        Initialize the agent.

        Args:
            llm: Language model client
            tool_registry: Registry of available tools
            max_iterations: Maximum number of tool-calling iterations
        """
        self.llm = llm
        self.tools = tool_registry
        self.max_iterations = max_iterations

    def run(self, query: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Run the agent on a query.

        Args:
            query: The user's query
            conversation_history: Previous conversation messages

        Returns:
            Final answer from the agent
        """
        if conversation_history is None:
            conversation_history = []

        history = conversation_history.copy()
        iteration_count = 0

        while iteration_count < self.max_iterations:
            iteration_count += 1

            # Plan next action
            action = self._plan_next_action(query, history)

            if action["type"] == "final_answer":
                logger.info(f"Agent reached final answer after {iteration_count} iterations")
                return action["content"]

            # Execute tool
            tool_result = self._execute_tool(action)

            # Update conversation history
            history.append({
                "role": "assistant",
                "content": f"I used the {action['tool']} tool with parameters: {action['parameters']}"
            })

            history.append({
                "role": "tool",
                "content": f"Tool result: {tool_result}"
            })

            logger.info(f"Completed iteration {iteration_count}/{self.max_iterations}")

        logger.warning(f"Agent reached maximum iterations ({self.max_iterations}) without final answer")
        return "I wasn't able to complete this task within the allowed number of steps. Let me provide what I found so far."

    def _plan_next_action(self, query: str, history: List[Dict]) -> Dict[str, Any]:
        """
        Plan the next action based on the current state.

        Args:
            query: Original user query
            history: Conversation history

        Returns:
            Action dictionary with type, tool, parameters, etc.
        """
        tools_desc = self.tools.list_tools()

        # Create prompt for the LLM
        prompt = self._create_agent_prompt(query, tools_desc, history)

        # Get response from LLM
        response = self.llm.generate_answer(prompt, max_new_tokens=512)

        # Parse the action from response
        return self._parse_action(response)

    def _create_agent_prompt(
        self,
        query: str,
        tools: List[Dict],
        history: List[Dict]
    ) -> str:
        """
        Create the agent prompt with tools and history.
        """
        tools_str = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in tools
        ])

        history_str = ""
        if history:
            history_items = []
            for msg in history[-6:]:  # Last 6 messages to avoid context overflow
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:200]  # Truncate long content
                history_items.append(f"{role}: {content}")
            history_str = "\n".join(history_items) + "\n\n"

        return f"""You are a helpful AI assistant with access to various tools. Your task is to help users by using the appropriate tools when needed.

Available Tools:
{tools_str}

Tool Usage Format:
When you need to use a tool, respond with:
Action: tool_name
Action Input: {{"param1": "value1", "param2": "value2"}}

When you have enough information to answer, respond with:
Final Answer: Your complete answer here

Guidelines:
- Use tools when you need specific information or computations
- For search queries, use search_knowledge_base first, then search_web if needed
- For calculations, use the calculate tool
- For current information, use search_web
- Provide comprehensive answers based on tool results
- If you're unsure, use tools to gather more information

User Query: {query}

{history_str}What is your next action?"""

    def _parse_action(self, response: str) -> Dict[str, Any]:
        """
        Parse the action from the LLM response.

        Args:
            response: Raw LLM response

        Returns:
            Parsed action dictionary
        """
        response = response.strip()

        # Check for final answer
        if "Final Answer:" in response:
            answer = response.split("Final Answer:", 1)[1].strip()
            return {
                "type": "final_answer",
                "content": answer
            }

        # Check for tool usage
        if "Action:" in response and "Action Input:" in response:
            try:
                # Split by Action and Action Input
                parts = response.split("Action Input:", 1)
                if len(parts) == 2:
                    action_part = parts[0]
                    input_part = parts[1].strip()

                    # Extract tool name
                    tool_name = action_part.replace("Action:", "").strip()

                    # Parse parameters
                    try:
                        parameters = json.loads(input_part)
                    except json.JSONDecodeError:
                        # Fallback: try to extract simple parameters
                        parameters = {}
                        logger.warning(f"Could not parse JSON parameters: {input_part}")

                    return {
                        "type": "tool_call",
                        "tool": tool_name,
                        "parameters": parameters
                    }
            except Exception as e:
                logger.error(f"Error parsing action: {e}")

        # Default: assume final answer
        logger.warning(f"Could not parse action from response: {response[:200]}...")
        return {
            "type": "final_answer",
            "content": "I'm not sure how to respond to that request. Could you please rephrase your question?"
        }

    def _execute_tool(self, action: Dict[str, Any]) -> str:
        """
        Execute a tool based on the action.

        Args:
            action: Action dictionary with tool and parameters

        Returns:
            Tool execution result
        """
        tool_name = action.get("tool")
        parameters = action.get("parameters", {})

        if not tool_name:
            return "Error: No tool specified"

        try:
            result = self.tools.execute_tool(tool_name, **parameters)
            return str(result)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return f"Tool execution error: {str(e)}"


class AgentConfig:
    """
    Configuration for agent behavior.
    """

    DEFAULT_MAX_ITERATIONS = 5
    SUPPORTED_LLMS = ["llama", "mistral", "other"]

    @staticmethod
    def create_agent(
        llm: LamaCppClient,
        tool_registry: ToolRegistry,
        max_iterations: int = DEFAULT_MAX_ITERATIONS
    ) -> Agent:
        """
        Create a configured agent instance.

        Args:
            llm: Language model client
            tool_registry: Tool registry
            max_iterations: Maximum tool-calling iterations

        Returns:
            Configured Agent instance
        """
        return Agent(
            llm=llm,
            tool_registry=tool_registry,
            max_iterations=max_iterations
        )
