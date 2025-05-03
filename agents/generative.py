"""
Generative agent implementation for Agentic RAG.

This module implements an agent that generates human-like responses using OpenAI or Groq models.
"""

import json
import time
import uuid
import logging
import requests
from typing import Dict, List, Optional, Union, Any, Literal

from core import AgentType, Query, Document, AgentResult
from agents.base import BaseAgent


class GenerativeAgent(BaseAgent):
    """
    Generative agent implementation.
    
    This agent generates human-like responses using OpenAI or Groq language models.
    """
    
    def __init__(
        self, 
        provider: Literal["openai", "groq"] = "groq",
        model: str = "llama3-70b-8192", 
        api_key: str = "", 
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> None:
        """
        Initialize the generative agent.
        
        Args:
            provider: The LLM provider ("openai" or "groq")
            model: Name of the language model to use
            api_key: API key for the language model service
            max_tokens: Maximum number of tokens in generated responses
            temperature: Temperature parameter for generation (0.0-1.0)
        """
        super().__init__(agent_type=AgentType.GENERATIVE)
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.logger.info(
            f"Generative agent initialized with provider={provider}, model={model}, "
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
                source=f"generative_agent:{self.provider}:{self.model}",
                metadata={
                    "provider": self.provider,
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
                    "provider": self.provider,
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
                    "provider": self.provider,
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
                source=f"generative_agent:{self.provider}:{self.model}",
                metadata={
                    "provider": self.provider,
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
                    "provider": self.provider,
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
                    "provider": self.provider,
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
        self.logger.debug(f"Generating response with {self.provider}/{self.model}")
        
        try:
            # Prepare context for prompt
            context_str = ""
            if context_docs:
                context_str = "Context:\n"
                for i, doc in enumerate(context_docs[:5]):  # Limit to 5 docs
                    source = doc.metadata.get("title", doc.source)
                    content = doc.content[:500] + "..." if len(doc.content) > 500 else doc.content
                    context_str += f"[{i+1}] {source}\n{content}\n\n"
            
            # Call the appropriate API based on provider
            if self.provider == "openai":
                return self._call_openai_api(system_prompt, query_text, context_str)
            elif self.provider == "groq":
                return self._call_groq_api(system_prompt, query_text, context_str)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            raise
    
    def _call_openai_api(self, system_prompt: str, query_text: str, context_str: str) -> str:
        """
        Call the OpenAI API to generate a response.
        
        Args:
            system_prompt: System prompt for the model
            query_text: The query text
            context_str: Context information
            
        Returns:
            Generated response text
        """
        if not self.api_key:
            self.logger.warning("OpenAI API key not set, using mock response")
            return self._generate_mock_response(query_text, context_str != "")
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add context if available
            if context_str:
                messages.append({"role": "user", "content": f"Here is context information:\n\n{context_str}"})
            
            # Add user query
            messages.append({"role": "user", "content": query_text})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            self.logger.error("OpenAI package not installed. Install with: pip install openai")
            return self._generate_mock_response(query_text, context_str != "")
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {str(e)}")
            return self._generate_mock_response(query_text, context_str != "")
    
    def _call_groq_api(self, system_prompt: str, query_text: str, context_str: str) -> str:
        """
        Call the Groq API to generate a response.
        
        Args:
            system_prompt: System prompt for the model
            query_text: The query text
            context_str: Context information
            
        Returns:
            Generated response text
        """
        if not self.api_key:
            self.logger.warning("Groq API key not set, using mock response")
            return self._generate_mock_response(query_text, context_str != "")
        
        try:
            import groq
            client = groq.Groq(api_key=self.api_key)
            
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add context if available
            if context_str:
                messages.append({"role": "user", "content": f"Here is context information:\n\n{context_str}"})
            
            # Add user query
            messages.append({"role": "user", "content": query_text})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            self.logger.error("Groq package not installed. Install with: pip install groq")
            return self._generate_mock_response(query_text, context_str != "")
        except Exception as e:
            self.logger.error(f"Error calling Groq API: {str(e)}")
            return self._generate_mock_response(query_text, context_str != "")
    
    def _call_api_directly(self, provider: str, model: str, messages: List[Dict[str, str]]) -> str:
        """
        Call the API directly using requests when the package is not available.
        
        Args:
            provider: The provider name ("openai" or "groq")
            model: The model name
            messages: The messages to send
            
        Returns:
            Generated response text
        """
        try:
            base_url = "https://api.openai.com/v1" if provider == "openai" else "https://api.groq.com/openai/v1"
            
            response = requests.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                },
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            self.logger.error(f"Error calling {provider} API directly: {str(e)}")
            return self._generate_mock_response(messages[-1]["content"], len(messages) > 2)
    
    def _generate_mock_response(self, query_text: str, has_context: bool) -> str:
        """
        Generate a mock response when the API call fails.
        
        Args:
            query_text: The query text
            has_context: Whether context is available
            
        Returns:
            Generated mock response text
        """
        self.logger.debug("Generating mock response")
        
        # Simulate API call delay
        time.sleep(0.5)
        
        if not has_context:
            # Direct query response
            response = f"Based on my knowledge, {query_text} involves several important aspects. "
            response += "First, it's essential to understand the core concepts. "
            response += "Additionally, there are multiple perspectives to consider. "
            response += "I hope this helps answer your query."
        else:
            # Context-based response
            response = f"Based on the provided information, {query_text} can be addressed as follows. "
            response += "The context suggests several important considerations. "
            response += "Taking all sources into account, I recommend considering multiple factors. "
            response += "Let me know if you'd like more specific information on any aspect."
        
        return response