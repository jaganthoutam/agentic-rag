"""
Search agent implementation for Agentic RAG.

This module implements an agent that searches external sources for information.
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import requests

from core import AgentType, Query, Document, AgentResult
from agents.base import BaseAgent


class SearchAgent(BaseAgent):
    """
    Search agent implementation.
    
    This agent searches external sources for information.
    """
    
    def __init__(self, engine: str = "kagi", api_key: str = "", max_results: int = 10) -> None:
        """
        Initialize the search agent.
        
        Args:
            engine: Search engine to use
            api_key: API key for the search engine
            max_results: Maximum number of results to return
        """
        super().__init__(agent_type=AgentType.SEARCH)
        self.engine = engine
        self.api_key = api_key
        self.max_results = max_results
        self.logger.info(f"Search agent initialized with engine={engine}, max_results={max_results}")
    
    @BaseAgent.measure_execution_time
    def process(self, query: Query) -> AgentResult:
        """
        Process the query by searching external sources.
        
        Args:
            query: The query to process
            
        Returns:
            An AgentResult containing the search results
        """
        self.logger.debug(f"Processing query: {query.id}")
        
        try:
            search_results = self._perform_search(query.text)
            documents = self._parse_search_results(search_results)
            
            # Limit results
            documents = documents[:self.max_results]
            
            # Calculate confidence based on result quality
            confidence = self._calculate_confidence(documents)
            
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=documents,
                confidence=confidence,
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "engine": self.engine,
                    "result_count": len(documents),
                    "search_query": query.text
                }
            )
        except Exception as e:
            self.logger.error(f"Error in search: {str(e)}")
            
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[],
                confidence=0.0,
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "error": str(e),
                    "engine": self.engine,
                    "search_query": query.text
                }
            )
    
    def _perform_search(self, query_text: str) -> Dict[str, Any]:
        """
        Perform a search using the configured engine.
        
        Args:
            query_text: Text to search for
            
        Returns:
            Search results as a dictionary
        """
        # In a real implementation, this would call the actual search API
        self.logger.debug(f"Searching for: {query_text} using {self.engine}")
        
        if self.engine == "kagi":
            return self._kagi_search(query_text)
        else:
            # Generic mock search
            return self._mock_search(query_text)
    
    def _kagi_search(self, query_text: str) -> Dict[str, Any]:
        """
        Perform a search using the kagi search engine.
        
        Args:
            query_text: Text to search for
            
        Returns:
            Search results as a dictionary
        """
        # In a real implementation, this would call the kagi API
        try:
            # Mock API call to kagi
            time.sleep(0.5)  # Simulate network delay
            
            # Simulate a response
            return {
                "results": [
                    {
                        "url": f"https://example.com/result1_{uuid.uuid4()}",
                        "title": f"Result 1 for {query_text}",
                        "snippet": f"This is the first result for {query_text}. It contains relevant information about the query topic.",
                        "relevance": 0.92
                    },
                    {
                        "url": f"https://example.com/result2_{uuid.uuid4()}",
                        "title": f"Result 2 for {query_text}",
                        "snippet": f"This is the second result for {query_text}. It provides additional context about the topic.",
                        "relevance": 0.85
                    },
                    {
                        "url": f"https://example.com/result3_{uuid.uuid4()}",
                        "title": f"Result 3 for {query_text}",
                        "snippet": f"This is the third result for {query_text}. It offers a different perspective on the subject.",
                        "relevance": 0.78
                    }
                ],
                "meta": {
                    "total_results": 1240,
                    "query_time_ms": 156,
                    "engine": "kagi"
                }
            }
        except Exception as e:
            self.logger.error(f"Error in kagi search: {str(e)}")
            raise
    
    def _mock_search(self, query_text: str) -> Dict[str, Any]:
        """
        Perform a mock search for testing.
        
        Args:
            query_text: Text to search for
            
        Returns:
            Mock search results as a dictionary
        """
        # Create a simple mock response for testing
        time.sleep(0.3)  # Simulate network delay
        
        return {
            "results": [
                {
                    "url": f"https://example.com/mock1_{uuid.uuid4()}",
                    "title": f"Mock Result 1 for {query_text}",
                    "snippet": f"This is a mock result for {query_text}. It simulates a search result.",
                    "relevance": 0.75
                },
                {
                    "url": f"https://example.com/mock2_{uuid.uuid4()}",
                    "title": f"Mock Result 2 for {query_text}",
                    "snippet": f"Another mock result for {query_text}. This is just for testing.",
                    "relevance": 0.65
                }
            ],
            "meta": {
                "total_results": 42,
                "query_time_ms": 123,
                "engine": "mock"
            }
        }
    
    def _parse_search_results(self, search_results: Dict[str, Any]) -> List[Document]:
        """
        Parse search results into Document objects.
        
        Args:
            search_results: Raw search results
            
        Returns:
            List of Document objects
        """
        documents = []
        
        for result in search_results.get("results", []):
            # Extract fields
            url = result.get("url", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            relevance = result.get("relevance", 0.5)
            
            # Create content
            content = f"{title}\n\n{snippet}"
            
            # Create document
            document = Document(
                content=content,
                source=url,
                metadata={
                    "title": title,
                    "snippet": snippet,
                    "url": url,
                    "relevance": relevance,
                    "engine": search_results.get("meta", {}).get("engine", self.engine)
                }
            )
            
            documents.append(document)
        
        return documents
    
    def _calculate_confidence(self, documents: List[Document]) -> float:
        """
        Calculate a confidence score based on search results.
        
        Args:
            documents: Search result documents
            
        Returns:
            Confidence score between 0 and 1
        """
        if not documents:
            return 0.0
        
        # Calculate based on average relevance and result count
        avg_relevance = sum(
            doc.metadata.get("relevance", 0.5) for doc in documents
        ) / len(documents)
        
        # Scale by result count (more results = higher confidence, up to a point)
        count_factor = min(len(documents) / self.max_results, 1.0)
        
        # Combine factors
        confidence = avg_relevance * 0.7 + count_factor * 0.3
        
        return confidence