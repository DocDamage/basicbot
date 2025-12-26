import requests
import json
import re
from tools import TOOLS_SCHEMA, AVAILABLE_TOOLS
from typing import List, Dict, Optional

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url

    def generate(self, model: str, prompt: str, system: str = "") -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            return f"Error calling {model}: {str(e)}"

    def chat(self, model: str, messages: list, tools: list = None) -> dict:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3}
        }
        if tools:
            payload["tools"] = tools
            
        try:
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

class MBADSystem:
    def __init__(self, ollama_client: OllamaClient, math_models: List[str], conv_models: List[str]):
        self.client = ollama_client
        # Defaults to Small Language Models (SLM) for "embedded" feel
        self.math_models = math_models if math_models else ["phi3", "qwen2:1.5b"] 
        self.conv_models = conv_models if conv_models else ["gemma2:2b", "phi3"]
        # Ensure we have at least 2 of each if possible, or recycle
        if len(self.math_models) < 2:
            self.math_models *= 2
        if len(self.conv_models) < 2:
            self.conv_models *= 2

    def process_math_query_tandem(self, query: str, context: str = "") -> Dict:
        """
        Executes the Multi-Branch Agent Debate (MBAD) for math.
        """
        # Step 1: Parallel Generation from Math Agents
        solution1 = self.client.generate(
            model=self.math_models[0],
            prompt=f"Please solve this math problem. Show your work step by step.\nProblem: {query}\nContext: {context}",
            system="You are a rigorous mathematician. Solve the problem accurately."
        )

        solution2 = self.client.generate(
            model=self.math_models[1],
            prompt=f"Please solve this math problem independent of others. Show your work.\nProblem: {query}\nContext: {context}",
            system="You are a rigorous mathematician. Solve the problem accurately."
        )

        # Step 2: Debate/Synthesis (Using a Conversion Agent as Critic)
        debate_prompt = f"""
        I have two solutions to the following problem:
        Problem: {query}

        Solution 1:
        {solution1}

        Solution 2:
        {solution2}

        Please evaluate both solutions. Check for errors in calculation or logic.
        If they agree, summarize the answer.
        If they disagree, determine which one is correct and explain why.
        Provide the final, correct answer clearly.
        """
        
        final_response = self.client.generate(
            model=self.conv_models[0],
            prompt=debate_prompt,
            system="You are an expert mathematical judge. Your goal is to find the truth by comparing proposed solutions."
        )

        return {
            "solution_1": solution1,
            "solution_2": solution2,
            "final_analysis": final_response
        }

    def process_general_chat(self, history: list, context: str = "") -> str:
        # Use phi3 or specialized model for tools if possible
        model = self.math_models[0] # Usually smarter for tools than 'gemma' small
        
        # Inject context properly
        system_msg = {
            "role": "system", 
            "content": f"You are Axiom, an advanced AI assistant. Use the provided tools to answer questions precisely. Context: {context}"
        }
        
        full_history = [system_msg] + history
        
        # 1. Call Model with Tools
        response = self.client.chat(model, full_history, tools=TOOLS_SCHEMA)
        
        if "error" in response:
            return f"System Error: {response['error']}"
            
        msg = response.get("message", {})
        
        # 2. Check for Tool Calls
        if msg.get("tool_calls"):
            print(f"Tool triggered: {msg['tool_calls']}")
            
            # Add assistant's tool-call request to history
            full_history.append(msg)
            
            # Execute each call
            for tool_call in msg["tool_calls"]:
                fn_name = tool_call["function"]["name"]
                args = tool_call["function"]["arguments"]
                
                if fn_name in AVAILABLE_TOOLS:
                    # Execute
                    try:
                        # Some args come as dict, some as string depending on model
                        if isinstance(args, str):
                            import json
                            args = json.loads(args)
                            
                        result = AVAILABLE_TOOLS[fn_name](**args)
                    except Exception as e:
                        result = f"Error executing {fn_name}: {e}"
                        
                    # Add result to history
                    full_history.append({
                        "role": "tool",
                        "content": str(result),
                        # "tool_call_id": tool_call["id"] # Ollama doesn't strictly need ID yet but good practice
                    })
            
            # 3. Final Response with Tool Outputs
            final_resp = self.client.chat(model, full_history)
            if "message" in final_resp:
                return final_resp["message"]["content"]
                
        # No tool called, return text
        return msg.get("content", "No response generated.")
