"""
Unit tests for planning components.

This module contains unit tests for the planning components of the Agentic RAG system.
"""

import unittest
from unittest.mock import MagicMock, patch

from core import AgentType, Query, Document, AgentResult, Plan
from planning import ReActPlanner, ChainOfThoughtPlanner
from agents import BaseAgent


class TestReActPlanner(unittest.TestCase):
    """Tests for the ReActPlanner component."""
    
    def setUp(self):
        """Set up test environment."""
        self.planner = ReActPlanner(max_steps=5, timeout=30)
        
        # Create mock agents
        self.agents = {
            AgentType.MEMORY: MagicMock(spec=BaseAgent),
            AgentType.SEARCH: MagicMock(spec=BaseAgent),
            AgentType.LOCAL_DATA: MagicMock(spec=BaseAgent),
            AgentType.AGGREGATOR: MagicMock(spec=BaseAgent),
            AgentType.GENERATIVE: MagicMock(spec=BaseAgent)
        }
        
        # Set agent types
        for agent_type, agent in self.agents.items():
            agent.agent_type = agent_type
    
    def test_create_plan(self):
        """Test creating a plan."""
        query = Query(text="What are the latest developments in AI research?")
        
        # Create plan
        plan = self.planner.create_plan(query, self.agents)
        
        # Verify plan
        self.assertEqual(plan.query_id, query.id)
        self.assertEqual(plan.planner_type, "react")
        self.assertEqual(plan.status, "created")
        
        # Should include steps for memory, search, aggregation, and generation
        self.assertGreaterEqual(len(plan.steps), 3)
        
        # First step should be memory check
        self.assertEqual(plan.steps[0].agent_type, AgentType.MEMORY)
        
        # Should include a search step
        search_steps = [s for s in plan.steps if s.agent_type == AgentType.SEARCH]
        self.assertEqual(len(search_steps), 1)
        
        # Should include a generative step
        gen_steps = [s for s in plan.steps if s.agent_type == AgentType.GENERATIVE]
        self.assertEqual(len(gen_steps), 1)
        
        # Last step should be generative
        self.assertEqual(plan.steps[-1].agent_type, AgentType.GENERATIVE)
    
    def test_plan_max_steps(self):
        """Test that plan doesn't exceed max steps."""
        query = Query(text="Complex query requiring many sources")
        
        # Set a very low max_steps
        self.planner.max_steps = 2
        
        # Create plan
        plan = self.planner.create_plan(query, self.agents)
        
        # Verify plan length is limited
        self.assertLessEqual(len(plan.steps), 2)
    
    def test_adapt_plan_with_memory_hit(self):
        """Test adapting a plan when memory returns a good result."""
        query = Query(text="Test query")
        
        # Create initial plan
        plan = Plan(query_id=query.id, planner_type="react")
        plan.add_step(AgentType.MEMORY, "Check memory")
        plan.add_step(AgentType.SEARCH, "Search external sources")
        plan.add_step(AgentType.LOCAL_DATA, "Check local data")
        plan.add_step(AgentType.AGGREGATOR, "Aggregate results")
        plan.add_step(AgentType.GENERATIVE, "Generate response")
        
        # Create a high-confidence memory result
        memory_result = AgentResult(
            agent_id="memory_agent",
            agent_type=AgentType.MEMORY,
            query_id=query.id,
            documents=[Document(content="Memory content", source="memory")],
            confidence=0.9,
            processing_time=0.1,
            metadata={}
        )
        
        # Adapt plan based on the memory result
        adapted_plan = self.planner.adapt_plan(plan, [memory_result], self.agents)
        
        # Verify adapted plan
        self.assertNotEqual(adapted_plan.id, plan.id)  # Should be a new plan
        
        # Should skip search and local data steps
        agent_types = [step.agent_type for step in adapted_plan.steps]
        self.assertNotIn(AgentType.SEARCH, agent_types)
        self.assertNotIn(AgentType.LOCAL_DATA, agent_types)
        
        # Should keep memory, aggregator, and generative steps
        self.assertIn(AgentType.MEMORY, agent_types)
        self.assertIn(AgentType.GENERATIVE, agent_types)
    
    def test_adapt_plan_with_failed_search(self):
        """Test adapting a plan when search returns no results."""
        query = Query(text="Test query")
        
        # Create initial plan with just search and generative steps
        plan = Plan(query_id=query.id, planner_type="react")
        search_step = plan.add_step(AgentType.SEARCH, "Search external sources")
        plan.add_step(AgentType.GENERATIVE, "Generate response")
        
        # Mark search step as completed
        search_step.status = "completed"
        
        # Create a search result with no documents
        search_result = AgentResult(
            agent_id="search_agent",
            agent_type=AgentType.SEARCH,
            query_id=query.id,
            documents=[],  # No documents found
            confidence=0.0,
            processing_time=0.5,
            metadata={}
        )
        
        # Adapt plan based on the search result
        adapted_plan = self.planner.adapt_plan(plan, [search_result], self.agents)
        
        # Verify adapted plan
        # Should add local data step if available
        agent_types = [step.agent_type for step in adapted_plan.steps]
        
        if AgentType.LOCAL_DATA in self.agents:
            self.assertIn(AgentType.LOCAL_DATA, agent_types)
        
        # Should keep generative step
        self.assertIn(AgentType.GENERATIVE, agent_types)


