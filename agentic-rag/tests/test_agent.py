"""
Unit tests for agent components.

This module contains unit tests for the agent components of the Agentic RAG system.
"""

import unittest
from unittest.mock import MagicMock, patch

from core import AgentType, Query, Document, AgentResult
from agents import SearchAgent, AggregatorAgent


class TestSearchAgent(unittest.TestCase):
    """Tests for the SearchAgent component."""
    
    def setUp(self):
        """Set up test environment."""
        self.agent = SearchAgent(engine="test", api_key="dummy_key", max_results=5)
    
    @patch("time.sleep", return_value=None)  # Skip sleep calls
    def test_process(self, mock_sleep):
        """Test the process method."""
        query = Query(text="Test query")
        
        # Mock the _perform_search method
        self.agent._perform_search = MagicMock(return_value={
            "results": [
                {
                    "url": "https://example.com/result1",
                    "title": "Result 1",
                    "snippet": "This is result 1",
                    "relevance": 0.9
                },
                {
                    "url": "https://example.com/result2",
                    "title": "Result 2",
                    "snippet": "This is result 2",
                    "relevance": 0.8
                }
            ],
            "meta": {
                "total_results": 2,
                "query_time_ms": 100,
                "engine": "test"
            }
        })
        
        # Process the query
        result = self.agent.process(query)
        
        # Verify the result
        self.assertEqual(result.agent_type, AgentType.SEARCH)
        self.assertEqual(result.query_id, query.id)
        self.assertEqual(len(result.documents), 2)
        self.assertGreater(result.confidence, 0.0)
        
        # Verify metadata
        self.assertEqual(result.metadata["engine"], "test")
        self.assertEqual(result.metadata["result_count"], 2)
        self.assertEqual(result.metadata["search_query"], "Test query")
        
        # Verify document content
        doc1, doc2 = result.documents
        self.assertEqual(doc1.source, "https://example.com/result1")
        self.assertIn("Result 1", doc1.content)
        self.assertIn("This is result 1", doc1.content)
        
        self.assertEqual(doc2.source, "https://example.com/result2")
        self.assertIn("Result 2", doc2.content)
        self.assertIn("This is result 2", doc2.content)
    
    @patch("time.sleep", return_value=None)  # Skip sleep calls
    def test_process_error(self, mock_sleep):
        """Test error handling in the process method."""
        query = Query(text="Test query")
        
        # Mock the _perform_search method to raise an exception
        self.agent._perform_search = MagicMock(side_effect=Exception("Test error"))
        
        # Process the query
        result = self.agent.process(query)
        
        # Verify the result
        self.assertEqual(result.agent_type, AgentType.SEARCH)
        self.assertEqual(result.query_id, query.id)
        self.assertEqual(len(result.documents), 0)
        self.assertEqual(result.confidence, 0.0)
        
        # Verify error is included in metadata
        self.assertEqual(result.metadata["error"], "Test error")
    
    def test_calculate_confidence(self):
        """Test the confidence calculation method."""
        # Create test documents with different relevance scores
        docs1 = [
            Document(
                content="Test content",
                source="test",
                metadata={"relevance": 0.9}
            ),
            Document(
                content="Test content",
                source="test",
                metadata={"relevance": 0.8}
            )
        ]
        
        docs2 = [
            Document(
                content="Test content",
                source="test",
                metadata={"relevance": 0.5}
            )
        ]
        
        # Calculate confidence for different document sets
        conf1 = self.agent._calculate_confidence(docs1)
        conf2 = self.agent._calculate_confidence(docs2)
        conf_empty = self.agent._calculate_confidence([])
        
        # Verify confidence values
        self.assertGreater(conf1, conf2)  # Higher relevance should give higher confidence
        self.assertGreater(conf2, 0.0)    # Some documents should give positive confidence
        self.assertEqual(conf_empty, 0.0)  # No documents should give zero confidence


class TestAggregatorAgent(unittest.TestCase):
    """Tests for the AggregatorAgent component."""
    
    def setUp(self):
        """Set up test environment."""
        self.agent = AggregatorAgent(timeout=10, max_agents=3)
    
    def test_aggregate(self):
        """Test the aggregate method."""
        query = Query(text="Test query")
        
        # Create test results from different agents
        search_result = AgentResult(
            agent_id="search_agent",
            agent_type=AgentType.SEARCH,
            query_id=query.id,
            documents=[
                Document(content="Search content 1", source="search1"),
                Document(content="Search content 2", source="search2")
            ],
            confidence=0.8,
            processing_time=0.5,
            metadata={}
        )
        
        local_result = AgentResult(
            agent_id="local_data_agent",
            agent_type=AgentType.LOCAL_DATA,
            query_id=query.id,
            documents=[
                Document(content="Local content", source="local")
            ],
            confidence=0.7,
            processing_time=0.3,
            metadata={}
        )
        
        # Aggregate the results
        result = self.agent.aggregate(query, [search_result, local_result])
        
        # Verify the aggregated result
        self.assertEqual(result.agent_type, AgentType.AGGREGATOR)
        self.assertEqual(result.query_id, query.id)
        
        # Should have all documents plus a summary document
        self.assertEqual(len(result.documents), 4)  # 3 original + 1 summary
        
        # First document should be the summary
        summary_doc = result.documents[0]
        self.assertEqual(summary_doc.source, "aggregator_summary")
        self.assertIn("query", summary_doc.content.lower())
        self.assertIn("3 relevant documents", summary_doc.content.lower())
        
        # Check metadata
        self.assertIn("source_agents", result.metadata)
        self.assertIn("search", result.metadata["source_agents"])
        self.assertIn("local_data", result.metadata["source_agents"])
        
        # Confidence should be average of input confidences
        expected_confidence = (0.8 + 0.7) / 2
        self.assertAlmostEqual(result.confidence, expected_confidence, places=1)
    
    def test_aggregate_no_results(self):
        """Test aggregating with no results."""
        query = Query(text="Test query")
        
        # Aggregate empty results
        result = self.agent.aggregate(query, [])
        
        # Verify the aggregated result
        self.assertEqual(result.agent_type, AgentType.AGGREGATOR)
        self.assertEqual(result.query_id, query.id)
        self.assertEqual(len(result.documents), 0)
        self.assertEqual(result.confidence, 0.0)
        
        # Verify error is included in metadata
        self.assertEqual(result.metadata["error"], "No results to aggregate")
    
    def test_deduplicate_documents(self):
        """Test the document deduplication method."""
        # Create documents with similar content
        docs = [
            Document(content="This is a test document with some content.", source="source1"),
            Document(content="This is a test document with some content. Extra stuff.", source="source2"),
            Document(content="Completely different content.", source="source3")
        ]
        
        # Deduplicate documents
        unique_docs = self.agent._deduplicate_documents(docs)
        
        # Should keep the first of the similar documents and the different one
        self.assertEqual(len(unique_docs), 2)
        self.assertEqual(unique_docs[0].source, "source1")
        self.assertEqual(unique_docs[1].source, "source3")


if __name__ == "__main__":
    unittest.main()