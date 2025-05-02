"""
Aggregator agent implementation for Agentic RAG.

This module implements an agent that aggregates and synthesizes results from other agents.
"""

import time
import uuid
from typing import Dict, List, Optional, Set, Tuple

from core import AgentType, Query, Document, AgentResult
from agents.base import BaseAgent


class AggregatorAgent(BaseAgent):
    """
    Aggregator agent implementation.
    
    This agent aggregates and synthesizes results from other agents.
    """
    
    def __init__(self, timeout: int = 30, max_agents: int = 5) -> None:
        """
        Initialize the aggregator agent.
        
        Args:
            timeout: Timeout in seconds for aggregation
            max_agents: Maximum number of agent results to aggregate
        """
        super().__init__(agent_type=AgentType.AGGREGATOR)
        self.timeout = timeout
        self.max_agents = max_agents
        self.logger.info(f"Aggregator agent initialized with timeout={timeout}s, max_agents={max_agents}")
    
    @BaseAgent.measure_execution_time
    def process(self, query: Query) -> AgentResult:
        """
        Process the query by aggregating results from other agents.
        
        Args:
            query: The query to process
            
        Returns:
            An AgentResult containing the aggregated information
        """
        self.logger.debug(f"Processing query: {query.id}")
        
        # For single agent processing, we need to have results from other agents
        # This would typically be called directly with results
        return AgentResult(
            agent_id=self.id,
            agent_type=self.agent_type,
            query_id=query.id,
            documents=[],
            confidence=0.0,
            processing_time=0.0,  # Will be set by decorator
            metadata={"error": "No agent results provided for aggregation"}
        )
    
    @BaseAgent.measure_execution_time
    def aggregate(self, query: Query, results: List[AgentResult]) -> AgentResult:
        """
        Aggregate results from multiple agents.
        
        Args:
            query: The original query
            results: List of agent results to aggregate
            
        Returns:
            An AgentResult containing the aggregated information
        """
        start_time = time.time()
        self.logger.debug(f"Aggregating {len(results)} results for query: {query.id}")
        
        if not results:
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[],
                confidence=0.0,
                processing_time=0.0,  # Will be set by decorator
                metadata={"error": "No results to aggregate"}
            )
        
        # Limit to max_agents results
        if len(results) > self.max_agents:
            self.logger.warning(f"Too many results ({len(results)} > {self.max_agents}), limiting")
            # Sort by confidence and take the top ones
            results = sorted(results, key=lambda r: r.confidence, reverse=True)[:self.max_agents]
        
        # Group results by agent type
        results_by_type: Dict[AgentType, List[AgentResult]] = {}
        for result in results:
            if result.agent_type not in results_by_type:
                results_by_type[result.agent_type] = []
            results_by_type[result.agent_type].append(result)
        
        # Process each group
        aggregated_documents = []
        metadata: Dict[str, object] = {
            "source_agents": [],
            "aggregation_strategy": "weighted_merge",
            "document_count": 0,
            "confidence_scores": {}
        }
        
        # Memory results get highest priority
        if AgentType.MEMORY in results_by_type:
            memory_results = results_by_type[AgentType.MEMORY]
            best_memory_result = max(memory_results, key=lambda r: r.confidence)
            
            if best_memory_result.confidence >= 0.8:
                self.logger.info(f"Using high-confidence memory result: {best_memory_result.confidence:.2f}")
                # Use memory result directly
                aggregated_documents.extend(best_memory_result.documents)
                metadata["source_agents"].append(f"memory:{best_memory_result.agent_id}")
                metadata["aggregation_strategy"] = "memory_prioritized"
                metadata["confidence_scores"]["memory"] = best_memory_result.confidence
        
        # If memory didn't provide high-confidence results, merge other sources
        if not aggregated_documents:
            # Process search results
            if AgentType.SEARCH in results_by_type:
                search_docs, search_confidence = self._aggregate_search_results(
                    results_by_type[AgentType.SEARCH]
                )
                aggregated_documents.extend(search_docs)
                metadata["source_agents"].append("search")
                metadata["confidence_scores"]["search"] = search_confidence
            
            # Process local data results
            if AgentType.LOCAL_DATA in results_by_type:
                local_docs, local_confidence = self._aggregate_local_data_results(
                    results_by_type[AgentType.LOCAL_DATA]
                )
                aggregated_documents.extend(local_docs)
                metadata["source_agents"].append("local_data")
                metadata["confidence_scores"]["local_data"] = local_confidence
            
            # Process cloud results
            if AgentType.CLOUD in results_by_type:
                cloud_docs, cloud_confidence = self._aggregate_cloud_results(
                    results_by_type[AgentType.CLOUD]
                )
                aggregated_documents.extend(cloud_docs)
                metadata["source_agents"].append("cloud")
                metadata["confidence_scores"]["cloud"] = cloud_confidence
        
        # Deduplicate documents
        aggregated_documents = self._deduplicate_documents(aggregated_documents)
        
        # Add metadata and create summary document
        metadata["document_count"] = len(aggregated_documents)
        
        if aggregated_documents:
            summary_doc = self._create_summary_document(query, aggregated_documents)
            aggregated_documents.insert(0, summary_doc)
        
        # Calculate overall confidence
        confidence_scores = metadata["confidence_scores"]
        overall_confidence = (
            sum(confidence_scores.values()) / len(confidence_scores)
            if confidence_scores else 0.0
        )
        
        # Check timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > self.timeout:
            self.logger.warning(f"Aggregation timed out after {elapsed_time:.2f}s")
            metadata["timeout"] = True
        
        return AgentResult(
            agent_id=self.id,
            agent_type=self.agent_type,
            query_id=query.id,
            documents=aggregated_documents,
            confidence=overall_confidence,
            processing_time=elapsed_time,
            metadata=metadata
        )
    
    def _aggregate_search_results(self, results: List[AgentResult]) -> Tuple[List[Document], float]:
        """
        Aggregate search results.
        
        Args:
            results: List of search results to aggregate
            
        Returns:
            Tuple of (aggregated documents, confidence score)
        """
        documents = []
        
        # Collect all documents
        for result in results:
            documents.extend(result.documents)
        
        # Sort by relevance and limit
        documents.sort(key=lambda doc: doc.metadata.get("relevance", 0.0), reverse=True)
        documents = documents[:10]  # Limit to top 10
        
        # Calculate confidence
        confidence = max(result.confidence for result in results) if results else 0.0
        
        return documents, confidence
    
    def _aggregate_local_data_results(self, results: List[AgentResult]) -> Tuple[List[Document], float]:
        """
        Aggregate local data results.
        
        Args:
            results: List of local data results to aggregate
            
        Returns:
            Tuple of (aggregated documents, confidence score)
        """
        documents = []
        
        # Collect all documents
        for result in results:
            documents.extend(result.documents)
        
        # Sort by relevance and limit
        documents.sort(key=lambda doc: doc.metadata.get("relevance", 0.0), reverse=True)
        documents = documents[:10]  # Limit to top 10
        
        # Calculate confidence
        confidence = max(result.confidence for result in results) if results else 0.0
        
        return documents, confidence
    
    def _aggregate_cloud_results(self, results: List[AgentResult]) -> Tuple[List[Document], float]:
        """
        Aggregate cloud results.
        
        Args:
            results: List of cloud results to aggregate
            
        Returns:
            Tuple of (aggregated documents, confidence score)
        """
        documents = []
        
        # Collect all documents
        for result in results:
            documents.extend(result.documents)
        
        # Sort by relevance and limit
        documents.sort(key=lambda doc: doc.metadata.get("relevance", 0.0), reverse=True)
        documents = documents[:10]  # Limit to top 10
        
        # Calculate confidence
        confidence = max(result.confidence for result in results) if results else 0.0
        
        return documents, confidence
    
    def _deduplicate_documents(self, documents: List[Document]) -> List[Document]:
        """
        Deduplicate documents by content.
        
        Args:
            documents: List of documents to deduplicate
            
        Returns:
            Deduplicated list of documents
        """
        seen_content = set()
        deduplicated = []
        
        for doc in documents:
            # Create a content signature (first 100 chars)
            signature = doc.content[:100]
            
            if signature not in seen_content:
                seen_content.add(signature)
                deduplicated.append(doc)
        
        return deduplicated
    
    def _create_summary_document(self, query: Query, documents: List[Document]) -> Document:
        """
        Create a summary document from the aggregated documents.
        
        Args:
            query: The original query
            documents: List of documents to summarize
            
        Returns:
            A summary document
        """
        # In a real implementation, this would use an LLM to create a coherent summary
        # For now, use a simple template
        
        sources = set(doc.source for doc in documents)
        sources_str = ", ".join(list(sources)[:5])
        if len(sources) > 5:
            sources_str += f", and {len(sources) - 5} more"
        
        summary = f"Summary of information for query: '{query.text}'\n\n"
        summary += f"Found {len(documents)} relevant documents from {len(sources)} sources "
        summary += f"({sources_str}).\n\n"
        
        # Add the first sentence from each of the top 3 documents
        for i, doc in enumerate(documents[:3]):
            first_sentence = doc.content.split(".")[0] + "."
            summary += f"Document {i+1}: {first_sentence}\n"
        
        return Document(
            content=summary,
            source="aggregator_summary",
            metadata={
                "is_summary": True,
                "document_count": len(documents),
                "source_count": len(sources)
            }
        )