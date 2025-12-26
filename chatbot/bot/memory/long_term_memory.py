import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Represents a single memory item."""
    user_id: str
    memory_type: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime = None
    last_accessed: datetime = None
    access_count: int = 0
    importance_score: float = 0.5

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = datetime.now()


class MemoryBackend(ABC):
    """Abstract base class for memory backends."""

    @abstractmethod
    def store(self, memory: MemoryItem) -> bool:
        """Store a memory item."""
        pass

    @abstractmethod
    def retrieve(self, user_id: str, query: str, limit: int = 10) -> List[MemoryItem]:
        """Retrieve relevant memories for a user."""
        pass

    @abstractmethod
    def get_all(self, user_id: str) -> List[MemoryItem]:
        """Get all memories for a user."""
        pass

    @abstractmethod
    def delete(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        pass

    @abstractmethod
    def cleanup(self, user_id: str, max_memories: int = 1000) -> int:
        """Clean up old/unimportant memories."""
        pass


class FileMemoryBackend(MemoryBackend):
    """Simple file-based memory backend."""

    def __init__(self, storage_path: str = "user_memories"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.embedder = None
        self._initialize_embedder()

    def _initialize_embedder(self):
        """Initialize embedder for similarity search."""
        try:
            from bot.memory.embedder import Embedder
            self.embedder = Embedder()
        except Exception as e:
            logger.warning(f"Could not initialize embedder: {e}")
            self.embedder = None

    def _get_user_file(self, user_id: str) -> Path:
        """Get the file path for a user's memories."""
        return self.storage_path / f"{user_id}_memories.json"

    def store(self, memory: MemoryItem) -> bool:
        """Store a memory item to file."""
        try:
            user_file = self._get_user_file(memory.user_id)

            # Load existing memories
            memories = self._load_memories(memory.user_id)

            # Generate embedding if embedder available
            if self.embedder and not memory.embedding:
                memory.embedding = self.embedder.embed_query(memory.content)

            # Add new memory
            memories.append(memory)

            # Save back to file
            self._save_memories(memory.user_id, memories)
            return True

        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False

    def retrieve(self, user_id: str, query: str, limit: int = 10) -> List[MemoryItem]:
        """Retrieve relevant memories using simple text matching."""
        try:
            memories = self._load_memories(user_id)

            if not memories:
                return []

            # Simple relevance scoring based on text overlap
            query_lower = query.lower()
            scored_memories = []

            for memory in memories:
                content_lower = memory.content.lower()
                relevance_score = 0.0

                # Simple word overlap scoring
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                overlap = len(query_words.intersection(content_words))

                if overlap > 0:
                    relevance_score = overlap / len(query_words)
                    relevance_score = min(relevance_score, 1.0)

                if relevance_score > 0.1:  # Minimum threshold
                    scored_memories.append((memory, relevance_score))

            # Sort by relevance and recency
            scored_memories.sort(key=lambda x: (x[1], x[0].last_accessed), reverse=True)

            # Update access information
            result = []
            for memory, score in scored_memories[:limit]:
                memory.last_accessed = datetime.now()
                memory.access_count += 1
                result.append(memory)

            # Save updated memories
            self._save_memories(user_id, memories)

            return result

        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []

    def get_all(self, user_id: str) -> List[MemoryItem]:
        """Get all memories for a user."""
        return self._load_memories(user_id)

    def delete(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        try:
            memories = self._load_memories(user_id)
            memories = [m for m in memories if getattr(m, 'id', None) != memory_id]
            self._save_memories(user_id, memories)
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False

    def cleanup(self, user_id: str, max_memories: int = 1000) -> int:
        """Clean up old/unimportant memories."""
        try:
            memories = self._load_memories(user_id)

            if len(memories) <= max_memories:
                return 0

            # Sort by importance and recency
            memories.sort(key=lambda m: (m.importance_score, m.last_accessed), reverse=True)

            # Keep only the top memories
            kept_memories = memories[:max_memories]
            removed_count = len(memories) - len(kept_memories)

            self._save_memories(user_id, kept_memories)
            return removed_count

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

    def _load_memories(self, user_id: str) -> List[MemoryItem]:
        """Load memories from file."""
        user_file = self._get_user_file(user_id)

        if not user_file.exists():
            return []

        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            memories = []
            for item in data:
                # Convert datetime strings back to datetime objects
                if 'created_at' in item:
                    item['created_at'] = datetime.fromisoformat(item['created_at'])
                if 'last_accessed' in item:
                    item['last_accessed'] = datetime.fromisoformat(item['last_accessed'])

                memories.append(MemoryItem(**item))

            return memories

        except Exception as e:
            logger.error(f"Error loading memories: {e}")
            return []

    def _save_memories(self, user_id: str, memories: List[MemoryItem]):
        """Save memories to file."""
        user_file = self._get_user_file(user_id)

        # Convert to serializable format
        data = []
        for memory in memories:
            memory_dict = asdict(memory)
            # Convert datetime objects to ISO strings
            if memory_dict['created_at']:
                memory_dict['created_at'] = memory_dict['created_at'].isoformat()
            if memory_dict['last_accessed']:
                memory_dict['last_accessed'] = memory_dict['last_accessed'].isoformat()
            data.append(memory_dict)

        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class Mem0MemoryBackend(MemoryBackend):
    """Mem0-based memory backend."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MEM0_API_KEY")
        self.mem0_client = None
        self._initialize_mem0()

    def _initialize_mem0(self):
        """Initialize Mem0 client."""
        try:
            from mem0 import Memory
            self.mem0_client = Memory(api_key=self.api_key)
            logger.info("Initialized Mem0 memory backend")
        except ImportError:
            logger.error("Mem0 not installed. Install with: pip install mem0ai")
            self.mem0_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            self.mem0_client = None

    def store(self, memory: MemoryItem) -> bool:
        """Store a memory using Mem0."""
        if not self.mem0_client:
            return False

        try:
            # Mem0 add method
            self.mem0_client.add(
                content=memory.content,
                user_id=memory.user_id,
                metadata={
                    "type": memory.memory_type,
                    "importance": memory.importance_score,
                    **memory.metadata
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error storing memory with Mem0: {e}")
            return False

    def retrieve(self, user_id: str, query: str, limit: int = 10) -> List[MemoryItem]:
        """Retrieve memories using Mem0."""
        if not self.mem0_client:
            return []

        try:
            # Mem0 search method
            results = self.mem0_client.search(
                query=query,
                user_id=user_id,
                limit=limit
            )

            memories = []
            for result in results:
                memory = MemoryItem(
                    user_id=user_id,
                    memory_type=result.get("metadata", {}).get("type", "conversation"),
                    content=result.get("content", ""),
                    metadata=result.get("metadata", {}),
                    importance_score=result.get("metadata", {}).get("importance", 0.5)
                )
                memories.append(memory)

            return memories

        except Exception as e:
            logger.error(f"Error retrieving memories with Mem0: {e}")
            return []

    def get_all(self, user_id: str) -> List[MemoryItem]:
        """Get all memories for a user."""
        if not self.mem0_client:
            return []

        try:
            # This is a simplified implementation
            # Mem0 might not have a direct "get_all" method
            return self.retrieve(user_id, "", limit=1000)
        except Exception as e:
            logger.error(f"Error getting all memories with Mem0: {e}")
            return []

    def delete(self, user_id: str, memory_id: str) -> bool:
        """Delete a memory (Mem0 may not support this)."""
        logger.warning("Mem0 backend does not support direct memory deletion")
        return False

    def cleanup(self, user_id: str, max_memories: int = 1000) -> int:
        """Cleanup (Mem0 handles this internally)."""
        logger.info("Mem0 handles memory cleanup internally")
        return 0


class LongTermMemory:
    """
    Long-term memory system with multiple backend options.
    Provides persistent memory across sessions.
    """

    def __init__(
        self,
        backend: str = "file",
        backend_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize long-term memory.

        Args:
            backend: Backend type ('file', 'mem0', 'postgres')
            backend_config: Configuration for the backend
        """
        self.backend_type = backend
        self.backend_config = backend_config or {}
        self.backend = self._initialize_backend()

        # Initialize embedder for importance calculation
        self.embedder = None
        self._initialize_embedder()

    def _initialize_backend(self) -> MemoryBackend:
        """Initialize the appropriate backend."""
        if self.backend_type == "file":
            storage_path = self.backend_config.get("storage_path", "user_memories")
            return FileMemoryBackend(storage_path)
        elif self.backend_type == "mem0":
            api_key = self.backend_config.get("api_key")
            return Mem0MemoryBackend(api_key)
        else:
            logger.warning(f"Unknown backend: {self.backend_type}, using file backend")
            return FileMemoryBackend()

    def _initialize_embedder(self):
        """Initialize embedder for memory processing."""
        try:
            from bot.memory.embedder import Embedder
            self.embedder = Embedder()
        except Exception as e:
            logger.warning(f"Could not initialize embedder: {e}")

    def remember(
        self,
        user_id: str,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a new memory.

        Args:
            user_id: User identifier
            content: Memory content
            memory_type: Type of memory (conversation, preference, fact, etc.)
            metadata: Additional metadata

        Returns:
            Success status
        """
        metadata = metadata or {}

        # Calculate importance score
        importance = self._calculate_importance(content, memory_type)

        memory = MemoryItem(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            importance_score=importance
        )

        return self.backend.store(memory)

    def recall(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[str]:
        """
        Retrieve relevant memories.

        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of memories to return

        Returns:
            List of memory contents
        """
        memories = self.backend.retrieve(user_id, query, limit)
        return [memory.content for memory in memories]

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive user profile from memories.

        Args:
            user_id: User identifier

        Returns:
            User profile dictionary
        """
        memories = self.backend.get_all(user_id)

        profile = {
            "user_id": user_id,
            "total_memories": len(memories),
            "memory_types": {},
            "preferences": [],
            "facts": [],
            "conversation_history": []
        }

        for memory in memories:
            # Count memory types
            mem_type = memory.memory_type
            profile["memory_types"][mem_type] = profile["memory_types"].get(mem_type, 0) + 1

            # Categorize memories
            if mem_type == "preference":
                profile["preferences"].append(memory.content)
            elif mem_type == "fact":
                profile["facts"].append(memory.content)
            elif mem_type == "conversation":
                profile["conversation_history"].append({
                    "content": memory.content,
                    "timestamp": memory.created_at.isoformat() if memory.created_at else None
                })

        return profile

    def summarize_conversation(
        self,
        conversation: List[Dict[str, str]],
        user_id: str
    ) -> str:
        """
        Create a summary of a conversation for long-term storage.

        Args:
            conversation: List of conversation messages
            user_id: User identifier

        Returns:
            Conversation summary
        """
        if not conversation:
            return ""

        # Simple conversation summarization
        user_messages = [msg for msg in conversation if msg.get("role") == "user"]
        assistant_messages = [msg for msg in conversation if msg.get("role") == "assistant"]

        summary_parts = []

        if user_messages:
            summary_parts.append(f"User asked about: {user_messages[0].get('content', '')[:100]}...")

        if assistant_messages:
            summary_parts.append(f"Assistant responded with information about the query")

        # Calculate conversation importance
        total_length = sum(len(msg.get("content", "")) for msg in conversation)
        importance = min(total_length / 1000, 1.0)  # Longer conversations are more important

        summary = " ".join(summary_parts)

        # Store the summary as a memory
        self.remember(
            user_id=user_id,
            content=summary,
            memory_type="conversation_summary",
            metadata={
                "message_count": len(conversation),
                "importance": importance
            }
        )

        return summary

    def _calculate_importance(self, content: str, memory_type: str) -> float:
        """
        Calculate importance score for a memory.

        Args:
            content: Memory content
            memory_type: Type of memory

        Returns:
            Importance score (0-1)
        """
        base_score = 0.5

        # Type-based scoring
        type_scores = {
            "preference": 0.8,
            "fact": 0.7,
            "conversation": 0.4,
            "conversation_summary": 0.6
        }

        base_score = type_scores.get(memory_type, 0.5)

        # Content-based scoring
        content_lower = content.lower()

        # Keywords that indicate importance
        important_keywords = [
            "always", "never", "prefer", "favorite", "hate", "love",
            "important", "remember", "key", "critical", "essential"
        ]

        keyword_matches = sum(1 for keyword in important_keywords if keyword in content_lower)
        keyword_boost = min(keyword_matches * 0.1, 0.3)

        # Length-based scoring (longer content might be more important)
        length_score = min(len(content) / 500, 0.2)

        importance = base_score + keyword_boost + length_score
        return min(importance, 1.0)

    def cleanup_user_memories(self, user_id: str, max_memories: int = 1000) -> int:
        """
        Clean up old/unimportant memories for a user.

        Args:
            user_id: User identifier
            max_memories: Maximum number of memories to keep

        Returns:
            Number of memories removed
        """
        return self.backend.cleanup(user_id, max_memories)

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """
        Delete a specific memory.

        Args:
            user_id: User identifier
            memory_id: Memory identifier

        Returns:
            Success status
        """
        return self.backend.delete(user_id, memory_id)

    def is_available(self) -> bool:
        """Check if long-term memory is available."""
        return self.backend is not None


class MemoryManager:
    """
    High-level memory management interface.
    """

    def __init__(self, memory_system: LongTermMemory):
        self.memory = memory_system

    def add_conversation_memory(
        self,
        user_id: str,
        question: str,
        answer: str,
        importance_threshold: float = 0.6
    ):
        """
        Add conversation memory if it meets importance criteria.

        Args:
            user_id: User identifier
            question: User's question
            answer: Assistant's answer
            importance_threshold: Minimum importance to store
        """
        content = f"Q: {question}\nA: {answer}"

        # Calculate if this conversation is worth remembering
        importance = self.memory._calculate_importance(content, "conversation")

        if importance >= importance_threshold:
            self.memory.remember(
                user_id=user_id,
                content=content,
                memory_type="conversation",
                metadata={"importance": importance}
            )

    def get_memory_context(self, user_id: str, current_query: str, max_memories: int = 3) -> str:
        """
        Get relevant memory context for a query.

        Args:
            user_id: User identifier
            current_query: Current user query
            max_memories: Maximum memories to include

        Returns:
            Formatted memory context
        """
        memories = self.memory.recall(user_id, current_query, max_memories)

        if not memories:
            return ""

        context_parts = ["Previous relevant information:"]
        for memory in memories:
            context_parts.append(f"- {memory}")

        return "\n".join(context_parts)
