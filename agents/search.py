"""
Search agent implementation for Agentic RAG.

This module implements an agent that searches external sources for information.
"""

import json
import time
import uuid
import os
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
    
    def __init__(
        self, 
        engine: str = "mock", 
        api_key: str = "", 
        max_results: int = 10
    ) -> None:
        """
        Initialize the search agent.
        
        Args:
            engine: Search engine to use (mock)
            api_key: API key for the search engine
            max_results: Maximum number of results to return
        """
        super().__init__(agent_type=AgentType.SEARCH)
        self.engine = engine
        self.api_key = api_key or os.environ.get("SEARCH_API_KEY", "")
        self.max_results = max_results
        self.logger.info(f"Search agent initialized with engine={engine}, max_results={max_results}")
        
        # Validate API key
        if not self.api_key and engine != "mock":
            self.logger.warning("No API key provided for search agent")
    
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
        self.logger.debug(f"Searching for: {query_text} using {self.engine}")
        
        # Always use mock search for now
        return self._mock_search(query_text)
    
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
            "meta": {
                "id": str(uuid.uuid4()),
                "node": "mock",
                "ms": 123
            },
            "data": [
                {
                    "t": 0,  # Result type 0 = web result
                    "rank": 1,
                    "url": f"https://example.com/mock1_{uuid.uuid4()}",
                    "title": f"Mock Result 1 for {query_text}",
                    "snippet": f"This is a mock result for {query_text}. It simulates a search result."
                },
                {
                    "t": 0,
                    "rank": 2,
                    "url": f"https://example.com/mock2_{uuid.uuid4()}",
                    "title": f"Mock Result 2 for {query_text}",
                    "snippet": f"Another mock result for {query_text}. This is just for testing purposes."
                }
            ]
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
        
        # Extract results from response
        results = search_results.get("data", [])
        
        for result in results:
            # Check result type (0 = web result, 1 = related searches)
            if result.get("t") == 0:  # Web result
                # Extract fields
                url = result.get("url", "")
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                rank = result.get("rank", 0)
                
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
                        "rank": rank,
                        "engine": self.engine,
                        "relevance": 1.0 - (rank / 10) if rank else 0.5  # Higher rank = lower relevance
                    }
                )
                
                documents.append(document)
        
        return documents
    
    def _calculate_confidence(self, documents: List[Document]) -> float:
        """
        Calculate confidence score based on search results.
        
        Args:
            documents: List of search result documents
            
        Returns:
            Confidence score (0.0-1.0)
        """
        if not documents:
            return 0.0
        
        # Simple confidence calculation based on number of results
        # and their relevance scores
        total_relevance = sum(doc.metadata.get("relevance", 0.5) for doc in documents)
        avg_relevance = total_relevance / len(documents)
        
        # Scale by number of results (up to a point)
        result_factor = min(len(documents) / 5, 1.0)
        
        return avg_relevance * result_factor


class KagiAPIError(Exception):
    """Exception raised for errors in the Kagi API."""
    pass