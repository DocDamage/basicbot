# RAG Chatbot Usage Guide

## Quick Start

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set Up Environment**:
   - Copy `.env.example` to `.env` (if needed)
   - Configure Ollama endpoint (default: http://localhost:11434)
   - Configure Qdrant (default: localhost:6333)

3. **Start Ollama** (if using Ollama models):
```bash
# Install Ollama from https://ollama.ai
# Pull models:
ollama pull llama3.2:1b
ollama pull mixtral:8x7b
```

4. **Start Qdrant** (if using local Qdrant):
```bash
docker run -p 6333:6333 qdrant/qdrant
```

5. **Run the Application**:
```bash
python src/main.py
```

## Features Implemented

### ✅ Dynamic Tool System
Agents can call any Python function as a tool:

```python
from src.tools.tool_registry import register_python_tool

@register_python_tool(description="My custom tool")
def my_custom_tool(param1: str, param2: int = 10):
    """Does something useful"""
    return f"{param1}: {param2}"

# Any agent can now call it:
# result = agent.call_python_tool("my_custom_tool", param1="test", param2=20)
```

### ✅ Streaming Responses
- Responses stream in real-time as they're generated
- No need to wait for complete response
- Better user experience

### ✅ Source Citations
- Clickable links to source documents
- Shows which documents were used
- Click to open source files

### ✅ Auto-Update System
- Automatically detects changes to Markdown files
- Re-indexes changed files
- Updates vector store in background

## Agent System

### Available Agents

1. **DocumentAgent**: Extracts and processes Markdown files
2. **RetrievalAgent**: Searches document chunks using multiple strategies
3. **FastLLMAgent**: Handles simple queries with fast models
4. **ComplexLLMAgent**: Handles complex queries with advanced models
5. **RouterAgent**: Routes queries to appropriate LLM
6. **MemoryAgent**: Manages chat history
7. **GUIAgent**: Manages user interface

### Adding Custom Tools

1. **Register a function**:
```python
from src.tools.tool_registry import register_python_tool

@register_python_tool(description="Tool description")
def my_tool(param: str):
    return f"Result: {param}"
```

2. **Call from any agent**:
```python
result = agent.call_python_tool("my_tool", param="value")
```

3. **List available tools**:
```python
tools = agent.list_available_tools()
print(tools['all'])  # All available tools
```

## Configuration

Settings are stored in `data/config.json` and can be modified via:
- GUI Settings window
- Direct JSON editing
- Environment variables

### Key Settings:
- `fast_llm`: Fast LLM configuration
- `complex_llm`: Complex LLM configuration
- `embedding_model`: Embedding model name
- `retrieval_strategy`: "semantic", "hybrid", or "reranking"
- `chunk_size`: Document chunk size (default: 500)
- `chunk_overlap`: Chunk overlap (default: 50)
- `top_k`: Number of results to retrieve (default: 5)

## Retrieval Strategies

1. **Semantic**: Vector similarity search only
2. **Hybrid**: Semantic + keyword search (BM25)
3. **Reranking**: Semantic search + LLM reranking

## Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check endpoint in settings: `http://localhost:11434`
- Verify models are pulled: `ollama list`

### Qdrant Connection Issues
- Check if Qdrant is running
- Verify host/port in environment variables
- Try file-based storage: Set `VECTOR_DB_DIR` in `.env`

### No Documents Found
- Place `docs.zip` or `database_docs.zip` in project root
- Or specify paths in settings

## Architecture

The system uses BMAD (Breakthrough Method for Agile AI-Driven Development) framework:

- **Agent-Based**: Each component is an independent agent
- **Tool System**: Dynamic tool registry for extensibility
- **Memory System**: Persistent chat history and context
- **Modular Design**: Easy to extend and maintain

## Extending the System

### Add New Agent
```python
from src.bmad.agent_base import BaseAgent, AgentRole

class MyAgent(BaseAgent):
    def __init__(self, framework=None):
        super().__init__(
            agent_id="my_agent",
            role=AgentRole.ROUTER,  # Choose appropriate role
            description="My custom agent",
            framework=framework
        )
    
    def process(self, input_data, **kwargs):
        # Your logic here
        return {"result": "success"}
```

### Add New Tool Module
1. Create file in `src/tools/`
2. Define functions
3. Import in `src/tools/__init__.py` (auto-registers)

## Next Steps

- Customize LLM models in settings
- Add your own tools
- Extend agents with new capabilities
- Integrate with other systems

