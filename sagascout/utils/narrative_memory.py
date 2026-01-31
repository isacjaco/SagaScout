"""Narrative memory and governance rituals for SagaScout agents."""

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


class GovernanceRitual:
    """
    Governance rituals for agent coordination and decision-making.
    
    Implements structured decision-making processes and coordination
    mechanisms for the agent ecosystem.
    """

    def __init__(self):
        """Initialize governance system."""
        self.rituals = {}
        self.decisions = []
        self.council_history = []

    def create_ritual(
        self, name: str, ritual_type: str, participants: List[str],
        rules: Dict[str, Any]
    ) -> str:
        """
        Create a governance ritual.

        Args:
            name: Ritual name
            ritual_type: Type of ritual ('decision', 'coordination', 'review')
            participants: List of agent names participating
            rules: Rules and parameters for the ritual

        Returns:
            Ritual ID
        """
        ritual_id = f"ritual_{len(self.rituals)}"
        
        ritual = {
            "id": ritual_id,
            "name": name,
            "type": ritual_type,
            "participants": participants,
            "rules": rules,
            "created": datetime.now().isoformat(),
            "executions": [],
        }

        self.rituals[ritual_id] = ritual
        return ritual_id

    def execute_ritual(
        self, ritual_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a governance ritual.

        Args:
            ritual_id: Ritual ID
            context: Context for ritual execution

        Returns:
            Ritual execution results
        """
        if ritual_id not in self.rituals:
            return {"error": "Ritual not found"}

        ritual = self.rituals[ritual_id]
        ritual_type = ritual["type"]

        if ritual_type == "decision":
            result = self._execute_decision_ritual(ritual, context)
        elif ritual_type == "coordination":
            result = self._execute_coordination_ritual(ritual, context)
        elif ritual_type == "review":
            result = self._execute_review_ritual(ritual, context)
        else:
            result = {"error": f"Unknown ritual type: {ritual_type}"}

        # Record execution
        execution = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "result": result,
        }
        ritual["executions"].append(execution)

        return result

    def council_decision(
        self, topic: str, agents: List[str], votes: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Make a council decision with agent votes.

        Args:
            topic: Decision topic
            agents: Participating agents
            votes: Dictionary of agent votes

        Returns:
            Decision result
        """
        # Tally votes
        vote_counts = {}
        for agent, vote in votes.items():
            vote_counts[vote] = vote_counts.get(vote, 0) + 1

        # Determine outcome
        winner = max(vote_counts.items(), key=lambda x: x[1])

        decision = {
            "topic": topic,
            "participants": agents,
            "votes": votes,
            "outcome": winner[0],
            "vote_count": winner[1],
            "timestamp": datetime.now().isoformat(),
        }

        self.decisions.append(decision)
        self.council_history.append(decision)

        return decision

    def _execute_decision_ritual(
        self, ritual: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a decision ritual."""
        rules = ritual["rules"]
        threshold = rules.get("threshold", 0.5)
        
        # Simulate consensus building
        votes = {}
        for participant in ritual["participants"]:
            # In real implementation, would query actual agents
            votes[participant] = context.get(f"{participant}_vote", "approve")

        # Count votes
        approvals = sum(1 for v in votes.values() if v == "approve")
        approval_rate = approvals / len(votes) if votes else 0

        decision = "approved" if approval_rate >= threshold else "rejected"

        return {
            "decision": decision,
            "votes": votes,
            "approval_rate": approval_rate,
            "threshold": threshold,
        }

    def _execute_coordination_ritual(
        self, ritual: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a coordination ritual."""
        participants = ritual["participants"]
        task = context.get("task", {})

        # Assign roles based on agent types
        assignments = {}
        for participant in participants:
            if "Scout" in participant:
                assignments[participant] = "dna_analysis"
            elif "Archivist" in participant:
                assignments[participant] = "tree_management"
            elif "Oracle" in participant:
                assignments[participant] = "research"
            elif "Diplomat" in participant:
                assignments[participant] = "communication"

        return {
            "status": "coordinated",
            "assignments": assignments,
            "participants": participants,
        }

    def _execute_review_ritual(
        self, ritual: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a review ritual."""
        subject = context.get("subject", {})
        reviewers = ritual["participants"]

        # Simulate reviews
        reviews = {}
        for reviewer in reviewers:
            reviews[reviewer] = {
                "rating": 4.0,  # Simulated rating
                "comments": f"Review from {reviewer}",
                "approved": True,
            }

        approval_count = sum(1 for r in reviews.values() if r["approved"])
        overall_approved = approval_count >= len(reviews) * 0.5

        return {
            "status": "reviewed",
            "reviews": reviews,
            "approved": overall_approved,
            "approval_count": approval_count,
        }

    def get_ritual_history(self, ritual_id: str) -> List[Dict[str, Any]]:
        """Get execution history for a ritual."""
        if ritual_id not in self.rituals:
            return []
        return self.rituals[ritual_id]["executions"]
