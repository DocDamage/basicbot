import logging
from typing import List, Optional, Dict, Any
from entities.document import Document

logger = logging.getLogger(__name__)


class ContextualChunker:
    """
    Contextual chunking implementation based on Anthropic's contextual retrieval.
    Adds contextual information to chunks to improve retrieval quality.
    """

    def __init__(self, llm_client=None, context_window: int = 500):
        """
        Initialize the contextual chunker.

        Args:
            llm_client: LLM client for generating contextual information
            context_window: Maximum characters of document context to consider
        """
        self.llm_client = llm_client
        self.context_window = context_window

    def add_context_to_chunk(
        self,
        chunk: str,
        document: str,
        chunk_index: int = 0,
        total_chunks: int = 1
    ) -> str:
        """
        Add contextual information to a chunk.

        Args:
            chunk: The text chunk to contextualize
            document: The full document text
            chunk_index: Index of this chunk in the document
            total_chunks: Total number of chunks in the document

        Returns:
            Chunk with added contextual information
        """
        if not self.llm_client:
            logger.warning("No LLM client provided, returning original chunk")
            return chunk

        try:
            # Extract relevant document context
            document_context = self._extract_document_context(
                document, chunk, self.context_window
            )

            # Generate contextual explanation
            context_prompt = self._create_context_prompt(
                chunk, document_context, chunk_index, total_chunks
            )

            contextual_info = self.llm_client.generate_answer(
                context_prompt, max_new_tokens=100
            )

            # Combine context with chunk
            contextualized_chunk = f"Context: {contextual_info.strip()}\n\n{chunk}"

            return contextualized_chunk

        except Exception as e:
            logger.error(f"Error adding context to chunk: {e}")
            return chunk

    def _extract_document_context(
        self,
        document: str,
        chunk: str,
        context_window: int
    ) -> str:
        """
        Extract relevant context from the document around the chunk.
        """
        # Find chunk position in document
        chunk_start = document.find(chunk)
        if chunk_start == -1:
            # If exact match not found, take beginning of document
            return document[:context_window]

        # Extract context window around chunk
        context_start = max(0, chunk_start - context_window // 2)
        context_end = min(len(document), chunk_start + len(chunk) + context_window // 2)

        return document[context_start:context_end]

    def _create_context_prompt(
        self,
        chunk: str,
        document_context: str,
        chunk_index: int,
        total_chunks: int
    ) -> str:
        """
        Create a prompt for generating contextual information.
        """
        return f"""
Document context: {document_context[:300]}...

Chunk: {chunk}

Provide a brief 1-2 sentence explanation of how this chunk relates to the overall document context and its significance.
Focus on the key concepts, relationships, or insights this chunk provides.

Contextual explanation:"""

    def process_chunks(
        self,
        chunks: List[str],
        document: str,
        batch_size: int = 5
    ) -> List[str]:
        """
        Process multiple chunks to add contextual information.

        Args:
            chunks: List of text chunks
            document: Full document text
            batch_size: Number of chunks to process in each batch

        Returns:
            List of contextualized chunks
        """
        contextualized_chunks = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            for j, chunk in enumerate(batch):
                chunk_index = i + j
                contextualized = self.add_context_to_chunk(
                    chunk, document, chunk_index, len(chunks)
                )
                contextualized_chunks.append(contextualized)

                logger.info(f"Processed chunk {chunk_index + 1}/{len(chunks)}")

        return contextualized_chunks


class LateChunkingEmbedder:
    """
    Late chunking implementation based on Jina AI's approach.
    Embeds full documents first, then derives chunk embeddings.
    """

    def __init__(self, model_name: str = "jinaai/jina-embeddings-v2-base-en"):
        """
        Initialize the late chunking embedder.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Initialized late chunking embedder with model: {self.model_name}")
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.model = None

    def embed_with_late_chunking(
        self,
        document: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> tuple[List[str], List[List[float]]]:
        """
        Perform late chunking: embed full document, then derive chunk embeddings.

        Args:
            document: Full document text
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks

        Returns:
            Tuple of (chunks, embeddings)
        """
        if not self.model:
            raise RuntimeError("Model not initialized")

        # Embed full document
        full_embedding = self.model.encode(document)

        # Split into chunks
        chunks = self._split_document(document, chunk_size, overlap)

        # Compute contextual embeddings for each chunk
        chunk_embeddings = []
        for chunk in chunks:
            chunk_emb = self._compute_contextual_embedding(
                chunk, full_embedding, document
            )
            chunk_embeddings.append(chunk_emb)

        return chunks, chunk_embeddings

    def _split_document(
        self,
        document: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """
        Split document into overlapping chunks.
        """
        chunks = []
        start = 0

        while start < len(document):
            end = start + chunk_size

            # Find a good breaking point (sentence end)
            if end < len(document):
                # Look for sentence endings within the last 100 characters
                search_end = min(end, len(document))
                search_start = max(end - 100, start)

                sentence_end = document.rfind('.', search_start, search_end)
                if sentence_end == -1:
                    sentence_end = document.rfind(' ', search_start, search_end)
                if sentence_end == -1:
                    sentence_end = end

                end = sentence_end + 1  # Include the period/space

            chunk = document[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)

            # Move start position with overlap
            start = end - overlap

            # Ensure we don't get stuck
            if start >= end:
                break

        return chunks

    def _compute_contextual_embedding(
        self,
        chunk: str,
        full_doc_embedding: List[float],
        full_document: str
    ) -> List[float]:
        """
        Compute contextual embedding for a chunk using full document context.
        """
        # Simple approach: combine chunk embedding with full document embedding
        chunk_embedding = self.model.encode(chunk)

        # Weighted combination - give more weight to chunk-specific embedding
        chunk_weight = 0.7
        doc_weight = 0.3

        contextual_embedding = []
        for chunk_val, doc_val in zip(chunk_embedding, full_doc_embedding):
            contextual_embedding.append(
                chunk_weight * chunk_val + doc_weight * doc_val
            )

        return contextual_embedding

    def is_available(self) -> bool:
        """Check if the late chunking embedder is available."""
        return self.model is not None


class EnhancedTextSplitter:
    """
    Enhanced text splitter that supports both contextual chunking and late chunking.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        use_contextual: bool = False,
        use_late_chunking: bool = False,
        llm_client=None
    ):
        """
        Initialize enhanced text splitter.

        Args:
            chunk_size: Size of text chunks
            overlap: Overlap between chunks
            use_contextual: Whether to add contextual information
            use_late_chunking: Whether to use late chunking embeddings
            llm_client: LLM client for contextual chunking
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.use_contextual = use_contextual
        self.use_late_chunking = use_late_chunking

        self.contextual_chunker = ContextualChunker(llm_client) if use_contextual else None
        self.late_chunker = LateChunkingEmbedder() if use_late_chunking else None

    def split_and_process(
        self,
        document: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Split document and apply enhancements.

        Args:
            document: Full document text
            metadata: Document metadata

        Returns:
            List of processed Document objects
        """
        # Start with basic splitting
        if self.use_late_chunking and self.late_chunker:
            chunks, embeddings = self.late_chunker.embed_with_late_chunking(
                document, self.chunk_size, self.overlap
            )
        else:
            # Standard chunking
            chunks = self._basic_split(document)

        # Apply contextual chunking if enabled
        if self.use_contextual and self.contextual_chunker:
            chunks = self.contextual_chunker.process_chunks(chunks, document)

        # Create Document objects
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = metadata.copy() if metadata else {}
            doc_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "contextual": self.use_contextual,
                "late_chunking": self.use_late_chunking
            })

            # Add embedding if computed
            if self.use_late_chunking and 'embeddings' in locals():
                doc_metadata["embedding"] = embeddings[i]

            doc = Document(page_content=chunk, metadata=doc_metadata)
            documents.append(doc)

        return documents

    def _basic_split(self, document: str) -> List[str]:
        """
        Basic document splitting into chunks.
        """
        return self._split_document(document, self.chunk_size, self.overlap)

    def _split_document(
        self,
        document: str,
        chunk_size: int,
        overlap: int
    ) -> List[str]:
        """
        Split document into overlapping chunks.
        """
        chunks = []
        start = 0

        while start < len(document):
            end = start + chunk_size

            # Find sentence boundary
            if end < len(document):
                search_end = min(end, len(document))
                search_start = max(end - 50, start)

                boundary = document.rfind('. ', search_start, search_end)
                if boundary == -1:
                    boundary = document.rfind(' ', search_start, search_end)
                if boundary == -1:
                    boundary = end

                end = boundary + 1

            chunk = document[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap
            if start >= end:
                break

        return chunks
