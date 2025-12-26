"""BMAD Memory System for context retention and chat history"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class MemoryEntry:
    """Single memory entry"""
    timestamp: str
    agent_id: str
    content: Any
    metadata: Dict[str, Any]


class MemorySystem:
    """BMAD Memory System for managing context and chat history"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize memory system
        
        Args:
            storage_path: Path to store persistent memory (None for in-memory only)
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.memories: List[MemoryEntry] = []
        self.agent_contexts: Dict[str, List[MemoryEntry]] = {}
        
        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self._load_memories()
    
    def _load_memories(self):
        """Load memories from disk"""
        if not self.storage_path:
            return
        
        memory_file = self.storage_path / "memories.json"
        if memory_file.exists():
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memories = [
                        MemoryEntry(**entry) for entry in data.get('memories', [])
                    ]
                    # Reconstruct agent contexts
                    for entry in self.memories:
                        if entry.agent_id not in self.agent_contexts:
                            self.agent_contexts[entry.agent_id] = []
                        self.agent_contexts[entry.agent_id].append(entry)
            except Exception as e:
                print(f"Error loading memories: {e}")
    
    def _save_memories(self):
        """Save memories to disk"""
        if not self.storage_path:
            return
        
        memory_file = self.storage_path / "memories.json"
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'memories': [asdict(entry) for entry in self.memories]
                }, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving memories: {e}")
    
    def store(self, agent_id: str, content: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a memory entry
        
        Args:
            agent_id: ID of the agent storing the memory
            content: Content to store
            metadata: Optional metadata
            
        Returns:
            Memory entry ID
        """
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            content=content,
            metadata=metadata or {}
        )
        
        self.memories.append(entry)
        
        if agent_id not in self.agent_contexts:
            self.agent_contexts[agent_id] = []
        self.agent_contexts[agent_id].append(entry)
        
        self._save_memories()
        
        return entry.timestamp
    
    def retrieve(self, agent_id: str, limit: int = 10) -> List[MemoryEntry]:
        """
        Retrieve recent memories for an agent
        
        Args:
            agent_id: ID of the agent
            limit: Maximum number of entries to retrieve
            
        Returns:
            List of memory entries
        """
        if agent_id not in self.agent_contexts:
            return []
        
        return self.agent_contexts[agent_id][-limit:]
    
    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """
        Search memories by content (simple text search)
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching memory entries
        """
        query_lower = query.lower()
        matches = []
        
        for entry in reversed(self.memories):
            content_str = str(entry.content).lower()
            if query_lower in content_str:
                matches.append(entry)
                if len(matches) >= limit:
                    break
        
        return matches
    
    def get_conversation_history(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            List of conversation entries
        """
        history = []
        for entry in self.memories:
            if entry.metadata.get('type') == 'conversation':
                if session_id is None or entry.metadata.get('session_id') == session_id:
                    history.append({
                        'timestamp': entry.timestamp,
                        'role': entry.metadata.get('role', 'assistant'),
                        'content': entry.content,
                        'sources': entry.metadata.get('sources', [])
                    })
        
        return history
    
    def clear_agent_context(self, agent_id: str):
        """Clear context for a specific agent"""
        if agent_id in self.agent_contexts:
            # Remove from memories
            self.memories = [
                m for m in self.memories if m.agent_id != agent_id
            ]
            del self.agent_contexts[agent_id]
            self._save_memories()

