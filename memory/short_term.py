"""
Short-term memory implementation for Agentic RAG.

This module provides an in-memory, time-limited storage for recent queries and results.
"""

import time
from collections import OrderedDict
from typing import Dict, List, Optional, Union

from core import AgentType, Query, Document, MemoryEntry, AgentResult
from memory.base import BaseMemory


class ShortTermMemory(BaseMemory):
    """
    Short-term memory implementation.
    
    This class provides an in-memory, time-limited storage for recent queries and results.
    It uses an LRU (Least Recently Used) policy when capacity is reached.
    """
    
    def __init__(self, capacity: int = 1000, ttl: int = 3600) -> None:
        """
        Initialize the short-term memory.
        
        Args:
            capacity: Maximum number of entries to store
            ttl: Time-to-live in seconds (0 for no expiration)
        """
        super().__init__()
        self.capacity = capacity
        self.ttl = ttl
        self.memory: OrderedDict[str, MemoryEntry] = OrderedDict()
        self.document_store: Dict[str, Document] = {}
        self.logger.info(f"Short-term memory initialized with capacity={capacity}, ttl={ttl}s")
    
    def retrieve(self, query: Query) -> Optional[AgentResult]:
        """
        Retrieve relevant information from memory based on the query.
        
        Args:
            query: The query to retrieve information for
            
        Returns:
            An AgentResult containing retrieved documents and metadata,
            or None if no relevant information is found
        """
        current_time = time.time()
        self._clear_expired(current_time)
        
        # Simple cosine similarity could be used here
        # For now, implement a basic keyword matching
        query_keywords = set(query.text.lower().split())
        
        best_match = None
        highest_score = 0.0
        
        for memory_id, entry in self.memory.items():
            # Skip expired entries
            if self.ttl > 0 and (current_time - entry.created_at.timestamp()) > self.ttl:
                continue
            
            # Get the query for this memory entry
            stored_query_text = ""
            if hasattr(entry, "query_id") and entry.query_id:
                stored_query_text = query.text if entry.query_id == query.id else ""
            
            if not stored_query_text:
                continue
                
            # Calculate simple score based on keyword overlap
            stored_keywords = set(stored_query_text.lower().split())
            common_keywords = query_keywords.intersection(stored_keywords)
            
            if not common_keywords:
                continue
                
            score = len(common_keywords) / max(len(query_keywords), len(stored_keywords))
            
            # Boost score based on recency and access count
            recency_factor = 1.0
            if self.ttl > 0:
                age = current_time - entry.created_at.timestamp()
                recency_factor = 1.0 - (age / self.ttl)
            
            access_factor = min(1.0, entry.access_count / 10.0)  # Cap at 1.0
            
            final_score = score * 0.6 + recency_factor * 0.3 + access_factor * 0.1
            
            if final_score > highest_score:
                highest_score = final_score
                best_match = entry
        
        if best_match and highest_score >= 0.7:
            # Move to end (most recently used)
            self.memory.move_to_end(best_match.id)
            
            # Update access statistics
            best_match.update_access()
            
            # Gather documents
            documents = [
                self.document_store.get(doc_id)
                for doc_id in best_match.document_ids
                if doc_id in self.document_store
            ]
            documents = [doc for doc in documents if doc is not None]
            
            # Create result
            return AgentResult(
                agent_id="short_term_memory",
                agent_type=AgentType.MEMORY,
                query_id=query.id,
                documents=documents,
                confidence=highest_score,
                processing_time=0.01,  # Negligible processing time
                metadata={
                    "memory_id": best_match.id,
                    "memory_type": "short_term",
                    "memory_age": current_time - best_match.created_at.timestamp(),
                    "access_count": best_match.access_count
                }
            )
        
        return None
    
    def store(self, query: Query, result: AgentResult) -> None:
        """
        Store information in memory.
        
        Args:
            query: The query associated with the information
            result: The result to store
        """
        # Store documents first
        for document in result.documents:
            self.document_store[document.id] = document
        
        # Create memory entry
        memory_entry = MemoryEntry(
            query_id=query.id,
            document_ids=[doc.id for doc in result.documents],
            relevance_score=result.confidence,
            memory_type="short_term",
            metadata={
                "agent_id": result.agent_id,
                "agent_type": result.agent_type.value,
                "original_metadata": result.metadata
            }
        )
        
        # Add to memory
        self.memory[memory_entry.id] = memory_entry
        
        # Enforce capacity limit
        while len(self.memory) > self.capacity:
            # Remove least recently used
            oldest_id, _ = next(iter(self.memory.items()))
            self.remove(oldest_id)
        
        self.logger.debug(f"Stored memory entry: {memory_entry.id} with {len(memory_entry.document_ids)} documents")
    
    def update(self, memory_entry: MemoryEntry) -> None:
        """
        Update an existing memory entry.
        
        Args:
            memory_entry: The memory entry to update
        """
        if memory_entry.id in self.memory:
            self.memory[memory_entry.id] = memory_entry
            # Move to end (most recently used)
            self.memory.move_to_end(memory_entry.id)
            self.logger.debug(f"Updated memory entry: {memory_entry.id}")
    
    def remove(self, memory_id: str) -> bool:
        """
        Remove a memory entry.
        
        Args:
            memory_id: The ID of the memory entry to remove
            
        Returns:
            True if the entry was removed, False otherwise
        """
        if memory_id in self.memory:
            # Get document IDs to check for cleanup
            document_ids = self.memory[memory_id].document_ids
            
            # Remove memory entry
            del self.memory[memory_id]
            
            # Clean up documents that are no longer referenced
            self._cleanup_documents(document_ids)
            
            self.logger.debug(f"Removed memory entry: {memory_id}")
            return True
        
        return False
    
    def clear(self) -> None:
        """Clear all memory entries."""
        self.memory.clear()
        self.document_store.clear()
        self.logger.info("Short-term memory cleared")
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get statistics about the memory.
        
        Returns:
            A dictionary of statistics
        """
        current_time = time.time()
        
        # Count non-expired entries
        active_entries = 0
        if self.ttl > 0:
            active_entries = sum(
                1 for entry in self.memory.values()
                if (current_time - entry.created_at.timestamp()) <= self.ttl
            )
        else:
            active_entries = len(self.memory)
        
        return {
            "total_entries": len(self.memory),
            "active_entries": active_entries,
            "document_count": len(self.document_store),
            "capacity_used_percent": (len(self.memory) / self.capacity) * 100 if self.capacity > 0 else 0
        }
    
    def _clear_expired(self, current_time: float) -> None:
        """
        Clear expired entries.
        
        Args:
            current_time: Current time in seconds since epoch
        """
        if self.ttl <= 0:
            return  # No expiration
        
        expired_ids = []
        
        for memory_id, entry in self.memory.items():
            if (current_time - entry.created_at.timestamp()) > self.ttl:
                expired_ids.append(memory_id)
        
        for memory_id in expired_ids:
            self.remove(memory_id)
        
        if expired_ids:
            self.logger.debug(f"Cleared {len(expired_ids)} expired memory entries")
    
    def _cleanup_documents(self, document_ids: List[str]) -> None:
        """
        Clean up documents that are no longer referenced.
        
        Args:
            document_ids: List of document IDs to check
        """
        # Check if each document is still referenced by any memory entry
        for doc_id in document_ids:
            is_referenced = any(
                doc_id in entry.document_ids
                for entry in self.memory.values()
            )
            
            if not is_referenced and doc_id in self.document_store:
                del self.document_store[doc_id]
                self.logger.debug(f"Removed unreferenced document: {doc_id}")