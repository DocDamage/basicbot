"""Retrieval Agent for document search"""

from typing import Dict, List, Any, Optional
import os

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.embedding_tools import create_embeddings, get_embedding_dimension
from ..tools.vector_tools import (
    initialize_collection,
    store_vectors,
    search_vectors,
    search_by_cas_number,
    search_by_article_number,
    search_by_hazard_tags,
    search_by_toxicity_type,
    search_by_listing_date,
    check_exposure_compliance
)
from ..tools.book_retrieval_tools import (
    search_by_title,
    search_by_author,
    search_by_series,
    search_by_character,
    search_by_quote,
    search_by_genre,
    get_full_book_text,
    get_book_metadata,
    get_related_books
)


class RetrievalAgent(BaseAgent):
    """Agent for retrieving relevant document chunks"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="semantic_search",
                description="Semantic search using vector similarity",
                func=self._semantic_search
            ),
            AgentTool(
                name="hybrid_search",
                description="Hybrid search (semantic + keyword)",
                func=self._hybrid_search
            ),
            AgentTool(
                name="rerank_results",
                description="Rerank search results using LLM",
                func=self._rerank_results
            ),
            AgentTool(
                name="search_by_cas_number",
                description="Search for documents by CAS registry number (exact match)",
                func=self._search_by_cas_number
            ),
            AgentTool(
                name="search_by_article_number",
                description="Search for documents by REACH article number",
                func=self._search_by_article_number
            ),
            AgentTool(
                name="search_by_hazard_tags",
                description="Search for documents by hazard classification tags",
                func=self._search_by_hazard_tags
            ),
            AgentTool(
                name="compliance_search",
                description="Compliance-specific search with multiple filters",
                func=self._compliance_search
            ),
            AgentTool(
                name="search_by_toxicity_type",
                description="Search for documents by Prop 65 toxicity type (cancer, reproductive, both)",
                func=self._search_by_toxicity_type
            ),
            AgentTool(
                name="search_by_listing_date",
                description="Search for documents by Prop 65 listing date range",
                func=self._search_by_listing_date
            ),
            AgentTool(
                name="check_exposure_compliance",
                description="Check if exposure exceeds Prop 65 NSRL/MADL thresholds",
                func=self._check_exposure_compliance
            ),
            AgentTool(
                name="search_books",
                description="Search books by title, author, series, character, quote, or genre",
                func=self._search_books
            ),
            AgentTool(
                name="get_book_full_text",
                description="Get complete text of a book by book ID",
                func=self._get_book_full_text
            ),
            AgentTool(
                name="browse_books_by_metadata",
                description="Browse books filtered by metadata (author, series, genre)",
                func=self._browse_books_by_metadata
            ),
            AgentTool(
                name="cross_reference_books",
                description="Find related books using semantic similarity and metadata",
                func=self._cross_reference_books
            )
        ]
        
        super().__init__(
            agent_id="retrieval_agent",
            role=AgentRole.RETRIEVAL,
            description="Retrieves relevant document chunks using multiple strategies",
            tools=tools,
            framework=framework
        )
        
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "rag_documents")
        self.top_k = int(os.getenv("TOP_K", "5"))
        self._collection_initialized = False
    
    def _initialize_collection(self):
        """Initialize Qdrant collection if not already done"""
        if self._collection_initialized:
            return
        
        vector_size = get_embedding_dimension(self.embedding_model)
        initialize_collection(self.collection_name, vector_size)
        self._collection_initialized = True
    
    def index_chunks(self, chunks: List[Dict], reindex: bool = False):
        """
        Index document chunks in vector store
        
        Args:
            chunks: List of chunk dictionaries
            reindex: Whether this is a reindexing operation
        """
        if not chunks:
            logger.warning("No chunks to index")
            return
        
        logger.info(f"Starting to index {len(chunks)} chunks...")
        self._initialize_collection()
        
        # Extract texts and metadata
        texts = [chunk['content'] for chunk in chunks]
        metadata_list = []
        for chunk in chunks:
            meta = {
                'source_file': chunk.get('source_file', ''),
                'section': chunk.get('section', {}),
                **chunk.get('metadata', {})
            }
            metadata_list.append(meta)
        
        # Create embeddings with progress
        logger.info(f"Generating embeddings for {len(texts)} chunks (this may take a while)...")
        batch_size = 100  # Process in batches for progress updates
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        all_embeddings = []
        for batch_idx in range(0, len(texts), batch_size):
            batch_texts = texts[batch_idx:batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            logger.debug(f"Embedding batch {batch_num}/{total_batches} ({len(batch_texts)} chunks)...")
            
            batch_embeddings = create_embeddings(
                batch_texts, 
                model_name=self.embedding_model,
                batch_size=32
            )
            
            if batch_embeddings:
                all_embeddings.extend(batch_embeddings)
            else:
                logger.warning(f"Failed to create embeddings for batch {batch_num}")
        
        if not all_embeddings:
            logger.error("Failed to create embeddings")
            return
        
        logger.info(f"Generated {len(all_embeddings)} embeddings. Storing in vector database...")
        
        # Store in Qdrant (also in batches for progress)
        all_point_ids = []
        for batch_idx in range(0, len(texts), batch_size):
            batch_texts = texts[batch_idx:batch_idx + batch_size]
            batch_embeddings = all_embeddings[batch_idx:batch_idx + batch_size]
            batch_metadata = metadata_list[batch_idx:batch_idx + batch_size]
            batch_num = (batch_idx // batch_size) + 1
            
            logger.debug(f"Storing batch {batch_num}/{total_batches}...")
            
            point_ids = store_vectors(
                texts=batch_texts,
                embeddings=batch_embeddings,
                metadata=batch_metadata,
                collection_name=self.collection_name
            )
            all_point_ids.extend(point_ids)
        
        logger.info(f"Indexed {len(all_point_ids)} chunks in vector store")
        
        # Store in memory
        if self.framework:
            self.framework.memory.store(
                self.agent_id,
                {"chunks_indexed": len(point_ids), "reindex": reindex},
                {"type": "indexing"}
            )
    
    def _semantic_search(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """Semantic search using vector similarity"""
        if top_k is None:
            top_k = self.top_k
        
        self._initialize_collection()
        
        # Create query embedding
        query_embeddings = create_embeddings([query], model_name=self.embedding_model)
        if not query_embeddings:
            return []
        
        # Search
        results = search_vectors(
            query_embedding=query_embeddings[0],
            top_k=top_k,
            collection_name=self.collection_name
        )
        
        return results
    
    def _hybrid_search(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """Hybrid search (semantic + keyword BM25)"""
        if top_k is None:
            top_k = self.top_k
        
        try:
            # Try to import BM25
            try:
                from rank_bm25 import BM25Okapi
                BM25_AVAILABLE = True
            except ImportError:
                BM25_AVAILABLE = False
                logger.warning("rank-bm25 not available, using semantic search only")
                return self._semantic_search(query, top_k)
            
            # Get semantic results
            semantic_results = self._semantic_search(query, top_k * 2)
            
            if not semantic_results or not BM25_AVAILABLE:
                return semantic_results[:top_k]
            
            # Extract texts for BM25
            texts = [r.get('text', '') for r in semantic_results]
            if not texts:
                return semantic_results[:top_k]
            
            # Tokenize for BM25
            tokenized_texts = [text.lower().split() for text in texts]
            tokenized_query = query.lower().split()
            
            # Create BM25 index
            bm25 = BM25Okapi(tokenized_texts)
            
            # Get BM25 scores
            bm25_scores = bm25.get_scores(tokenized_query)
            
            # Combine semantic and BM25 scores (weighted average)
            combined_results = []
            for i, result in enumerate(semantic_results):
                semantic_score = result.get('score', 0.0)
                bm25_score = bm25_scores[i] if i < len(bm25_scores) else 0.0
                
                # Normalize BM25 score (typically 0-10 range)
                normalized_bm25 = min(bm25_score / 10.0, 1.0) if bm25_score > 0 else 0.0
                
                # Weighted combination (70% semantic, 30% BM25)
                combined_score = 0.7 * semantic_score + 0.3 * normalized_bm25
                
                result_copy = result.copy()
                result_copy['score'] = combined_score
                result_copy['semantic_score'] = semantic_score
                result_copy['bm25_score'] = bm25_score
                combined_results.append(result_copy)
            
            # Sort by combined score
            combined_results.sort(key=lambda x: x.get('score', 0.0), reverse=True)
            
            return combined_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}", exc_info=True)
            # Fallback to semantic search
            return self._semantic_search(query, top_k)
    
    def _rerank_results(self, query: str, results: List[Dict], top_k: Optional[int] = None) -> List[Dict]:
        """Rerank results using fast LLM"""
        if top_k is None:
            top_k = self.top_k
        
        if not results:
            return []
        
        # Ask fast LLM to rerank
        if self.framework:
            fast_llm_agent = self.framework.get_agent("fast_llm_agent")
            if fast_llm_agent:
                # Create reranking prompt
                texts = [r['text'] for r in results]
                prompt = f"""Given the query: "{query}"

