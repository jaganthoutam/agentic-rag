"""
Base planner component for Agentic RAG.

This module defines the base abstract class for planning components.
"""

import abc
import logging
from typing import Dict, List, Optional

from core import AgentType, Query, Plan
from agents.base import BaseAgent


class BasePlanner(abc.ABC):
    """
    Base abstract class for planner components.
    
    This class defines the interface that all planner implementations must follow.
    """
    
    def __init__(self) -> None:
        """Initialize the planner component."""
        self.logger = logging.getLogger(f"agentic_rag.planning.{self.__class__.__name__}")
    
    @abc.abstractmethod
    def create_plan(self, query: Query, available_agents: Dict[AgentType, BaseAgent]) -> Plan:
        """
        Create an execution plan for the given query using available agents.
        
        Args:
            query: The query to create a plan for
            available_agents: Dictionary of available agents by type
            
        Returns:
            A Plan object containing the steps to execute
        """
        pass
    
    @abc.abstractmethod
    def adapt_plan(self, plan: Plan, results_so_far: List, available_agents: Dict[AgentType, BaseAgent]) -> Plan:
        """
        Adapt the plan based on results obtained so far.
        
        Args:
            plan: The current plan
            results_so_far: Results obtained from executing steps so far
            available_agents: Dictionary of available agents by type
            
        Returns:
            An updated Plan object
        """
        pass
    
    def validate_plan(self, plan: Plan, available_agents: Dict[AgentType, BaseAgent]) -> bool:
        """
        Validate that a plan can be executed with the available agents.
        
        Args:
            plan: The plan to validate
            available_agents: Dictionary of available agents by type
            
        Returns:
            True if the plan is valid, False otherwise
        """
        for step in plan.steps:
            if step.agent_type not in available_agents:
                self.logger.warning(f"Plan validation failed: Agent type {step.agent_type.value} not available")
                return False
        
        return True