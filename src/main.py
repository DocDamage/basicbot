"""Main entry point for RAG Chatbot"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now import from src
from src.bmad.framework import BMADFramework
from src.agents import (
    DocumentAgent,
    RetrievalAgent,
    FastLLMAgent,
    ComplexLLMAgent,
    RouterAgent,
    MemoryAgent,
    GUIAgent,
    REACHExtractionAgent,
    ComplianceTaggingAgent,
    Prop65ExtractionAgent,
    BookAgent,
    WritingAgent,
    StyleAnalysisAgent,
    ContinuityAgent,
    ProjectAgent
)
from src.config import get_settings
from src.tools.tool_registry import get_tool_registry
from src.tools.vector_tools import initialize_collection
from src.tools.embedding_tools import get_embedding_dimension


def initialize_framework():
    """Initialize BMAD framework and register all agents"""
    # Create framework
    memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
    framework = BMADFramework(memory_storage_path=memory_path)
    
    # Get settings
    settings = get_settings()
    
    # Register agents
    document_agent = DocumentAgent(framework=framework)
    framework.register_agent(document_agent)
    
    retrieval_agent = RetrievalAgent(framework=framework)
    framework.register_agent(retrieval_agent)
    
    fast_llm_agent = FastLLMAgent(
        framework=framework,
        config=settings.get_fast_llm_config()
    )
    framework.register_agent(fast_llm_agent)
    
    complex_llm_agent = ComplexLLMAgent(
        framework=framework,
        config=settings.get_complex_llm_config()
    )
    framework.register_agent(complex_llm_agent)
    
    router_agent = RouterAgent(framework=framework)
    framework.register_agent(router_agent)
    
    memory_agent = MemoryAgent(framework=framework)
    framework.register_agent(memory_agent)
    
    gui_agent = GUIAgent(framework=framework)
    framework.register_agent(gui_agent)
    
    # Register book processing agent
    book_agent = BookAgent(framework=framework)
    framework.register_agent(book_agent)
    
    # Register writing agents
    writing_agent = WritingAgent(framework=framework)
    framework.register_agent(writing_agent)
    
    style_analysis_agent = StyleAnalysisAgent(framework=framework)
    framework.register_agent(style_analysis_agent)
    
    continuity_agent = ContinuityAgent(framework=framework)
    framework.register_agent(continuity_agent)
    
    project_agent = ProjectAgent(framework=framework)
    framework.register_agent(project_agent)
    
    # Register REACH compliance agents
    reach_extraction_agent = REACHExtractionAgent(framework=framework)
    framework.register_agent(reach_extraction_agent)
    
    compliance_tagging_agent = ComplianceTaggingAgent(framework=framework)
    framework.register_agent(compliance_tagging_agent)
    
    # Register Prop 65 extraction agent
    prop65_extraction_agent = Prop65ExtractionAgent(framework=framework)
    framework.register_agent(prop65_extraction_agent)
    
    return framework


def initialize_documents(framework):
    """Initialize documents from extracted directory or zip files"""
    settings = get_settings()
    extracted_docs_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    
    # Check if files are already extracted
    extracted_path = Path(extracted_docs_dir)
    if extracted_path.exists():
        # Find all .md files in extracted directory
        md_files = list(extracted_path.rglob("*.md")) + list(extracted_path.rglob("*.markdown"))
        
        if md_files:
            print(f"Found {len(md_files)} already-extracted Markdown files")
            print("Processing from extracted directory (skipping zip extraction)...")
            print("=" * 60)
            document_agent = framework.get_agent("document_agent")
            if document_agent:
                # Process files directly from extracted directory
                result = document_agent.process({"file_paths": [str(f) for f in md_files]})
                files_processed = result.get('files_processed', 0)
                chunks_created = result.get('chunks_created', 0)
                print("=" * 60)
                print(f"✓ Document processing complete!")
                print(f"  Files processed: {files_processed}")
                print(f"  Chunks created: {chunks_created}")
                print("=" * 60)
                
                # Index chunks
                chunks = result.get("chunks", [])
                if chunks:
                    print(f"\nStarting vector indexing for {len(chunks)} chunks...")
                    print("=" * 60)
                    retrieval_agent = framework.get_agent("retrieval_agent")
                    if retrieval_agent:
                        retrieval_agent.index_chunks(chunks)
                        print("=" * 60)
                        print("✓ Chunks indexed in vector store")
                        print("=" * 60)
            return
    
    # Fallback to zip extraction if no extracted files found
    zip_files = settings.get("zip_files", [])
    
    # Auto-detect zip files in current directory
    if not zip_files:
        current_dir = Path(".")
        zip_files = [
            str(f) for f in current_dir.glob("*.zip")
            if f.name in ["docs.zip", "database_docs.zip"]
        ]
        if zip_files:
            settings.set("zip_files", zip_files)
    
    if zip_files:
        print(f"Processing {len(zip_files)} zip file(s)...")
        print("=" * 60)
        document_agent = framework.get_agent("document_agent")
        if document_agent:
            result = document_agent.process({"zip_files": zip_files})
            files_processed = result.get('files_processed', 0)
            chunks_created = result.get('chunks_created', 0)
            print("=" * 60)
            print(f"✓ Document processing complete!")
            print(f"  Files processed: {files_processed}")
            print(f"  Chunks created: {chunks_created}")
            print("=" * 60)
            
            # Index chunks
            chunks = result.get("chunks", [])
            if chunks:
                print(f"\nStarting vector indexing for {len(chunks)} chunks...")
                print("=" * 60)
                retrieval_agent = framework.get_agent("retrieval_agent")
                if retrieval_agent:
                    retrieval_agent.index_chunks(chunks)
                    print("=" * 60)
                    print("✓ Chunks indexed in vector store")
                    print("=" * 60)
    else:
        print("No extracted files or zip files found.")


def main():
    """Main entry point"""
    print("Initializing RAG Chatbot with BMAD Framework...")
    
    # Initialize framework
    framework = initialize_framework()
    print("Framework initialized")
    
    # Initialize vector store
    settings = get_settings()
    embedding_model = settings.get_embedding_model()
    vector_size = get_embedding_dimension(embedding_model)
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "rag_documents")
    initialize_collection(collection_name, vector_size)
    print(f"Vector store initialized: {collection_name}")
    
    # Initialize documents
    initialize_documents(framework)
    
    # Start GUI
    print("Starting GUI...")
    gui_agent = framework.get_agent("gui_agent")
    if gui_agent:
        gui_agent.process({"action": "start"})
        
        # Keep main thread alive
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            framework.shutdown()
            sys.exit(0)
    else:
        print("GUI agent not found")
        sys.exit(1)


if __name__ == "__main__":
    main()

