"""
Base agent interface for Agentic RAG.

This module defines the base abstract class for agent implementations.
"""

import abc
import logging
import time
from typing import Dict, List, Optional, Union

from core import AgentType, Query, Document, AgentResult


class BaseAgent(abc.ABC):
    """
    Base abstract class for agent implementations.
    
    This class defines the interface that all agent implementations must follow.
    """
    
    def __init__(self, agent_type: AgentType) -> None:
        """
        Initialize the agent.
        
        Args:
            agent_type: Type of this agent
        """
        self.agent_type = agent_type
        self.logger = logging.getLogger(f"agentic_rag.agents.{self.__class__.__name__}")
        self.id = f"{self.agent_type.value}_{id(self)}"
    
    @abc.abstractmethod
    def process(self, query: Query) -> AgentResult:
        """
        Process the query and generate a result.
        
        Args:
            query: The query to process
            
        Returns:
            An AgentResult containing the processed information
        """
        pass
    
    def measure_execution_time(func):
        """
        Decorator to measure execution time of a function.
        
        Args:
            func: The function to measure
            
        Returns:
            Wrapped function that measures execution time
        """
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            execution_time = time.time() - start_time
            
            # Add execution time to result
            if result and isinstance(result, AgentResult):
                result.processing_time = execution_time
            
            return result
        
        return wrapper