"""
Unit tests for core components.

This module contains unit tests for the core data models and related functionality.
"""

import unittest
from datetime import datetime
import uuid

from core import AgentType, Query, Document, MemoryEntry, AgentResult, Plan, PlanStep


class TestCoreModels(unittest.TestCase):
    """Tests for the core data models."""
    
    def test_query_creation(self):
        """Test creating a Query object."""
        query = Query(text="Test query")
        
        self.assertIsNotNone(query.id)
        self.assertEqual(query.text, "Test query")
        self.assertIsInstance(query.timestamp, datetime)
        self.assertEqual(query.metadata, {})
        
        # Test with custom values
        custom_id = str(uuid.uuid4())
        custom_timestamp = datetime.utcnow()
        custom_metadata = {"source": "test"}
        
        query = Query(
            id=custom_id,
            text="Test query",
            timestamp=custom_timestamp,
            metadata=custom_metadata
        )
        
        self.assertEqual(query.id, custom_id)
        self.assertEqual(query.timestamp, custom_timestamp)
        self.assertEqual(query.metadata, custom_metadata)
    
    def test_document_creation(self):
        """Test creating a Document object."""
        document = Document(content="Test content", source="test")
        
        self.assertIsNotNone(document.id)
        self.assertEqual(document.content, "Test content")
        self.assertEqual(document.source, "test")
        self.assertIsInstance(document.timestamp, datetime)
        self.assertEqual(document.metadata, {})
    
    def test_memory_entry_creation(self):
        """Test creating a MemoryEntry object."""
        query_id = str(uuid.uuid4())
        document_ids = [str(uuid.uuid4()) for _ in range(3)]
        
        entry = MemoryEntry(
            query_id=query_id,
            document_ids=document_ids,
            memory_type="short_term"
        )
        
        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.query_id, query_id)
        self.assertEqual(entry.document_ids, document_ids)
        self.assertEqual(entry.access_count, 0)
        self.assertEqual(entry.relevance_score, 0.0)
        self.assertEqual(entry.memory_type, "short_term")
        
        # Test update_access method
        initial_accessed_at = entry.accessed_at
        entry.update_access()
        
        self.assertEqual(entry.access_count, 1)
        self.assertNotEqual(entry.accessed_at, initial_accessed_at)
    
    def test_agent_result_creation(self):
        """Test creating an AgentResult object."""
        query_id = str(uuid.uuid4())
        documents = [
            Document(content=f"Content {i}", source=f"source_{i}")
            for i in range(3)
        ]
        
        result = AgentResult(
            agent_id="test_agent",
            agent_type=AgentType.SEARCH,
            query_id=query_id,
            documents=documents,
            confidence=0.8,
            processing_time=1.5,
            metadata={"test": "value"}
        )
        
        self.assertEqual(result.agent_id, "test_agent")
        self.assertEqual(result.agent_type, AgentType.SEARCH)
        self.assertEqual(result.query_id, query_id)
        self.assertEqual(result.documents, documents)
        self.assertEqual(result.confidence, 0.8)
        self.assertEqual(result.processing_time, 1.5)
        self.assertEqual(result.metadata, {"test": "value"})
    
    def test_plan_and_steps(self):
        """Test creating Plan and PlanStep objects."""
        query_id = str(uuid.uuid4())
        plan = Plan(query_id=query_id, planner_type="react")
        
        self.assertIsNotNone(plan.id)
        self.assertEqual(plan.query_id, query_id)
        self.assertEqual(plan.planner_type, "react")
        self.assertEqual(plan.steps, [])
        self.assertEqual(plan.status, "created")
        
        # Add steps
        step1 = plan.add_step(AgentType.MEMORY, "Check memory")
        step2 = plan.add_step(AgentType.SEARCH, "Search external sources")
        
        self.assertEqual(len(plan.steps), 2)
        self.assertEqual(step1.agent_type, AgentType.MEMORY)
        self.assertEqual(step1.description, "Check memory")
        self.assertEqual(step1.status, "pending")
        
        # Test step execution
        step1.start()
        self.assertEqual(step1.status, "in_progress")
        self.assertIsNotNone(step1.start_time)
        
        result = AgentResult(
            agent_id="test_agent",
            agent_type=AgentType.MEMORY,
            query_id=query_id,
            documents=[],
            confidence=0.5,
            processing_time=0.5,
            metadata={}
        )
        
        step1.complete(result)
        self.assertEqual(step1.status, "completed")
        self.assertEqual(step1.result, result)
        self.assertIsNotNone(step1.end_time)
        
        # Test plan status
        plan.start_execution()
        self.assertEqual(plan.status, "executing")
        
        plan.complete()
        self.assertEqual(plan.status, "completed")
        
        # Test plan failure
        plan.status = "executing"  # Reset for testing
        step2.fail()
        
        self.assertEqual(step2.status, "failed")
        self.assertIsNotNone(step2.end_time)
        
        plan.fail()
        self.assertEqual(plan.status, "failed")


if __name__ == "__main__":
    unittest.main()