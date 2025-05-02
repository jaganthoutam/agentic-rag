"""
Memory agent implementation for Agentic RAG.

This module implements an agent that retrieves information from memory components.
"""

import time
from typing import Dict, List, Optional, Union

from core import AgentType, Query, Document, AgentResult
from agents.base import BaseAgent
from memory.base import BaseMemory


class MemoryAgent(BaseAgent):
    """
    Memory agent implementation.
    
    This agent retrieves information from memory components.
    """
    
    def __init__(self, memories: Dict[str, BaseMemory]) -> None:
        """
        Initialize the memory agent.
        
        Args:
            memories: Dictionary of memory components by name
        """
        super().__init__(agent_type=AgentType.MEMORY)
        self.memories = memories
        self.logger.info(f"Memory agent initialized with {len(memories)} memory components")
    
    @BaseAgent.measure_execution_time
    def process(self, query: Query) -> AgentResult:
        """
        Process the query by retrieving relevant information from memory.
        
        Args:
            query: The query to process
            
        Returns:
            An AgentResult containing the retrieved information
        """
        self.logger.debug(f"Processing query: {query.id}")
        
        if not self.memories:
            self.logger.warning("No memory components available")
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[],
                confidence=0.0,
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "error": "No memory components available"
                }
            )
        
        try:
            # Check short-term memory first if available
            if "short_term" in self.memories:
                self.logger.debug("Checking short-term memory")
                short_term_result = self.memories["short_term"].retrieve(query)
                
                if short_term_result and short_term_result.confidence >= 0.8:
                    self.logger.info(f"High-confidence match found in short-term memory: {short_term_result.confidence:.2f}")
                    return short_term_result
            
            # Then check long-term memory if available
            if "long_term" in self.memories:
                self.logger.debug("Checking long-term memory")
                long_term_result = self.memories["long_term"].retrieve(query)
                
                if long_term_result and long_term_result.confidence >= 0.7:
                    self.logger.info(f"Good match found in long-term memory: {long_term_result.confidence:.2f}")
                    return long_term_result
            
            # If we reach here, no high-confidence matches were found
            # Return the best result from any memory component, if any
            best_result = None
            best_confidence = 0.0
            
            for memory_name, memory in self.memories.items():
                result = memory.retrieve(query)
                
                if result and result.confidence > best_confidence:
                    best_result = result
                    best_confidence = result.confidence
            
            if best_result:
                self.logger.info(f"Best memory match found with confidence: {best_confidence:.2f}")
                return best_result
            
            # No matches found
            self.logger.info("No memory matches found")
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[],
                confidence=0.0,
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "memory_hit": False,
                    "memories_checked": list(self.memories.keys())
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error retrieving from memory: {str(e)}")
            
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[],
                confidence=0.0,
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "error": str(e)
                }
            )