class TestChainOfThoughtPlanner(unittest.TestCase):
    """Tests for the ChainOfThoughtPlanner component."""
    
    def setUp(self):
        """Set up test environment."""
        self.planner = ChainOfThoughtPlanner(max_depth=3)
        
        # Create mock agents
        self.agents = {
            AgentType.MEMORY: MagicMock(spec=BaseAgent),
            AgentType.SEARCH: MagicMock(spec=BaseAgent),
            AgentType.LOCAL_DATA: MagicMock(spec=BaseAgent),
            AgentType.AGGREGATOR: MagicMock(spec=BaseAgent),
            AgentType.GENERATIVE: MagicMock(spec=BaseAgent)
        }
        
        # Set agent types
        for agent_type, agent in self.agents.items():
            agent.agent_type = agent_type
    
    def test_create_plan(self):
        """Test creating a plan."""
        query = Query(text="What is the definition of machine learning?")
        
        # Create plan
        plan = self.planner.create_plan(query, self.agents)
        
        # Verify plan
        self.assertEqual(plan.query_id, query.id)
        self.assertEqual(plan.planner_type, "cot")
        
        # Should include steps for memory, definition search, and generation
        self.assertGreaterEqual(len(plan.steps), 2)
        
        # First step should be memory check
        self.assertEqual(plan.steps[0].agent_type, AgentType.MEMORY)
        
        # Last step should be generative
        self.assertEqual(plan.steps[-1].agent_type, AgentType.GENERATIVE)
    
    def test_adapt_plan_with_sufficient_info(self):
        """Test adapting a plan when we have sufficient information."""
        query = Query(text="Test query")
        
        # Create initial plan
        plan = Plan(query_id=query.id, planner_type="cot")
        plan.add_step(AgentType.MEMORY, "Check memory")
        plan.add_step(AgentType.SEARCH, "Search for definition")
        plan.add_step(AgentType.SEARCH, "Search for examples")
        plan.add_step(AgentType.LOCAL_DATA, "Check local data")
        plan.add_step(AgentType.GENERATIVE, "Generate response")
        
        # Mark first two steps as completed
        plan.steps[0].status = "completed"
        plan.steps[1].status = "completed"
        
        # Create high-confidence search result
        search_result = AgentResult(
            agent_id="search_agent",
            agent_type=AgentType.SEARCH,
            query_id=query.id,
            documents=[Document(content="Definition content", source="search")],
            confidence=0.9,
            processing_time=0.5,
            metadata={}
        )
        
        # Adapt plan based on the search result
        adapted_plan = self.planner.adapt_plan(plan, [search_result], self.agents)
        
        # Verify adapted plan
        self.assertNotEqual(adapted_plan.id, plan.id)  # Should be a new plan
        
        # Should include completed steps
        self.assertEqual(adapted_plan.steps[0].status, "completed")
        self.assertEqual(adapted_plan.steps[1].status, "completed")
        
        # Should skip remaining information gathering steps
        # and go directly to aggregation and generation
        agent_types = [step.agent_type for step in adapted_plan.steps[2:]]
        self.assertNotIn(AgentType.LOCAL_DATA, agent_types)
        
        # Should include generative step
        self.assertIn(AgentType.GENERATIVE, agent_types)
        
        # Should include aggregator step if available
        if AgentType.AGGREGATOR in self.agents:
            self.assertIn(AgentType.AGGREGATOR, agent_types)


if __name__ == "__main__":
    unittest.main()