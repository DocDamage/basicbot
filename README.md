# Axiom Math Chatbot

A specialized, locally embedded conversational AI built for advanced mathematical reasoning using the **MBAD (Multi-Branch Agent Debate)** method.

## features

- **MBAD Architecture**: Utilizes 4 local LLMs in tandem:
  - **Agent Alpha (Math)**: Rigorous step-by-step solver.
  - **Agent Beta (Math)**: Independent verifier/solver.
  - **Coordinator**: Synthesizes results and detects discrepancies.
  - **Chat Agent**: Handles general conversation and context.
- **RAG Integration**: Retrieves context from local documents (`/rag_data`).
- **Locally Embedded**: Powered by **Ollama**, ensuring complete privacy and offline capability.
- **Premium UI**: Glassmorphism design with real-time "Tandem" visualization.

## Prerequisites

1. **Ollama**: Must be installed and running.
2. **Small Models (SLMs)**: Pull the high-efficiency models:

    ```bash
    ollama pull phi3
    ollama pull gemma2:2b
    ollama pull qwen2:1.5b
    ollama pull nomic-embed-text
    ```

## Quick Start

1. **Install Dependencies**:

    ```bash
    pip install -r backend/requirements.txt
    cd frontend && npm install
    ```

2. **Run System**:

    ```powershell
    .\start_axiom.ps1
    ```

    *Or manually:*
    - Backend: `cd backend && uvicorn main:app --reload`
    - Frontend: `cd frontend && npm run dev`

## Architecture

The system uses a Python (FastAPI) backend to orchestrate the agents. When a math question is detected:

1. **Parallel Execution**: Agents Alpha and Beta solve the problem independently.
2. **Debate/Synthesis**: The Coordinator evaluates both solutions.
3. **Visualization**: The Frontend displays the internal monologue of both agents side-by-side before revealing the final synthesized answer.