Rank these texts by relevance (most relevant first):
{chr(10).join(f"{i+1}. {text[:200]}..." for i, text in enumerate(texts))}

Return only the numbers in order of relevance, separated by commas."""
                
                try:
                    rerank_response = fast_llm_agent.execute_tool(
                        "call_llm",
                        prompt=prompt,
                        temperature=0.1
                    )
                    
                    # Parse reranking order
                    # Simple implementation - just return original order if parsing fails
                    try:
                        order = [int(x.strip()) - 1 for x in rerank_response.split(',')]
                        reranked = [results[i] for i in order if 0 <= i < len(results)]
                        return reranked[:top_k]
                    except:
                        return results[:top_k]
                except:
                    return results[:top_k]
        
        return results[:top_k]
    
    def _search_by_cas_number(self, cas_number: str, top_k: Optional[int] = None) -> List[Dict]:
        """Search by CAS number"""
        if top_k is None:
            top_k = self.top_k
        
        self._initialize_collection()
        return search_by_cas_number(cas_number, top_k, self.collection_name)
    
    def _search_by_article_number(self, article_number: str, top_k: Optional[int] = None) -> List[Dict]:
        """Search by article number"""
        if top_k is None:
            top_k = self.top_k
        
        self._initialize_collection()
        return search_by_article_number(article_number, top_k, self.collection_name)
    
    def _search_by_hazard_tags(
        self,
        hazard_tags: List[str],
        top_k: Optional[int] = None,
        match_all: bool = False
    ) -> List[Dict]:
        """Search by hazard tags"""
        if top_k is None:
            top_k = self.top_k
        
        self._initialize_collection()
        return search_by_hazard_tags(hazard_tags, top_k, self.collection_name, match_all)
    
    def _compliance_search(
        self,
        query: str,
        cas_number: Optional[str] = None,
        article_number: Optional[str] = None,
        hazard_tags: Optional[List[str]] = None,
        jurisdiction: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Compliance-specific search with multiple filters
        
        Args:
            query: Text query for semantic search
            cas_number: Filter by CAS number (exact match)
            article_number: Filter by article number
            hazard_tags: Filter by hazard tags
            jurisdiction: Filter by jurisdiction (EU, US, etc.)
            top_k: Number of results
        
        Returns:
            List of search results
        """
        if top_k is None:
            top_k = self.top_k
        
        self._initialize_collection()
        
        # If exact identifiers provided, use exact match first
        if cas_number:
            results = self._search_by_cas_number(cas_number, top_k)
            if results:
                return results
        
        if article_number:
            results = self._search_by_article_number(article_number, top_k)
            if results:
                return results
        
        # Otherwise, use semantic search with filters
        filter_metadata = {}
        if jurisdiction:
            filter_metadata['jurisdiction'] = jurisdiction
        
        # Create query embedding
        from ..tools.embedding_tools import create_embeddings
        query_embeddings = create_embeddings([query], model_name=self.embedding_model)
        if not query_embeddings:
            return []
        
        # Perform semantic search with filters
        results = search_vectors(
            query_embedding=query_embeddings[0],
            top_k=top_k * 2,  # Get more results to filter
            collection_name=self.collection_name,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        # Filter by hazard tags if provided
        if hazard_tags:
            filtered_results = []
            for result in results:
                result_tags = result.get('metadata', {}).get('hazard_tags', [])
                if isinstance(result_tags, str):
                    import json
                    try:
                        result_tags = json.loads(result_tags)
                    except:
                        result_tags = []
                
                if isinstance(result_tags, list):
                    if any(tag in result_tags for tag in hazard_tags):
                        filtered_results.append(result)
            
            results = filtered_results[:top_k]
        
        return results[:top_k]
    
    def _search_by_toxicity_type(
        self,
        toxicity_type: str,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """Search by toxicity type"""
        if top_k is None:
            top_k = self.top_k
        
        self._initialize_collection()
        return search_by_toxicity_type(toxicity_type, top_k, self.collection_name)
    
    def _search_by_listing_date(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """Search by listing date range"""
        if top_k is None:
            top_k = self.top_k
        
        self._initialize_collection()
        return search_by_listing_date(date_from, date_to, top_k, self.collection_name)
    
    def _check_exposure_compliance(
        self,
        cas_number: str,
        exposure_value: float,
        exposure_unit: str
    ) -> Dict[str, Any]:
        """Check exposure compliance"""
        self._initialize_collection()
        return check_exposure_compliance(cas_number, exposure_value, exposure_unit, self.collection_name)
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process retrieval request
        
        Args:
            input_data: Query string or dict with 'query' and 'strategy'
            **kwargs: Additional parameters (strategy, top_k, rerank, cas_number, article_number, hazard_tags, jurisdiction)
        """
        if isinstance(input_data, str):
            query = input_data
            strategy = kwargs.get('strategy', 'semantic')
        elif isinstance(input_data, dict):
            query = input_data.get('query', '')
            strategy = input_data.get('strategy', kwargs.get('strategy', 'semantic'))
        else:
            return {"error": "Invalid input"}
        
        top_k = kwargs.get('top_k', self.top_k)
        rerank = kwargs.get('rerank', False)
        
        # Check for compliance-specific search parameters
        cas_number = kwargs.get('cas_number') or (input_data.get('cas_number') if isinstance(input_data, dict) else None)
        article_number = kwargs.get('article_number') or (input_data.get('article_number') if isinstance(input_data, dict) else None)
        hazard_tags = kwargs.get('hazard_tags') or (input_data.get('hazard_tags') if isinstance(input_data, dict) else None)
        jurisdiction = kwargs.get('jurisdiction') or (input_data.get('jurisdiction') if isinstance(input_data, dict) else None)
        toxicity_type = kwargs.get('toxicity_type') or (input_data.get('toxicity_type') if isinstance(input_data, dict) else None)
        date_from = kwargs.get('date_from') or (input_data.get('date_from') if isinstance(input_data, dict) else None)
        date_to = kwargs.get('date_to') or (input_data.get('date_to') if isinstance(input_data, dict) else None)
        
        # Use Prop 65 specific searches
        if toxicity_type:
            results = self.execute_tool("search_by_toxicity_type", toxicity_type=toxicity_type, top_k=top_k)
        elif date_from or date_to:
            results = self.execute_tool("search_by_listing_date", date_from=date_from, date_to=date_to, top_k=top_k)
        # Use compliance search if any compliance filters are provided
        elif cas_number or article_number or hazard_tags or jurisdiction:
            results = self.execute_tool(
                "compliance_search",
                query=query,
                cas_number=cas_number,
                article_number=article_number,
                hazard_tags=hazard_tags,
                jurisdiction=jurisdiction,
                top_k=top_k
            )
        else:
            # Perform search based on strategy
            if strategy == 'semantic':
                results = self.execute_tool("semantic_search", query=query, top_k=top_k)
            elif strategy == 'hybrid':
                results = self.execute_tool("hybrid_search", query=query, top_k=top_k)
            else:
                results = self.execute_tool("semantic_search", query=query, top_k=top_k)
        
        # Rerank if requested
        if rerank and results:
            results = self.execute_tool("rerank_results", query=query, results=results, top_k=top_k)
        
        return {
            "query": query,
            "strategy": strategy,
            "results": results,
            "count": len(results),
            "filters": {
                "cas_number": cas_number,
                "article_number": article_number,
                "hazard_tags": hazard_tags,
                "jurisdiction": jurisdiction,
                "toxicity_type": toxicity_type,
                "date_from": date_from,
                "date_to": date_to
            }
        }
    
    def _search_books(self, query: str, search_type: str = "title", top_k: int = 10) -> List[Dict]:
        """
        Search books by various criteria
        
        Args:
            query: Search query
            search_type: Type of search (title, author, series, character, quote, genre)
            top_k: Number of results
            
        Returns:
            List of search results
        """
        search_type = search_type.lower()
        
        if search_type == "title":
            return search_by_title(query, top_k, self.collection_name)
        elif search_type == "author":
            return search_by_author(query, top_k, self.collection_name)
        elif search_type == "series":
            return search_by_series(query, top_k, self.collection_name)
        elif search_type == "character":
            return search_by_character(query, top_k, self.collection_name)
        elif search_type == "quote":
            return search_by_quote(query, top_k, self.collection_name)
        elif search_type == "genre":
            return search_by_genre(query, top_k, self.collection_name)
        else:
            # Default to semantic search
            return self._semantic_search(query, top_k)
    
    def _get_book_full_text(self, book_id: str) -> Dict[str, Any]:
        """
        Get full text of a book
        
        Args:
            book_id: Book ID
            
        Returns:
            Dictionary with book text and metadata
        """
        text = get_full_book_text(book_id)
        metadata = get_book_metadata(book_id)
        
        return {
            'book_id': book_id,
            'text': text,
            'metadata': metadata,
            'success': text is not None
        }
    
    def _browse_books_by_metadata(self, author: Optional[str] = None, series: Optional[str] = None, 
                                   genre: Optional[str] = None, top_k: int = 50) -> List[Dict]:
        """
        Browse books filtered by metadata
        
        Args:
            author: Filter by author
            series: Filter by series
            genre: Filter by genre
            top_k: Number of results
            
        Returns:
            List of book results
        """
        results = []
        
        if author:
            results = search_by_author(author, top_k, self.collection_name)
        elif series:
            results = search_by_series(series, top_k, self.collection_name)
        elif genre:
            results = search_by_genre(genre, top_k, self.collection_name)
        else:
            # Return all books (semantic search with empty query)
            query_embeddings = create_embeddings([""])
            if query_embeddings:
                results = search_vectors(
                    query_embedding=query_embeddings[0],
                    top_k=top_k,
                    collection_name=self.collection_name,
                    filter_metadata={'content_type': 'book'}
                )
        
        return results
    
    def _cross_reference_books(self, book_id: str, top_k: int = 10) -> List[Dict]:
        """
        Find related books using semantic similarity and metadata
        
        Args:
            book_id: Book ID
            top_k: Number of related books
            
        Returns:
            List of related book results
        """
        return get_related_books(book_id, top_k, self.collection_name)
    
    def receive_message(self, from_agent_id: str, message: Any, metadata: Optional[Dict] = None):
        """Handle messages from other agents"""
        if isinstance(message, dict):
            action = message.get('action')
            
            if action == 'index':
                chunks = message.get('chunks', [])
                self.index_chunks(chunks, reindex=False)
            
            elif action == 'reindex':
                chunks = message.get('chunks', [])
                file_path = message.get('file_path', '')
                self.index_chunks(chunks, reindex=True)

