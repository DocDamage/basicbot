# RAG Chatbot with Markdown Sources (BMAD Framework)

A Python-based RAG (Retrieval-Augmented Generation) chatbot that reads Markdown files from zip archives, supports multiple free/open-source LLM options with IDE-style selection, and implements a dual LLM architecture (fast + complex) using BMAD's agent-based system.

## Features

- ✅ Extract MD files from zip archives
- ✅ Hybrid chunking (structure + size)
- ✅ Multiple retrieval strategies (semantic, hybrid, reranking)
- ✅ Dual LLM system (fast + complex)
- ✅ IDE-style model selection
- ✅ GUI with streaming responses
- ✅ Source citations
- ✅ Chat history persistence
- ✅ Auto-reindexing on file changes
- ✅ Configurable via GUI settings

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd basicbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Install and start Ollama (if using Ollama models):
```bash
# Visit https://ollama.ai for installation instructions
# Pull models: ollama pull llama3.2:1b ollama pull mixtral:8x7b
```

5. Start Qdrant (if using local Qdrant):
```bash
docker run -p 6333:6333 qdrant/qdrant
```

## Project Structure

See `docs/PROJECT_STRUCTURE.md` for detailed directory organization.

Key directories:
- `src/` - Source code (agents, tools, GUI)
- `docs/` - Documentation files
- `scripts/` - Utility scripts
- `data/` - Data storage (archives, extracted docs, vector DB)
- `books/` - Book collection

## Usage

1. Place your Markdown zip files in `data/archives/` or extract them to `data/extracted_docs/`
2. Run the application:
```bash
python src/main.py
```

3. On first run, configure:
   - Fast LLM selection
   - Complex LLM selection
   - Embedding model
   - Retrieval strategy
   - Path to zip files

4. The GUI will launch and you can start chatting!

## Project Structure

See `IMPLEMENTATION_PLAN.md` for detailed architecture and implementation details.

## Configuration

Configuration is managed through the GUI settings window and stored in `data/config.json`.

## License

[Your License Here]

