"""
Unit tests for API components.

This module contains unit tests for the API components of the Agentic RAG system.
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api import app, QueryRequest, QueryResponse
from app import AgenticRag
from core import RagOutput, AgentType


class TestAPI(unittest.TestCase):
    """Tests for the API components."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = TestClient(app)
        
        # Create a mock RAG instance
        self.mock_rag = MagicMock(spec=AgenticRag)
        
        # Create a sample response for the mock
        self.sample_output = RagOutput(
            query_id="test-query-id",
            response="This is a test response",
            documents=[],
            processing_time=0.5,
            confidence=0.8,
            metadata={"test": "value"}
        )
        
        # Configure the mock to return the sample output
        self.mock_rag.process_query.return_value = self.sample_output
    
    @patch("api.rag")
    def test_health_endpoint(self, mock_rag):
        """Test the health endpoint."""
        # Set the mock RAG instance
        mock_rag.return_value = self.mock_rag
        
        # Send a request to the health endpoint
        response = self.client.get("/health")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("version", data)
        self.assertIn("timestamp", data)
    
    @patch("api.rag")
    def test_query_endpoint(self, mock_rag):
        """Test the query endpoint."""
        # Set the mock RAG instance
        mock_rag.return_value = self.mock_rag
        
        # Create a query request
        query_request = {
            "text": "Test query",
            "metadata": {"source": "test"}
        }
        
        # Send a request to the query endpoint
        response = self.client.post("/query", json=query_request)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["query_id"], "test-query-id")
        self.assertEqual(data["response"], "This is a test response")
        self.assertEqual(data["confidence"], 0.8)
        self.assertEqual(data["metadata"]["test"], "value")
        
        # Verify that the RAG instance was called with the correct query
        self.mock_rag.process_query.assert_called_once_with("Test query")
    
    @patch("api.rag")
    def test_query_endpoint_error(self, mock_rag):
        """Test error handling in the query endpoint."""
        # Set the mock RAG instance
        mock_rag.return_value = self.mock_rag
        
        # Configure the mock to raise an exception
        self.mock_rag.process_query.side_effect = Exception("Test error")
        
        # Create a query request
        query_request = {
            "text": "Test query",
            "metadata": {"source": "test"}
        }
        
        # Send a request to the query endpoint
        response = self.client.post("/query", json=query_request)
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("Test error", data["detail"])
    
    @patch("api.rag")
    def test_stats_endpoint(self, mock_rag):
        """Test the stats endpoint."""
        # Set the mock RAG instance
        mock_rag.return_value = self.mock_rag
        
        # Configure the mock for memory stats
        mock_memory1 = MagicMock()
        mock_memory1.get_stats.return_value = {
            "total_entries": 10,
            "active_entries": 8,
            "document_count": 20
        }
        
        mock_memory2 = MagicMock()
        mock_memory2.get_stats.return_value = {
            "memory_entries": 5,
            "documents": 15
        }
        
        self.mock_rag.memories = {
            "short_term": mock_memory1,
            "long_term": mock_memory2
        }
        
        # Configure the mock for agent counts
        self.mock_rag.agents = {
            AgentType.SEARCH: MagicMock(),
            AgentType.MEMORY: MagicMock()
        }
        
        # Send a request to the stats endpoint
        response = self.client.get("/stats")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("agents", data)
        self.assertIn("memory", data)
        self.assertIn("uptime", data)
        self.assertIn("query_count", data)
        
        # Check memory stats
        self.assertEqual(data["memory"]["short_term"]["total_entries"], 10)
        self.assertEqual(data["memory"]["long_term"]["memory_entries"], 5)
        
        # Check agent counts
        self.assertEqual(data["agents"]["search"], 1)
        self.assertEqual(data["agents"]["memory"], 1)


if __name__ == "__main__":
    unittest.main()