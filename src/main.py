"""Main entry point for RAG Chatbot"""

# Python 3.13 compatibility fix - must be imported before any other imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.six_moves_compat import *  # noqa: F401, F403
except ImportError:
    # If the compat module doesn't exist, try inline fix
    import types
    import io
    import queue
    if 'six.moves' not in sys.modules:
        moves = types.ModuleType('six.moves')
        moves.__path__ = []
        sys.modules['six.moves'] = moves
        moves.StringIO = io.StringIO
        moves.cStringIO = io.StringIO
        moves.queue = queue
        moves.Queue = queue.Queue

import os
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


def initialize_documents(framework, progress_tracker=None):
    """Initialize documents from extracted directory or zip files"""
    from src.utils.indexing_progress import IndexingProgress
    
    if progress_tracker is None:
        progress_tracker = IndexingProgress()
    
    settings = get_settings()
    extracted_docs_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "rag_documents")
    
    # Check if files are already extracted
    extracted_path = Path(extracted_docs_dir)
    if extracted_path.exists():
        # Find all .md files in extracted directory
        all_md_files = list(extracted_path.rglob("*.md")) + list(extracted_path.rglob("*.markdown"))
        
        # Filter out non-content files (project documentation, not searchable content)
        # Common patterns: README, LICENSE, CHANGELOG, BUILD, INSTALL, etc.
        exclude_patterns = [
            'README', 'LICENSE', 'CHANGELOG', 'CONTRIBUTING', 'AUTHORS', 
            'COPYING', 'NOTICE', 'INSTALL', 'TODO', 'HISTORY', 'CHANGES', 
            'CREDITS', 'ACKNOWLEDGEMENTS', 'ACKNOWLEDGMENTS', 'CONTRIBUTORS',
            'MAINTAINERS', 'NOTES', 'RELEASE', 'VERSION', 'UPGRADE',
            'DEPLOYMENT', 'SETUP', 'BUILD', 'MAKEFILE'
        ]
        
        def is_content_file(file_path: Path) -> bool:
            """Check if file is actual content (not project documentation)"""
            name_upper = file_path.name.upper()
            # Check if filename contains any exclude pattern
            for pattern in exclude_patterns:
                if pattern in name_upper:
                    return False
            return True
        
        md_files = [f for f in all_md_files if is_content_file(f)]
        
        if md_files:
            print(f"Found {len(md_files)} already-extracted Markdown files")
            
            # Check which files are already indexed
            from src.tools.vector_tools import get_indexed_files
            import os
            
            print("Checking which files are already indexed...")
            indexed_files = get_indexed_files(collection_name=collection_name)
            print(f"Found {len(indexed_files)} files already indexed in vector database")
            
            # Normalize paths for comparison (handle absolute vs relative path mismatches)
            def normalize_path(path: str) -> str:
                """Normalize path for comparison (resolve to absolute, normalize separators)"""
                try:
                    # Convert to absolute path and normalize
                    abs_path = os.path.abspath(path)
                    # Normalize separators (Windows backslashes to forward slashes for consistency)
                    normalized = abs_path.replace('\\', '/')
                    return normalized.lower()  # Case-insensitive comparison
                except Exception:
                    # Fallback to original if normalization fails
                    return path.replace('\\', '/').lower()
            
            # Normalize indexed files set
            normalized_indexed = {normalize_path(f) for f in indexed_files}
            
            # Filter out already-indexed files using normalized paths
            md_file_paths = [str(f) for f in md_files]
            normalized_md_paths = {normalize_path(f): f for f in md_file_paths}
            
            new_files = [f for norm_path, f in normalized_md_paths.items() if norm_path not in normalized_indexed]
            already_indexed = [f for norm_path, f in normalized_md_paths.items() if norm_path in normalized_indexed]
            
            # Debug: Show sample paths if there's a mismatch
            if len(already_indexed) == 0 and len(new_files) > 0 and len(indexed_files) > 0:
                print("\n⚠️  Path mismatch detected! Sample paths:")
                print(f"  Sample indexed path: {list(indexed_files)[:1]}")
                print(f"  Sample file path: {md_file_paths[:1]}")
                print(f"  Normalized indexed: {list(normalized_indexed)[:1]}")
                print(f"  Normalized file: {list(normalized_md_paths.keys())[:1]}")
            
            print(f"  - Already indexed: {len(already_indexed)} files")
            print(f"  - Need indexing: {len(new_files)} files")
            print("=" * 60)
            
            if new_files:
                print("Processing new files from extracted directory...")
                # Start progress tracking
                progress_tracker.start(total_files=len(new_files))
                
                document_agent = framework.get_agent("document_agent")
                if document_agent:
                    # Process only new files (with progress tracking)
                    result = document_agent.process(
                        {"file_paths": new_files},
                        progress_tracker=progress_tracker
                    )
                    files_processed = result.get('files_processed', 0)
                    chunks_created = result.get('chunks_created', 0)
                    print("=" * 60)
                    print(f"✓ Document processing complete!")
                    print(f"  Files processed: {files_processed}")
                    print(f"  Chunks created: {chunks_created}")
                    print("=" * 60)
                    
                    # Index chunks incrementally
                    chunks = result.get("chunks", [])
                    if chunks:
                        print(f"\nStarting vector indexing for {len(chunks)} chunks...")
                        print("=" * 60)
                        progress_tracker.update_chunks(0, total=len(chunks))
                        
                        retrieval_agent = framework.get_agent("retrieval_agent")
                        if retrieval_agent:
                            # Index chunks with progress updates
                            retrieval_agent.index_chunks(chunks, progress_tracker=progress_tracker)
                            print("=" * 60)
                            print("✓ Chunks indexed in vector store")
                            print("=" * 60)
                        
                        progress_tracker.complete(f"Indexed {len(chunks)} chunks from {files_processed} files")
            else:
                print("✓ All files are already indexed. Skipping processing.")
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


def initialize_documents_background(framework):
    """Initialize documents in background thread"""
    import threading
    from src.utils.indexing_progress import IndexingProgress
    
    def background_indexing():
        progress_tracker = IndexingProgress()
        try:
            initialize_documents(framework, progress_tracker=progress_tracker)
        except Exception as e:
            print(f"Error in background indexing: {e}")
            progress_tracker.error(str(e))
            import traceback
            traceback.print_exc()
    
    thread = threading.Thread(target=background_indexing, daemon=True)
    thread.start()
    return thread


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
    
    # Start GUI immediately (don't wait for indexing)
    print("Starting GUI...")
    gui_agent = framework.get_agent("gui_agent")
    if gui_agent:
        # Start background indexing
        initialize_documents_background(framework)
        # Start GUI
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

