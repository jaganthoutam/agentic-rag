"""
Unit tests for memory components.

This module contains unit tests for the memory components of the Agentic RAG system.
"""

import unittest
import time
from unittest.mock import MagicMock, patch

from core import AgentType, Query, Document, AgentResult
from memory import ShortTermMemory


class TestShortTermMemory(unittest.TestCase):
    """Tests for the ShortTermMemory component."""
    
    def setUp(self):
        """Set up test environment."""
        self.memory = ShortTermMemory(capacity=3, ttl=1)  # Short TTL for testing
    
    def test_store_and_retrieve(self):
        """Test storing and retrieving data from memory."""
        # Create test data
        query = Query(text="Test query")
        doc1 = Document(content="Test content 1", source="test1")
        doc2 = Document(content="Test content 2", source="test2")
        
        result = AgentResult(
            agent_id="test_agent",
            agent_type=AgentType.SEARCH,
            query_id=query.id,
            documents=[doc1, doc2],
            confidence=0.8,
            processing_time=0.5,
            metadata={"test": "value"}
        )
        
        # Store in memory
        self.memory.store(query, result)
        
        # Retrieve from memory
        retrieved = self.memory.retrieve(query)
        
        # Check retrieved data
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.agent_type, AgentType.MEMORY)
        self.assertEqual(retrieved.query_id, query.id)
        self.assertEqual(len(retrieved.documents), 2)
        self.assertGreaterEqual(retrieved.confidence, 0.7)  # Should be high confidence for exact match
        
        # Check document content
        doc_contents = [doc.content for doc in retrieved.documents]
        self.assertIn("Test content 1", doc_contents)
        self.assertIn("Test content 2", doc_contents)
    
    def test_capacity_limit(self):
        """Test that capacity limit is enforced."""
        # Store more entries than capacity
        for i in range(5):
            query = Query(text=f"Test query {i}")
            doc = Document(content=f"Test content {i}", source=f"test{i}")
            
            result = AgentResult(
                agent_id="test_agent",
                agent_type=AgentType.SEARCH,
                query_id=query.id,
                documents=[doc],
                confidence=0.8,
                processing_time=0.5,
                metadata={}
            )
            
            self.memory.store(query, result)
        
        # Check memory size
        self.assertEqual(len(self.memory.memory), 3)  # Should be limited to capacity
        
        # The oldest entries should be removed (LRU policy)
        # So memory should contain entries for queries 2, 3, and 4
        query0 = Query(text="Test query 0")
        retrieved0 = self.memory.retrieve(query0)
        self.assertIsNone(retrieved0)  # Should not find query 0
        
        query4 = Query(text="Test query 4")
        retrieved4 = self.memory.retrieve(query4)
        self.assertIsNotNone(retrieved4)  # Should find query 4
    
    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        # Store an entry
        query = Query(text="Test query")
        doc = Document(content="Test content", source="test")
        
        result = AgentResult(
            agent_id="test_agent",
            agent_type=AgentType.SEARCH,
            query_id=query.id,
            documents=[doc],
            confidence=0.8,
            processing_time=0.5,
            metadata={}
        )
        
        self.memory.store(query, result)
        
        # Verify it can be retrieved
        retrieved1 = self.memory.retrieve(query)
        self.assertIsNotNone(retrieved1)
        
        # Wait for TTL to expire
        time.sleep(1.1)  # TTL is 1 second
        
        # Try to retrieve again
        retrieved2 = self.memory.retrieve(query)
        self.assertIsNone(retrieved2)  # Should not find the expired entry
    
    def test_remove(self):
        """Test removing an entry from memory."""
        # Store an entry
        query = Query(text="Test query")
        doc = Document(content="Test content", source="test")
        
        result = AgentResult(
            agent_id="test_agent",
            agent_type=AgentType.SEARCH,
            query_id=query.id,
            documents=[doc],
            confidence=0.8,
            processing_time=0.5,
            metadata={}
        )
        
        self.memory.store(query, result)
        
        # Get the memory ID
        memory_id = next(iter(self.memory.memory.keys()))
        
        # Remove the entry
        removed = self.memory.remove(memory_id)
        
        self.assertTrue(removed)
        self.assertEqual(len(self.memory.memory), 0)
        
        # Try to retrieve the removed entry
        retrieved = self.memory.retrieve(query)
        self.assertIsNone(retrieved)
    
    def test_clear(self):
        """Test clearing all entries from memory."""
        # Store multiple entries
        for i in range(3):
            query = Query(text=f"Test query {i}")
            doc = Document(content=f"Test content {i}", source=f"test{i}")
            
            result = AgentResult(
                agent_id="test_agent",
                agent_type=AgentType.SEARCH,
                query_id=query.id,
                documents=[doc],
                confidence=0.8,
                processing_time=0.5,
                metadata={}
            )
            
            self.memory.store(query, result)
        
        # Verify entries were stored
        self.assertEqual(len(self.memory.memory), 3)
        
        # Clear memory
        self.memory.clear()
        
        # Verify memory is empty
        self.assertEqual(len(self.memory.memory), 0)
        self.assertEqual(len(self.memory.document_store), 0)
    
    def test_get_stats(self):
        """Test getting memory statistics."""
        # Store entries
        for i in range(2):
            query = Query(text=f"Test query {i}")
            doc = Document(content=f"Test content {i}", source=f"test{i}")
            
            result = AgentResult(
                agent_id="test_agent",
                agent_type=AgentType.SEARCH,
                query_id=query.id,
                documents=[doc],
                confidence=0.8,
                processing_time=0.5,
                metadata={}
            )
            
            self.memory.store(query, result)
        
        # Get stats
        stats = self.memory.get_stats()
        
        self.assertEqual(stats["total_entries"], 2)
        self.assertEqual(stats["document_count"], 2)
        self.assertEqual(stats["capacity_used_percent"], (2 / 3) * 100)


if __name__ == "__main__":
    unittest.main()