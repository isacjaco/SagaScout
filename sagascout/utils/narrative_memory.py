"""Narrative memory system for SagaScout agents."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class NarrativeMemory:
    """
    Narrative-driven memory system for agents.
    
    Stores events as narrative memories with context, emotional significance,
    and connections to other memories.
    """

    def __init__(self):
        """Initialize narrative memory system."""
        self.memories = []
        self.memory_index = {}
        self.memory_connections = {}

    def store_memory(
        self,
        event_type: str,
        content: Dict[str, Any],
        significance: float = 0.5,
        tags: List[str] = None,
    ) -> str:
        """
        Store a narrative memory.

        Args:
            event_type: Type of event (e.g., 'discovery', 'connection', 'conflict')
            content: Event content and context
            significance: Emotional/narrative significance (0.0 to 1.0)
            tags: Tags for categorization

        Returns:
            Memory ID
        """
        memory_id = f"mem_{len(self.memories)}"
        
        memory = {
            "id": memory_id,
            "type": event_type,
            "content": content,
            "significance": significance,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat(),
            "connections": [],
        }

        self.memories.append(memory)
        self.memory_index[memory_id] = memory
        self.memory_connections[memory_id] = []

        # Auto-tag based on content
        self._auto_tag_memory(memory)

        return memory_id

    def recall_memories(
        self,
        query: Optional[str] = None,
        event_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_significance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Recall memories based on criteria.

        Args:
            query: Text query to search in content
            event_type: Filter by event type
            tags: Filter by tags
            min_significance: Minimum significance threshold

        Returns:
            List of matching memories
        """
        results = []

        for memory in self.memories:
            # Apply filters
            if event_type and memory["type"] != event_type:
                continue
            
            if memory["significance"] < min_significance:
                continue
            
            if tags and not any(tag in memory["tags"] for tag in tags):
                continue
            
            if query:
                content_str = str(memory["content"]).lower()
                if query.lower() not in content_str:
                    continue

            results.append(memory)

        # Sort by significance and recency
        results.sort(
            key=lambda m: (m["significance"], m["timestamp"]),
            reverse=True,
        )

        return results

    def connect_memories(self, memory_id1: str, memory_id2: str, 
                        connection_type: str = "related") -> None:
        """
        Create a connection between two memories.

        Args:
            memory_id1: First memory ID
            memory_id2: Second memory ID
            connection_type: Type of connection
        """
        if memory_id1 in self.memory_index and memory_id2 in self.memory_index:
            connection = {
                "to": memory_id2,
                "type": connection_type,
            }
            
            self.memory_index[memory_id1]["connections"].append(connection)
            self.memory_connections[memory_id1].append(memory_id2)

    def get_memory_narrative(self, memory_id: str) -> Dict[str, Any]:
        """
        Get a memory with its narrative context (connections, related memories).

        Args:
            memory_id: Memory ID

        Returns:
            Memory with narrative context
        """
        if memory_id not in self.memory_index:
            return {}

        memory = self.memory_index[memory_id]
        connected_ids = self.memory_connections.get(memory_id, [])
        connected_memories = [
            self.memory_index[mid] for mid in connected_ids
            if mid in self.memory_index
        ]

        return {
            "memory": memory,
            "connected_memories": connected_memories,
            "narrative_thread": self._build_narrative_thread(memory_id),
        }

    def _auto_tag_memory(self, memory: Dict[str, Any]) -> None:
        """Automatically add tags based on memory content."""
        content_str = str(memory["content"]).lower()
        
        # DNA-related tags
        if any(word in content_str for word in ["dna", "match", "centimorgans"]):
            memory["tags"].append("dna")
        
        # Research tags
        if any(word in content_str for word in ["research", "archive", "document"]):
            memory["tags"].append("research")
        
        # Communication tags
        if any(word in content_str for word in ["message", "contact", "outreach"]):
            memory["tags"].append("communication")
        
        # Discovery tags
        if any(word in content_str for word in ["found", "discovered", "identified"]):
            memory["tags"].append("discovery")

    def _build_narrative_thread(self, memory_id: str,
                                depth: int = 3) -> List[Dict[str, Any]]:
        """Build a narrative thread from a memory."""
        if depth == 0 or memory_id not in self.memory_index:
            return []

        thread = [self.memory_index[memory_id]]
        connected = self.memory_connections.get(memory_id, [])

        for conn_id in connected[:2]:  # Limit to 2 connections per level
            thread.extend(self._build_narrative_thread(conn_id, depth - 1))

        return thread

    # ------------------------------------------------------------------ #
    # JSON serialization                                                   #
    # ------------------------------------------------------------------ #

    def to_json(self) -> Dict[str, Any]:
        """
        Serialize all memories and connections to a JSON-compatible dictionary.

        Returns:
            Dictionary containing memories list and connection map
        """
        return {
            "memories": self.memories,
            "connections": {
                mid: list(targets)
                for mid, targets in self.memory_connections.items()
            },
        }

    def save_to_file(self, filepath: str) -> None:
        """
        Save memories to a JSON file.

        Args:
            filepath: Destination file path
        """
        Path(filepath).write_text(
            json.dumps(self.to_json(), indent=2), encoding="utf-8"
        )

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "NarrativeMemory":
        """
        Restore a NarrativeMemory from a previously serialized dictionary.

        Args:
            data: Dictionary as returned by :meth:`to_json`

        Returns:
            NarrativeMemory instance populated with the saved state
        """
        nm = cls()
        for memory in data.get("memories", []):
            nm.memories.append(memory)
            nm.memory_index[memory["id"]] = memory
        for mid, targets in data.get("connections", {}).items():
            nm.memory_connections[mid] = list(targets)
        return nm

    @classmethod
    def load_from_file(cls, filepath: str) -> "NarrativeMemory":
        """
        Load a NarrativeMemory from a JSON file saved by :meth:`save_to_file`.

        Args:
            filepath: Source file path

        Returns:
            NarrativeMemory instance populated with the saved state
        """
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        return cls.from_json(data)


# Backward-compatible re-export so existing imports still work
from sagascout.utils.governance import GovernanceRitual  # noqa: F401, E402

