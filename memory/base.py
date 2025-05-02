"""
Base memory component for Agentic RAG.

This module defines the base abstract class for memory components.
"""

import abc
import logging
from typing import Dict, List, Optional, Union

from core import Query, Document, MemoryEntry, AgentResult


class BaseMemory(abc.ABC):
    """
    Base abstract class for memory components.
    
    This class defines the interface that all memory implementations must follow.
    """
    
    def __init__(self) -> None:
        """Initialize the memory component."""
        self.logger = logging.getLogger(f"agentic_rag.memory.{self.__class__.__name__}")
    
    @abc.abstractmethod
    def retrieve(self, query: Query) -> Optional[AgentResult]:
        """
        Retrieve relevant information from memory based on the query.
        
        Args:
            query: The query to retrieve information for
            
        Returns:
            An AgentResult containing retrieved documents and metadata,
            or None if no relevant information is found
        """
        pass
    
    @abc.abstractmethod
    def store(self, query: Query, result: AgentResult) -> None:
        """
        Store information in memory.
        
        Args:
            query: The query associated with the information
            result: The result to store
        """
        pass
    
    @abc.abstractmethod
    def update(self, memory_entry: MemoryEntry) -> None:
        """
        Update an existing memory entry.
        
        Args:
            memory_entry: The memory entry to update
        """
        pass
    
    @abc.abstractmethod
    def remove(self, memory_id: str) -> bool:
        """
        Remove a memory entry.
        
        Args:
            memory_id: The ID of the memory entry to remove
            
        Returns:
            True if the entry was removed, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def clear(self) -> None:
        """Clear all memory entries."""
        pass
    
    @abc.abstractmethod
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get statistics about the memory.
        
        Returns:
            A dictionary of statistics
        """
        pass
    
    def close(self) -> None:
        """Close any resources associated with the memory."""
        pass