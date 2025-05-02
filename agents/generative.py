"""
Generative agent implementation for Agentic RAG.

This module implements an agent that generates human-like responses using a language model.
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Union, Any

from core import AgentType, Query, Document, AgentResult
from agents.base import BaseAgent


class GenerativeAgent(BaseAgent):
    """
    Generative agent implementation.
    
    This agent generates human-like responses using a language model.
    """
    
    def __init__(
        self, 
        model: str = "claude-3-opus-20240229", 
        api_key: str = "", 
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> None:
        """
        Initialize the generative agent.
        
        Args:
            model: Name of the language model to use
            api_key: API key for the language model service
            max_tokens: Maximum number of tokens in generated responses
            temperature: Temperature parameter for generation (0.0-1.0)
        """
        super().__init__(agent_type=AgentType.GENERATIVE)
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.logger.info(
            f"Generative agent initialized with model={model}, "
            f"max_tokens={max_tokens}, temperature={temperature}"
        )
    
    @BaseAgent.measure_execution_time
    def process(self, query: Query) -> AgentResult:
        """
        Process the query by generating a response based purely on the query.
        
        Args:
            query: The query to process
            
        Returns:
            An AgentResult containing the generated response
        """
        self.logger.debug(f"Processing query: {query.id}")
        
        try:
            # Generate response using only the query
            generated_text = self._generate_response(
                query.text,
                [],
                system_prompt=f"Generate a helpful response to the following query: {query.text}"
            )
            
            # Create document
            document = Document(
                content=generated_text,
                source=f"generative_agent:{self.model}",
                metadata={
                    "model": self.model,
                    "query": query.text,
                    "temperature": self.temperature,
                    "generation_type": "direct_query"
                }
            )
            
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[document],
                confidence=0.7,  # Moderate confidence for generation without context
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                    "generation_type": "direct_query"
                }
            )
        except Exception as e:
            self.logger.error(f"Error in generative agent: {str(e)}")
            
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[],
                confidence=0.0,
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "error": str(e),
                    "model": self.model
                }
            )
    
    @BaseAgent.measure_execution_time
    def generate_response(self, query: Query, context_result: AgentResult) -> AgentResult:
        """
        Generate a response based on the query and context.
        
        Args:
            query: The query to process
            context_result: Result containing context documents
            
        Returns:
            An AgentResult containing the generated response
        """
        self.logger.debug(f"Generating response for query: {query.id} with context")
        
        try:
            # Extract context documents
            context_docs = context_result.documents
            
            if not context_docs:
                self.logger.warning("No context documents provided, falling back to direct query")
                return self.process(query)
            
            # Generate response using query and context
            system_prompt = (
                f"Generate a helpful response to the following query: {query.text}\n"
                f"Use the provided context to inform your response."
            )
            
            generated_text = self._generate_response(
                query.text,
                context_docs,
                system_prompt=system_prompt
            )
            
            # Create document
            document = Document(
                content=generated_text,
                source=f"generative_agent:{self.model}",
                metadata={
                    "model": self.model,
                    "query": query.text,
                    "temperature": self.temperature,
                    "context_count": len(context_docs),
                    "context_sources": [doc.source for doc in context_docs[:5]],
                    "generation_type": "context_based"
                }
            )
            
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[document],
                confidence=0.9,  # Higher confidence for generation with context
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "model": self.model,
                    "temperature": self.temperature,
                    "context_count": len(context_docs),
                    "generation_type": "context_based"
                }
            )
        except Exception as e:
            self.logger.error(f"Error in generative agent: {str(e)}")
            
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[],
                confidence=0.0,
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "error": str(e),
                    "model": self.model
                }
            )
    
    def _generate_response(
        self, 
        query_text: str, 
        context_docs: List[Document],
        system_prompt: str
    ) -> str:
        """
        Generate a response using the language model.
        
        Args:
            query_text: The query text
            context_docs: List of context documents
            system_prompt: System prompt for the model
            
        Returns:
            Generated response text
        """
        # In a real implementation, this would call the language model API
        # For now, create a mock response
        self.logger.debug(f"Generating response with model: {self.model}")
        
        try:
            # Simulate API call delay
            time.sleep(1.5)
            
            # Prepare context for prompt
            context_str = ""
            if context_docs:
                context_str = "Context:\n"
                for i, doc in enumerate(context_docs[:5]):  # Limit to 5 docs
                    source = doc.metadata.get("title", doc.source)
                    content = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
                    context_str += f"[{i+1}] {source}\n{content}\n\n"
            
            # Create a mock response based on the query and context
            if not context_docs:
                # Direct query response
                response = f"Based on my knowledge, {query_text} involves several important aspects. "
                response += "First, it's essential to understand the core concepts. "
                response += "Additionally, there are multiple perspectives to consider. "
                response += "I hope this helps answer your query."
            else:
                # Context-based response
                response = f"Based on the provided information, {query_text} can be addressed as follows. "
                
                # Reference some of the context
                if len(context_docs) >= 1:
                    response += f"According to the first source, {context_docs[0].content[:50]}... "
                
                if len(context_docs) >= 2:
                    response += f"The second source adds that {context_docs[1].content[:50]}... "
                
                response += "Taking all sources into account, I recommend considering multiple factors. "
                response += "Let me know if you'd like more specific information on any aspect."
            
            self.logger.debug(f"Generated response of length {len(response)}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise