"""
ReAct planner implementation for Agentic RAG.

This module implements the ReAct (Reasoning and Acting) planning approach, 
which interleaves reasoning and action steps.
"""

import time
import uuid
from typing import Dict, List, Optional, Set

from core import AgentType, Query, Plan, PlanStep, AgentResult
from planning.base import BasePlanner
from agents.base import BaseAgent


class ReActPlanner(BasePlanner):
    """
    ReAct planner implementation.
    
    This planner implements the ReAct (Reasoning and Acting) approach,
    which interleaves reasoning and action steps.
    """
    
    def __init__(self, max_steps: int = 10, timeout: int = 60) -> None:
        """
        Initialize the ReAct planner.
        
        Args:
            max_steps: Maximum number of steps to include in a plan
            timeout: Timeout in seconds for plan creation
        """
        super().__init__()
        self.max_steps = max_steps
        self.timeout = timeout
        self.logger.info(f"ReAct planner initialized with max_steps={max_steps}, timeout={timeout}s")
    
    def create_plan(self, query: Query, available_agents: Dict[AgentType, BaseAgent]) -> Plan:
        """
        Create an execution plan for the given query using available agents.
        
        Args:
            query: The query to create a plan for
            available_agents: Dictionary of available agents by type
            
        Returns:
            A Plan object containing the steps to execute
        """
        start_time = time.time()
        plan = Plan(query_id=query.id, planner_type="react")
        
        # Check if memory agent is available for first step
        if AgentType.MEMORY in available_agents:
            plan.add_step(
                agent_type=AgentType.MEMORY,
                description=f"Check memory for similar queries to '{query.text}'"
            )
        
        # Query analysis and information gathering steps
        # This is a simple fixed plan, but a real ReAct implementation would
        # adaptively generate plans based on query understanding
        
        # Check if we need to search external sources
        needs_search = self._query_needs_search(query.text)
        
        if needs_search and AgentType.SEARCH in available_agents:
            plan.add_step(
                agent_type=AgentType.SEARCH,
                description=f"Search external sources for information about '{query.text}'"
            )
        
        # Check if we need to access local data
        needs_local_data = self._query_needs_local_data(query.text)
        
        if needs_local_data and AgentType.LOCAL_DATA in available_agents:
            plan.add_step(
                agent_type=AgentType.LOCAL_DATA,
                description=f"Retrieve relevant local data for '{query.text}'"
            )
        
        # Check if we need to access cloud resources
        needs_cloud = self._query_needs_cloud(query.text)
        
        if needs_cloud and AgentType.CLOUD in available_agents:
            plan.add_step(
                agent_type=AgentType.CLOUD,
                description=f"Access cloud resources for information about '{query.text}'"
            )
        
        # Always use aggregator if available to combine results
        if AgentType.AGGREGATOR in available_agents and len(plan.steps) > 1:
            plan.add_step(
                agent_type=AgentType.AGGREGATOR,
                description=f"Aggregate and synthesize information from previous steps"
            )
        
        # Always use generative agent for final response
        if AgentType.GENERATIVE in available_agents:
            plan.add_step(
                agent_type=AgentType.GENERATIVE,
                description=f"Generate final response to '{query.text}'"
            )
        
        # Ensure we don't exceed max steps
        if len(plan.steps) > self.max_steps:
            self.logger.warning(f"Plan exceeded max steps ({len(plan.steps)} > {self.max_steps}), truncating")
            plan.steps = plan.steps[:self.max_steps]
        
        # Check timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > self.timeout:
            self.logger.warning(f"Plan creation timed out after {elapsed_time:.2f}s")
        
        return plan
    
    def adapt_plan(self, plan: Plan, results_so_far: List[AgentResult], available_agents: Dict[AgentType, BaseAgent]) -> Plan:
        """
        Adapt the plan based on results obtained so far.
        
        Args:
            plan: The current plan
            results_so_far: Results obtained from executing steps so far
            available_agents: Dictionary of available agents by type
            
        Returns:
            An updated Plan object
        """
        # Check if we need to adapt the plan based on memory results
        memory_results = [r for r in results_so_far if r.agent_type == AgentType.MEMORY]
        
        if memory_results and memory_results[0].confidence >= 0.8:
            # Memory returned a high-confidence result, we can skip search steps
            self.logger.info("High-confidence memory result found, adapting plan to skip search steps")
            
            # Remove search, local data, and cloud steps
            new_steps = [
                step for step in plan.steps
                if step.agent_type not in {AgentType.SEARCH, AgentType.LOCAL_DATA, AgentType.CLOUD}
                and step.status == "pending"  # Only keep pending steps
            ]
            
            # Create a new plan with the filtered steps
            new_plan = Plan(
                id=str(uuid.uuid4()),
                query_id=plan.query_id,
                planner_type="react",
                status="created"
            )
            
            for step in new_steps:
                new_plan.add_step(step.agent_type, step.description)
            
            return new_plan
        
        # Check if we need to adapt based on search results
        search_results = [r for r in results_so_far if r.agent_type == AgentType.SEARCH]
        
        if search_results and not search_results[0].documents:
            # Search returned no results, we need to try other sources
            self.logger.info("Search returned no results, adapting plan to use alternative sources")
            
            # Add local data and cloud steps if not already in the plan
            # and if the corresponding agents are available
            
            current_agent_types = {step.agent_type for step in plan.steps}
            
            if AgentType.LOCAL_DATA not in current_agent_types and AgentType.LOCAL_DATA in available_agents:
                # Find the position after the search step
                for i, step in enumerate(plan.steps):
                    if step.agent_type == AgentType.SEARCH:
                        plan.steps.insert(i + 1, PlanStep(
                            plan_id=plan.id,
                            agent_type=AgentType.LOCAL_DATA,
                            description=f"Retrieve relevant local data as search returned no results"
                        ))
                        break
            
            if AgentType.CLOUD not in current_agent_types and AgentType.CLOUD in available_agents:
                # Find the position after the local data step if it exists, otherwise after search
                local_data_index = next((i for i, step in enumerate(plan.steps) if step.agent_type == AgentType.LOCAL_DATA), None)
                search_index = next((i for i, step in enumerate(plan.steps) if step.agent_type == AgentType.SEARCH), None)
                
                insert_index = (local_data_index or search_index or 0) + 1
                
                plan.steps.insert(insert_index, PlanStep(
                    plan_id=plan.id,
                    agent_type=AgentType.CLOUD,
                    description=f"Access cloud resources as alternative source of information"
                ))
        
        # Ensure we don't exceed max steps
        if len(plan.steps) > self.max_steps:
            self.logger.warning(f"Adapted plan exceeded max steps ({len(plan.steps)} > {self.max_steps}), truncating")
            
            # Keep completed steps and enough pending steps to stay within max_steps
            completed_steps = [step for step in plan.steps if step.status != "pending"]
            pending_steps = [step for step in plan.steps if step.status == "pending"]
            
            remaining_slots = self.max_steps - len(completed_steps)
            if remaining_slots > 0:
                plan.steps = completed_steps + pending_steps[:remaining_slots]
            else:
                plan.steps = completed_steps[:self.max_steps]
        
        return plan
    
    def _query_needs_search(self, query_text: str) -> bool:
        """
        Determine if the query needs external search.
        
        Args:
            query_text: The query text
            
        Returns:
            True if search is needed, False otherwise
        """
        # Check for keywords that suggest external search is needed
        search_keywords = {
            "search", "find", "look up", "latest", "recent", "news",
            "current", "update", "information about", "data on"
        }
        
        query_lower = query_text.lower()
        
        # Check if any search keyword is in the query
        for keyword in search_keywords:
            if keyword in query_lower:
                return True
        
        # Default to True for most queries
        return True
    
    def _query_needs_local_data(self, query_text: str) -> bool:
        """
        Determine if the query needs local data access.
        
        Args:
            query_text: The query text
            
        Returns:
            True if local data access is needed, False otherwise
        """
        # Check for keywords that suggest local data access is needed
        local_data_keywords = {
            "local", "file", "document", "internal", "our", "company",
            "dataset", "database", "data", "report", "analysis"
        }
        
        query_lower = query_text.lower()
        
        # Check if any local data keyword is in the query
        for keyword in local_data_keywords:
            if keyword in query_lower:
                return True
        
        return False
    
    def _query_needs_cloud(self, query_text: str) -> bool:
        """
        Determine if the query needs cloud resource access.
        
        Args:
            query_text: The query text
            
        Returns:
            True if cloud access is needed, False otherwise
        """
        # Check for keywords that suggest cloud access is needed
        cloud_keywords = {
            "cloud", "aws", "azure", "s3", "bucket", "remote", "service",
            "api", "endpoint", "lambda", "function", "storage"
        }
        
        query_lower = query_text.lower()
        
        # Check if any cloud keyword is in the query
        for keyword in cloud_keywords:
            if keyword in query_lower:
                return True
        
        return False