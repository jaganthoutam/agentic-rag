"""
Main implementation of the Agentic RAG system.

This module serves as the entry point for the Agentic RAG application,
coordinating the workflow between different components.
"""

import json
import logging
import time
import os
from typing import Dict, List, Optional, Union

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"Error loading .env file: {str(e)}")

from core import AgentType, Query, Plan, RagOutput
from memory.base import BaseMemory
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from planning.base import BasePlanner
from planning.react import ReActPlanner
from planning.cot import ChainOfThoughtPlanner
from agents.base import BaseAgent
from agents.aggregator import AggregatorAgent
from agents.search import SearchAgent
from agents.local_data import LocalDataAgent
from agents.cloud import CloudAgent
from agents.generative import GenerativeAgent
from agents.memory import MemoryAgent


class AgenticRag:
    """
    Main Agentic RAG implementation.
    
    This class coordinates the workflow between memory components,
    planning modules, and agent implementations to process queries
    and generate responses.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the Agentic RAG system.
        
        Args:
            config_path: Path to the configuration file
        """
        self._load_config(config_path)
        self._setup_logging()
        self._initialize_components()
        
        self.logger.info("Agentic RAG system initialized")
    
    def _load_config(self, config_path: str) -> None:
        """
        Load configuration from the specified file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            self.app_config = self.config["app"]
            self.log_config = self.config["logging"]
            self.api_config = self.config["api"]
            self.memory_config = self.config["memory"]
            self.planning_config = self.config["planning"]
            self.agents_config = self.config["agents"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            # Fall back to default configuration
            raise RuntimeError(f"Failed to load configuration: {str(e)}")
    
    def _setup_logging(self) -> None:
        """Set up logging based on configuration."""
        log_level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        
        log_level = log_level_map.get(
            self.log_config.get("level", "info").lower(),
            logging.INFO
        )
        
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            if self.log_config.get("format") == "text"
            else '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
        )
        
        handlers = []
        if self.log_config.get("output") in ["console", "both"]:
            handlers.append(logging.StreamHandler())
        
        if self.log_config.get("output") in ["file", "both"] and self.log_config.get("file_path"):
            handlers.append(logging.FileHandler(self.log_config["file_path"]))
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=handlers
        )
        
        self.logger = logging.getLogger("agentic_rag")
    
    def _initialize_components(self) -> None:
        """Initialize memory, planning, and agent components."""
        # Initialize memory components
        self.memories: Dict[str, BaseMemory] = {}
        
        if self.memory_config["short_term"]["enabled"]:
            self.memories["short_term"] = ShortTermMemory(
                capacity=self.memory_config["short_term"]["capacity"],
                ttl=self.memory_config["short_term"]["ttl"]
            )
            self.logger.info("Short-term memory initialized")
        
        if self.memory_config["long_term"]["enabled"]:
            self.memories["long_term"] = LongTermMemory(
                connection_string=self.memory_config["long_term"]["connection_string"],
                table_name=self.memory_config["long_term"].get("table_name", "long_term_memory")
            )
            self.logger.info("Long-term memory initialized")
        
        # Initialize planning components
        self.planners: Dict[str, BasePlanner] = {}
        
        if self.planning_config["react"]["enabled"]:
            self.planners["react"] = ReActPlanner(
                max_steps=self.planning_config["react"]["max_steps"],
                timeout=self.planning_config["react"].get("timeout", 60)
            )
            self.logger.info("ReAct planner initialized")
        
        if self.planning_config["cot"]["enabled"]:
            self.planners["cot"] = ChainOfThoughtPlanner(
                max_depth=self.planning_config["cot"]["max_depth"]
            )
            self.logger.info("Chain of Thought planner initialized")
        
        # Initialize agent components
        self.agents: Dict[AgentType, BaseAgent] = {}
        
        if self.agents_config["aggregator"]["enabled"]:
            self.agents[AgentType.AGGREGATOR] = AggregatorAgent(
                timeout=self.agents_config["aggregator"]["timeout"],
                max_agents=self.agents_config["aggregator"].get("max_agents", 5)
            )
            self.logger.info("Aggregator agent initialized")
        
        if self.agents_config["search"]["enabled"]:
            self.agents[AgentType.SEARCH] = SearchAgent(
                engine=self.agents_config["search"]["engine"],
                api_key=self.agents_config["search"]["api_key"],
                max_results=self.agents_config["search"].get("max_results", 10)
            )
            self.logger.info("Search agent initialized")
        
        if self.agents_config["local_data"]["enabled"]:
            self.agents[AgentType.LOCAL_DATA] = LocalDataAgent(
                data_path=self.agents_config["local_data"]["data_path"],
                formats=self.agents_config["local_data"].get("formats", ["csv", "json", "pdf"])
            )
            self.logger.info("Local data agent initialized")
        
        if self.agents_config["cloud"]["enabled"]:
            self.agents[AgentType.CLOUD] = CloudAgent(
                provider=self.agents_config["cloud"]["provider"],
                region=self.agents_config["cloud"]["region"],
                credentials=self.agents_config["cloud"]["credentials"]
            )
            self.logger.info("Cloud agent initialized")
        
        if self.agents_config["generative"]["enabled"]:
            self.agents[AgentType.GENERATIVE] = GenerativeAgent(
                provider=self.agents_config["generative"].get("provider", "openai"),
                model=self.agents_config["generative"]["model"],
                api_key=self.agents_config["generative"]["api_key"],
                max_tokens=self.agents_config["generative"].get("max_tokens", 4000),
                temperature=self.agents_config["generative"].get("temperature", 0.7)
            )
            self.logger.info(f"Generative agent initialized with provider={self.agents_config['generative'].get('provider', 'openai')}")
        
        if self.agents_config["memory_agent"]["enabled"]:
            self.agents[AgentType.MEMORY] = MemoryAgent(
                memories=self.memories
            )
            self.logger.info("Memory agent initialized")
    
    def process_query(self, query_text: str) -> RagOutput:
        """
        Process a query through the Agentic RAG system.
        
        Args:
            query_text: Text of the query to process
            
        Returns:
            RagOutput object containing the response and metadata
        """
        start_time = time.time()
        query = Query(text=query_text)
        self.logger.info(f"Processing query: {query.id}")
        
        try:
            # Check memory first
            memory_result = None
            if AgentType.MEMORY in self.agents:
                self.logger.debug(f"Checking memory for query: {query.id}")
                memory_result = self.agents[AgentType.MEMORY].process(query)
                self.logger.info(f"Memory agent result: {memory_result.confidence if memory_result else 'None'}")
            
            # Check if we have a high-confidence memory result
            if memory_result and memory_result.confidence >= 0.8:
                self.logger.info(f"Using high-confidence memory result for query: {query.id}")
                # Build the output directly from memory result
                processing_time = time.time() - start_time
                output = RagOutput(
                    query_id=query.id,
                    response=memory_result.documents[0].content if memory_result and memory_result.documents else "Unable to generate response",
                    documents=memory_result.documents if memory_result else [],
                    plan_id=None,
                    processing_time=processing_time,
                    confidence=memory_result.confidence if memory_result else 0.0,
                    metadata={
                        "memory_hit": True,
                        "agent_counts": {}  # No agents used when using memory directly
                    }
                )
                
                self.logger.info(f"Query processed successfully using memory: {query.id} in {processing_time:.2f}s")
                return output
            
            # Create and execute a plan if no high-confidence memory match
            plan = None
            # Choose planner - default to ReAct if available
            planner = self.planners.get("react", next(iter(self.planners.values())))
            self.logger.debug(f"Creating plan for query: {query.id} using {planner.__class__.__name__}")
            plan = planner.create_plan(query, self.agents)
            
            # Execute the plan
            self.logger.debug(f"Executing plan: {plan.id}")
            plan.start_execution()
            results = []
            
            for step in plan.steps:
                if step.agent_type in self.agents:
                    step.start()
                    try:
                        self.logger.debug(f"Executing step: {step.id} with agent: {step.agent_type.value}")
                        result = self.agents[step.agent_type].process(query)
                        step.complete(result)
                        results.append(result)
                        self.logger.info(f"Step {step.id} completed with confidence: {result.confidence}")
                    except Exception as e:
                        self.logger.error(f"Error executing step {step.id}: {str(e)}")
                        step.fail()
                else:
                    self.logger.warning(f"Agent not available for step: {step.agent_type.value}")
                    step.fail()
            
            if all(step.status == "completed" for step in plan.steps):
                plan.complete()
            else:
                plan.fail()
            
            # Use aggregator to combine results
            if AgentType.AGGREGATOR in self.agents and results:
                self.logger.debug(f"Aggregating results for query: {query.id}")
                aggregated_result = self.agents[AgentType.AGGREGATOR].aggregate(query, results)
                self.logger.info(f"Aggregator result confidence: {aggregated_result.confidence}")
            else:
                # Fallback if no aggregator
                self.logger.warning("No aggregator agent available, using best individual result")
                aggregated_result = max(results, key=lambda r: r.confidence) if results else None
            
            # Generate final response using the generative agent
            if AgentType.GENERATIVE in self.agents and aggregated_result:
                self.logger.debug(f"Generating final response for query: {query.id}")
                final_result = self.agents[AgentType.GENERATIVE].generate_response(query, aggregated_result)
                self.logger.info(f"Generative agent result confidence: {final_result.confidence}")
            else:
                self.logger.warning("No generative agent available, using aggregated result")
                final_result = aggregated_result
            
            # Build the output
            processing_time = time.time() - start_time
            output = RagOutput(
                query_id=query.id,
                response=final_result.documents[0].content if final_result and final_result.documents else "Unable to generate response",
                documents=final_result.documents if final_result else [],
                plan_id=plan.id if plan else None,
                processing_time=processing_time,
                confidence=final_result.confidence if final_result else 0.0,
                metadata={
                    "memory_hit": False,
                    "agent_counts": {agent_type.value: len([s for s in plan.steps if s.agent_type == agent_type]) for agent_type in AgentType if plan}
                }
            )
            
            # Store in memory
            if final_result and final_result.confidence >= 0.5:
                for memory in self.memories.values():
                    memory.store(query, final_result)
            
            self.logger.info(f"Query processed successfully: {query.id} in {processing_time:.2f}s")
            return output
            
        except Exception as e:
            self.logger.error(f"Error processing query {query.id}: {str(e)}")
            processing_time = time.time() - start_time
            return RagOutput(
                query_id=query.id,
                response=f"Error processing query: {str(e)}",
                processing_time=processing_time,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def shutdown(self) -> None:
        """Shut down the Agentic RAG system."""
        for memory in self.memories.values():
            memory.close()
        
        self.logger.info("Agentic RAG system shut down")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic RAG System")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    args = parser.parse_args()
    
    rag = AgenticRag(config_path=args.config)
    
    # Example query
    query = "What are the latest developments in AI research?"
    result = rag.process_query(query)
    print(f"Query: {query}")
    print(f"Response: {result.response}")
    print(f"Processing time: {result.processing_time:.2f}s")
    print(f"Confidence: {result.confidence:.2f}")
    
    rag.shutdown()