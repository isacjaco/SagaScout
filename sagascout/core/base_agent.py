"""Core base class for all SagaScout agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseAgent(ABC):
    """Base class for all SagaScout agents."""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize a base agent.

        Args:
            name: Name of the agent
            config: Configuration dictionary for the agent
        """
        self.name = name
        self.config = config or {}
        self.memory = []

    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """
        Process input data according to agent's specialty.

        Args:
            input_data: Input data to process

        Returns:
            Processed result
        """
        pass

    def remember(self, event: Dict[str, Any]) -> None:
        """
        Store an event in the agent's narrative memory.

        Args:
            event: Event dictionary containing memory information
        """
        self.memory.append(event)

    def recall(self, query: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve memories, optionally filtered by query.

        Args:
            query: Optional query string to filter memories

        Returns:
            List of memory events
        """
        if query is None:
            return self.memory
        return [m for m in self.memory if query.lower() in str(m).lower()]

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the agent.

        Returns:
            Dictionary containing agent status information
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "memory_count": len(self.memory),
            "config": self.config,
        }
