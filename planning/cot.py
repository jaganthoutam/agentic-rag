"""
Chain of Thought planner implementation for Agentic RAG.

This module implements the Chain of Thought planning approach,
which uses step-by-step reasoning to decompose complex tasks.
"""

import uuid
from typing import Dict, List, Optional, Tuple

from core import AgentType, Query, Plan, PlanStep, AgentResult
from planning.base import BasePlanner
from agents.base import BaseAgent


class ChainOfThoughtPlanner(BasePlanner):
    """
    Chain of Thought planner implementation.
    
    This planner implements the Chain of Thought approach,
    which uses step-by-step reasoning to decompose complex tasks.
    """
    
    def __init__(self, max_depth: int = 5) -> None:
        """
        Initialize the Chain of Thought planner.
        
        Args:
            max_depth: Maximum depth of reasoning steps
        """
        super().__init__()
        self.max_depth = max_depth
        self.logger.info(f"Chain of Thought planner initialized with max_depth={max_depth}")
    
    def create_plan(self, query: Query, available_agents: Dict[AgentType, BaseAgent]) -> Plan:
        """
        Create an execution plan for the given query using available agents.
        
        Args:
            query: The query to create a plan for
            available_agents: Dictionary of available agents by type
            
        Returns:
            A Plan object containing the steps to execute
        """
        plan = Plan(query_id=query.id, planner_type="cot")
        
        # Analyze the query to determine required information and dependencies
        query_analysis = self._analyze_query(query.text)
        
        # Start with memory check if available
        if AgentType.MEMORY in available_agents:
            plan.add_step(
                agent_type=AgentType.MEMORY,
                description=f"Retrieve relevant prior knowledge about '{query.text}'"
            )
        
        # Add information gathering steps based on query analysis
        for info_need, description in query_analysis:
            agent_type = self._map_info_need_to_agent(info_need, available_agents)
            
            if agent_type:
                plan.add_step(
                    agent_type=agent_type,
                    description=description
                )
        
        # Add synthesis steps
        if len(query_analysis) > 1 and AgentType.AGGREGATOR in available_agents:
            plan.add_step(
                agent_type=AgentType.AGGREGATOR,
                description=f"Synthesize information from multiple sources"
            )
        
        # Add response generation step
        if AgentType.GENERATIVE in available_agents:
            plan.add_step(
                agent_type=AgentType.GENERATIVE,
                description=f"Generate comprehensive response to '{query.text}'"
            )
        
        # Ensure the plan is valid
        if not self.validate_plan(plan, available_agents):
            self.logger.warning("Generated plan is invalid, falling back to simple plan")
            plan = self._create_simple_plan(query, available_agents)
        
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
        # Check if we have enough information
        if self._has_sufficient_information(results_so_far):
            # Skip remaining information gathering steps
            self.logger.info("Sufficient information gathered, adapting plan")
            
            new_plan = Plan(
                id=str(uuid.uuid4()),
                query_id=plan.query_id,
                planner_type="cot",
                status="created"
            )
            
            # Copy completed steps
            for step in plan.steps:
                if step.status != "pending":
                    new_step = PlanStep(
                        plan_id=new_plan.id,
                        agent_type=step.agent_type,
                        description=step.description,
                        status=step.status,
                        result=step.result,
                        start_time=step.start_time,
                        end_time=step.end_time
                    )
                    new_plan.steps.append(new_step)
            
            # Add aggregation step if needed
            if AgentType.AGGREGATOR in available_agents:
                new_plan.add_step(
                    agent_type=AgentType.AGGREGATOR,
                    description="Synthesize gathered information"
                )
            
            # Add response generation step
            if AgentType.GENERATIVE in available_agents:
                new_plan.add_step(
                    agent_type=AgentType.GENERATIVE,
                    description="Generate final response"
                )
            
            return new_plan
        
        # Check if we need additional information
        missing_info = self._identify_missing_information(results_so_far, plan.query_id)
        
        if missing_info:
            self.logger.info(f"Identified missing information: {missing_info}")
            
            # Create a new plan with additional steps
            new_plan = Plan(
                id=str(uuid.uuid4()),
                query_id=plan.query_id,
                planner_type="cot",
                status="created"
            )
            
            # Copy existing steps
            for step in plan.steps:
                new_step = PlanStep(
                    plan_id=new_plan.id,
                    agent_type=step.agent_type,
                    description=step.description,
                    status=step.status,
                    result=step.result,
                    start_time=step.start_time,
                    end_time=step.end_time
                )
                new_plan.steps.append(new_step)
            
            # Add new steps for missing information
            for info_need, description in missing_info:
                agent_type = self._map_info_need_to_agent(info_need, available_agents)
                
                if agent_type:
                    new_plan.add_step(
                        agent_type=agent_type,
                        description=description
                    )
            
            return new_plan
        
        # No adaptation needed
        return plan
    
    def _analyze_query(self, query_text: str) -> List[Tuple[str, str]]:
        """
        Analyze the query to determine required information and dependencies.
        
        Args:
            query_text: The query text
            
        Returns:
            A list of tuples (info_need, description)
        """
        # This is a simplified implementation. A real implementation would use
        # a language model to decompose the query.
        
        query_lower = query_text.lower()
        results = []
        
        # Check for factual information needs
        if any(keyword in query_lower for keyword in ["who", "what", "when", "where", "how", "why"]):
            results.append(("factual", f"Retrieve factual information about '{query_text}'"))
        
        # Check for definitions or explanations
        if any(keyword in query_lower for keyword in ["define", "explain", "mean", "definition"]):
            results.append(("definition", f"Retrieve definition or explanation for concepts in '{query_text}'"))
        
        # Check for comparisons
        if any(keyword in query_lower for keyword in ["compare", "difference", "versus", "vs"]):
            results.append(("comparison", f"Compare entities mentioned in '{query_text}'"))
        
        # Check for data or statistics
        if any(keyword in query_lower for keyword in ["data", "statistic", "number", "percent", "figure"]):
            results.append(("data", f"Retrieve data or statistics related to '{query_text}'"))
        
        # Check for recommendations
        if any(keyword in query_lower for keyword in ["recommend", "suggestion", "best", "top"]):
            results.append(("recommendation", f"Generate recommendations based on '{query_text}'"))
        
        # If no specific needs identified, add a general search
        if not results:
            results.append(("general", f"Search for general information about '{query_text}'"))
        
        return results
    
    def _map_info_need_to_agent(self, info_need: str, available_agents: Dict[AgentType, BaseAgent]) -> Optional[AgentType]:
        """
        Map an information need to an appropriate agent type.
        
        Args:
            info_need: The information need
            available_agents: Dictionary of available agents by type
            
        Returns:
            An agent type, or None if no appropriate agent is available
        """
        # Map information needs to agent types
        agent_mapping = {
            "factual": AgentType.SEARCH,
            "definition": AgentType.SEARCH,
            "comparison": AgentType.SEARCH,
            "data": AgentType.LOCAL_DATA,
            "recommendation": AgentType.GENERATIVE,
            "general": AgentType.SEARCH
        }
        
        # Get the preferred agent type
        preferred_agent = agent_mapping.get(info_need)
        
        if preferred_agent in available_agents:
            return preferred_agent
        
        # Fall back to search for most information needs
        if info_need != "recommendation" and AgentType.SEARCH in available_agents:
            return AgentType.SEARCH
        
        # No appropriate agent available
        return None
    
    def _create_simple_plan(self, query: Query, available_agents: Dict[AgentType, BaseAgent]) -> Plan:
        """
        Create a simple fallback plan.
        
        Args:
            query: The query to create a plan for
            available_agents: Dictionary of available agents by type
            
        Returns:
            A simple Plan object
        """
        plan = Plan(query_id=query.id, planner_type="cot")
        
        # Memory check
        if AgentType.MEMORY in available_agents:
            plan.add_step(
                agent_type=AgentType.MEMORY,
                description=f"Check memory for '{query.text}'"
            )
        
        # Search
        if AgentType.SEARCH in available_agents:
            plan.add_step(
                agent_type=AgentType.SEARCH,
                description=f"Search for information about '{query.text}'"
            )
        
        # Generative response
        if AgentType.GENERATIVE in available_agents:
            plan.add_step(
                agent_type=AgentType.GENERATIVE,
                description=f"Generate response to '{query.text}'"
            )
        
        return plan
    
    def _has_sufficient_information(self, results: List[AgentResult]) -> bool:
        """
        Determine if we have sufficient information to generate a response.
        
        Args:
            results: Results obtained so far
            
        Returns:
            True if we have sufficient information, False otherwise
        """
        # Simple heuristic: if we have at least one high-confidence result,
        # we have sufficient information
        for result in results:
            if result.confidence >= 0.8:
                return True
        
        # If we have results from multiple sources, that's also sufficient
        agent_types = set(result.agent_type for result in results)
        if len(agent_types) >= 2:
            return True
        
        return False
    
    def _identify_missing_information(self, results: List[AgentResult], query_id: str) -> List[Tuple[str, str]]:
        """
        Identify missing information needed to complete the task.
        
        Args:
            results: Results obtained so far
            query_id: ID of the query
            
        Returns:
            A list of tuples (info_need, description) for missing information
        """
        # This is a simplified implementation. A real implementation would
        # analyze the content of results to identify gaps.
        
        # Get the query from the first result
        if not results:
            return []
        
        query_text = ""
        for result in results:
            if hasattr(result, "query_id") and result.query_id == query_id:
                # Ideally we would have access to the original query text here
                # For now, assume it's available in metadata
                query_text = result.metadata.get("query_text", "")
                break
        
        if not query_text:
            return []
        
        # Check if we have results from different agent types
        agent_types = set(result.agent_type for result in results)
        
        missing = []
        
        # If we only have results from memory, we might need external information
        if agent_types == {AgentType.MEMORY}:
            missing.append(("general", f"Search for external information about '{query_text}'"))
        
        # If we only have results from search, we might need local data
        if agent_types == {AgentType.SEARCH}:
            has_low_confidence = any(result.confidence < 0.6 for result in results)
            if has_low_confidence:
                missing.append(("data", f"Check local data sources for information about '{query_text}'"))
        
        return missing