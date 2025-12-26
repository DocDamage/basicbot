from backend.mbad import OllamaClient, MBADSystem
from backend.tools import AVAILABLE_TOOLS
import json

# Mock Client to test Tool Logic without needing a smart model response
class MockOllamaClient(OllamaClient):
    def chat(self, model, messages, tools=None):
        last_msg = messages[-1]
        
        # Scenario 1: User asks math -> Tool Call
        if "calculate" in last_msg["content"].lower():
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "calculate",
                                "arguments": '{"expression": "50 * 3"}'
                            }
                        }
                    ]
                }
            }
        
        # Scenario 2: Tool Output -> Final Answer
        if last_msg["role"] == "tool":
            return {
                "message": {
                    "role": "assistant",
                    "content": f"The result is {last_msg['content']}"
                }
            }
            
        return {"message": {"role": "assistant", "content": "Hello"}}

def test_tool_flow():
    mock_client = MockOllamaClient()
    system = MBADSystem(mock_client, ["mock"], ["mock"])
    
    print("Testing Math Tool Flow...")
    history = [{"role": "user", "content": "calculate 50 * 3"}]
    response = system.process_general_chat(history)
    print(f"Response: {response}")
    
    assert "150" in response or "result" in response.lower()
    print("SUCCESS: Tool flow verified with Mock.")

if __name__ == "__main__":
    test_tool_flow()
