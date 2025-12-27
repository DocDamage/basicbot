"""Agent Tools"""

from .document_tools import extract_markdown_from_zip, parse_markdown_structure
from .chunking_tools import hybrid_chunk_markdown
from .embedding_tools import create_embeddings
from .vector_tools import store_vectors, search_vectors, get_indexed_files, is_file_indexed
from .llm_tools import call_llm, stream_llm
from .tool_registry import (
    ToolRegistry,
    get_tool_registry,
    register_python_tool,
    call_any_tool
)

__all__ = [
    "extract_markdown_from_zip",
    "parse_markdown_structure",
    "hybrid_chunk_markdown",
    "create_embeddings",
    "store_vectors",
    "search_vectors",
    "get_indexed_files",
    "is_file_indexed",
    "call_llm",
    "stream_llm",
    "ToolRegistry",
    "get_tool_registry",
    "register_python_tool",
    "call_any_tool"
]

# Auto-register all tools from this module
def _auto_register_tools():
    """Auto-register all tools from this package"""
    registry = get_tool_registry()
    
    # Register existing modules
    registry.register_module('src.tools.document_tools')
    registry.register_module('src.tools.chunking_tools')
    registry.register_module('src.tools.embedding_tools')
    registry.register_module('src.tools.vector_tools')
    registry.register_module('src.tools.llm_tools')
    
    # Register new comprehensive tool modules
    registry.register_module('src.tools.file_operations_tools')
    registry.register_module('src.tools.archive_tools')
    registry.register_module('src.tools.network_tools')
    registry.register_module('src.tools.data_processing_tools')
    registry.register_module('src.tools.system_tools')
    registry.register_module('src.tools.text_processing_tools')
    registry.register_module('src.tools.image_tools')
    registry.register_module('src.tools.hash_tools')
    registry.register_module('src.tools.path_tools')
    registry.register_module('src.tools.datetime_tools')
    registry.register_module('src.tools.math_tools')
    registry.register_module('src.tools.database_tools')
    registry.register_module('src.tools.pdf_tools')
    registry.register_module('src.tools.office_tools')
    registry.register_module('src.tools.compression_tools')
    registry.register_module('src.tools.media_tools')
    registry.register_module('src.tools.book_tools')
    registry.register_module('src.tools.entity_extraction_tools')
    registry.register_module('src.tools.book_retrieval_tools')
    registry.register_module('src.tools.writing_tools')
    registry.register_module('src.tools.model_manager')

# Auto-register on import
_auto_register_tools()

