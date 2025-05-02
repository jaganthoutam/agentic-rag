"""
Long-term memory implementation for Agentic RAG.

This module provides a persistent database storage for long-term memory.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Union

import sqlalchemy
from sqlalchemy import create_engine, Table, Column, String, Float, Integer, DateTime, Text, MetaData
from sqlalchemy.sql import select, delete, update, func
from sqlalchemy.exc import SQLAlchemyError

from core import AgentType, Query, Document, MemoryEntry, AgentResult
from memory.base import BaseMemory


class LongTermMemory(BaseMemory):
    """
    Long-term memory implementation.
    
    This class provides a persistent database storage for long-term memory.
    """
    
    def __init__(self, connection_string: str, table_name: str = "long_term_memory") -> None:
        """
        Initialize the long-term memory.
        
        Args:
            connection_string: Database connection string
            table_name: Base name for memory tables
        """
        super().__init__()
        self.connection_string = connection_string
        self.table_name = table_name
        
        # Connect to database
        try:
            self.engine = create_engine(connection_string)
            self.metadata = MetaData()
            self._create_tables()
            self.connection = self.engine.connect()
            self.logger.info(f"Connected to long-term memory database: {connection_string}")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise RuntimeError(f"Failed to connect to database: {str(e)}")
    
    def _create_tables(self) -> None:
        """Create the necessary database tables if they don't exist."""
        # Memory entries table
        self.memory_table = Table(
            f"{self.table_name}_entries", self.metadata,
            Column("id", String(36), primary_key=True),
            Column("query_id", String(36), index=True),
            Column("created_at", DateTime),
            Column("accessed_at", DateTime),
            Column("access_count", Integer, default=0),
            Column("relevance_score", Float),
            Column("memory_type", String(20)),
            Column("metadata", Text)
        )
        
        # Documents table
        self.document_table = Table(
            f"{self.table_name}_documents", self.metadata,
            Column("id", String(36), primary_key=True),
            Column("content", Text),
            Column("source", String(255)),
            Column("timestamp", DateTime),
            Column("metadata", Text)
        )
        
        # Memory-Document mapping table
        self.memory_document_table = Table(
            f"{self.table_name}_memory_document", self.metadata,
            Column("memory_id", String(36), primary_key=True),
            Column("document_id", String(36), primary_key=True)
        )
        
        # Queries table
        self.query_table = Table(
            f"{self.table_name}_queries", self.metadata,
            Column("id", String(36), primary_key=True),
            Column("text", Text),
            Column("timestamp", DateTime),
            Column("metadata", Text)
        )
        
        # Create tables
        try:
            self.metadata.create_all(self.engine)
            self.logger.debug("Database tables created if they didn't exist")
        except SQLAlchemyError as e:
            self.logger.error(f"Failed to create tables: {str(e)}")
            raise RuntimeError(f"Failed to create tables: {str(e)}")
    
    def retrieve(self, query: Query) -> Optional[AgentResult]:
        """
        Retrieve relevant information from memory based on the query.
        
        Args:
            query: The query to retrieve information for
            
        Returns:
            An AgentResult containing retrieved documents and metadata,
            or None if no relevant information is found
        """
        try:
            # Store the query first
            self._store_query(query)
            
            # Get the most similar queries using simple full-text search
            # This is a simplification - a production system would use 
            # proper vector embeddings and semantic search
            similar_queries = self._find_similar_queries(query.text)
            
            if not similar_queries:
                self.logger.debug(f"No similar queries found for query: {query.id}")
                return None
            
            best_query_id, highest_score = similar_queries[0]
            
            if highest_score < 0.7:
                self.logger.debug(f"No sufficiently similar queries found (best score: {highest_score:.2f})")
                return None
            
            # Find memory entries associated with the best query
            stmt = select(self.memory_table).where(
                self.memory_table.c.query_id == best_query_id
            ).order_by(
                self.memory_table.c.relevance_score.desc()
            )
            
            memory_result = self.connection.execute(stmt).fetchone()
            
            if not memory_result:
                self.logger.debug(f"No memory entries found for query ID: {best_query_id}")
                return None
            
            # Extract memory entry data
            memory_id = memory_result.id
            metadata = json.loads(memory_result.metadata) if memory_result.metadata else {}
            
            # Update access statistics
            self._update_memory_access(memory_id)
            
            # Retrieve associated documents
            documents = self._get_documents_for_memory(memory_id)
            
            if not documents:
                self.logger.debug(f"No documents found for memory ID: {memory_id}")
                return None
            
            return AgentResult(
                agent_id="long_term_memory",
                agent_type=AgentType.MEMORY,
                query_id=query.id,
                documents=documents,
                confidence=highest_score,
                processing_time=0.1,
                metadata={
                    "memory_id": memory_id,
                    "memory_type": "long_term",
                    "original_query_id": best_query_id,
                    "similarity_score": highest_score,
                    "original_metadata": metadata
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error retrieving from long-term memory: {str(e)}")
            return None
    
    def store(self, query: Query, result: AgentResult) -> None:
        """
        Store information in memory.
        
        Args:
            query: The query associated with the information
            result: The result to store
        """
        try:
            # Store the query
            self._store_query(query)
            
            # Store documents
            for document in result.documents:
                self._store_document(document)
            
            # Create memory entry
            memory_entry = MemoryEntry(
                query_id=query.id,
                document_ids=[doc.id for doc in result.documents],
                relevance_score=result.confidence,
                memory_type="long_term",
                metadata={
                    "agent_id": result.agent_id,
                    "agent_type": result.agent_type.value,
                    "original_metadata": result.metadata
                }
            )
            
            # Store memory entry
            stmt = self.memory_table.insert().values(
                id=memory_entry.id,
                query_id=memory_entry.query_id,
                created_at=memory_entry.created_at,
                accessed_at=memory_entry.accessed_at,
                access_count=memory_entry.access_count,
                relevance_score=memory_entry.relevance_score,
                memory_type=memory_entry.memory_type,
                metadata=json.dumps(memory_entry.metadata)
            )
            
            self.connection.execute(stmt)
            
            # Store document associations
            for document_id in memory_entry.document_ids:
                stmt = self.memory_document_table.insert().values(
                    memory_id=memory_entry.id,
                    document_id=document_id
                )
                
                self.connection.execute(stmt)
            
            self.logger.debug(f"Stored memory entry: {memory_entry.id} with {len(memory_entry.document_ids)} documents")
        
        except Exception as e:
            self.logger.error(f"Error storing in long-term memory: {str(e)}")
    
    def update(self, memory_entry: MemoryEntry) -> None:
        """
        Update an existing memory entry.
        
        Args:
            memory_entry: The memory entry to update
        """
        try:
            # Check if the memory entry exists
            stmt = select(self.memory_table).where(self.memory_table.c.id == memory_entry.id)
            result = self.connection.execute(stmt).fetchone()
            
            if not result:
                self.logger.warning(f"Memory entry not found for update: {memory_entry.id}")
                return
            
            # Update memory entry
            stmt = self.memory_table.update().where(
                self.memory_table.c.id == memory_entry.id
            ).values(
                accessed_at=memory_entry.accessed_at,
                access_count=memory_entry.access_count,
                relevance_score=memory_entry.relevance_score,
                metadata=json.dumps(memory_entry.metadata)
            )
            
            self.connection.execute(stmt)
            
            # Update document associations
            # First, remove all existing associations
            stmt = delete(self.memory_document_table).where(
                self.memory_document_table.c.memory_id == memory_entry.id
            )
            
            self.connection.execute(stmt)
            
            # Then, add the new associations
            for document_id in memory_entry.document_ids:
                stmt = self.memory_document_table.insert().values(
                    memory_id=memory_entry.id,
                    document_id=document_id
                )
                
                self.connection.execute(stmt)
            
            self.logger.debug(f"Updated memory entry: {memory_entry.id}")
        
        except Exception as e:
            self.logger.error(f"Error updating memory entry: {str(e)}")
    
    def remove(self, memory_id: str) -> bool:
        """
        Remove a memory entry.
        
        Args:
            memory_id: The ID of the memory entry to remove
            
        Returns:
            True if the entry was removed, False otherwise
        """
        try:
            # Get document IDs associated with the memory entry
            stmt = select(self.memory_document_table.c.document_id).where(
                self.memory_document_table.c.memory_id == memory_id
            )
            
            document_id_rows = self.connection.execute(stmt).fetchall()
            document_ids = [row.document_id for row in document_id_rows]
            
            # Remove document associations
            stmt = delete(self.memory_document_table).where(
                self.memory_document_table.c.memory_id == memory_id
            )
            
            self.connection.execute(stmt)
            
            # Remove memory entry
            stmt = delete(self.memory_table).where(
                self.memory_table.c.id == memory_id
            )
            
            result = self.connection.execute(stmt)
            
            if result.rowcount == 0:
                self.logger.warning(f"Memory entry not found for removal: {memory_id}")
                return False
            
            # Clean up unreferenced documents
            for document_id in document_ids:
                self._cleanup_document(document_id)
            
            self.logger.debug(f"Removed memory entry: {memory_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error removing memory entry: {str(e)}")
            return False
    
    def clear(self) -> None:
        """Clear all memory entries."""
        try:
            # Clear all tables
            self.connection.execute(delete(self.memory_document_table))
            self.connection.execute(delete(self.document_table))
            self.connection.execute(delete(self.memory_table))
            self.connection.execute(delete(self.query_table))
            
            self.logger.info("Long-term memory cleared")
        
        except Exception as e:
            self.logger.error(f"Error clearing long-term memory: {str(e)}")
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get statistics about the memory.
        
        Returns:
            A dictionary of statistics
        """
        try:
            # Get counts
            memory_count = self.connection.execute(
                select(func.count()).select_from(self.memory_table)
            ).scalar() or 0
            
            document_count = self.connection.execute(
                select(func.count()).select_from(self.document_table)
            ).scalar() or 0
            
            query_count = self.connection.execute(
                select(func.count()).select_from(self.query_table)
            ).scalar() or 0
            
            return {
                "memory_entries": memory_count,
                "documents": document_count,
                "queries": query_count
            }
        
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {str(e)}")
            return {
                "memory_entries": 0,
                "documents": 0,
                "queries": 0,
                "error": str(e)
            }
    
    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self, "connection") and self.connection:
            self.connection.close()
            self.logger.info("Long-term memory database connection closed")
    
    def _store_query(self, query: Query) -> None:
        """
        Store a query in the database.
        
        Args:
            query: The query to store
        """
        # Check if the query already exists
        stmt = select(self.query_table).where(self.query_table.c.id == query.id)
        result = self.connection.execute(stmt).fetchone()
        
        if result:
            # Query already exists
            return
        
        # Insert the query
        stmt = self.query_table.insert().values(
            id=query.id,
            text=query.text,
            timestamp=query.timestamp,
            metadata=json.dumps(query.metadata)
        )
        
        self.connection.execute(stmt)
    
    def _store_document(self, document: Document) -> None:
        """
        Store a document in the database.
        
        Args:
            document: The document to store
        """
        # Check if the document already exists
        stmt = select(self.document_table).where(self.document_table.c.id == document.id)
        result = self.connection.execute(stmt).fetchone()
        
        if result:
            # Document already exists
            return
        
        # Insert the document
        stmt = self.document_table.insert().values(
            id=document.id,
            content=document.content,
            source=document.source,
            timestamp=document.timestamp,
            metadata=json.dumps(document.metadata)
        )
        
        self.connection.execute(stmt)
    
    def _update_memory_access(self, memory_id: str) -> None:
        """
        Update the access statistics for a memory entry.
        
        Args:
            memory_id: The ID of the memory entry
        """
        stmt = update(self.memory_table).where(
            self.memory_table.c.id == memory_id
        ).values(
            accessed_at=func.now(),
            access_count=self.memory_table.c.access_count + 1
        )
        
        self.connection.execute(stmt)
    
    def _get_documents_for_memory(self, memory_id: str) -> List[Document]:
        """
        Get the documents associated with a memory entry.
        
        Args:
            memory_id: The ID of the memory entry
            
        Returns:
            A list of documents
        """
        # Get document IDs
        stmt = select(self.memory_document_table.c.document_id).where(
            self.memory_document_table.c.memory_id == memory_id
        )
        
        document_id_rows = self.connection.execute(stmt).fetchall()
        document_ids = [row.document_id for row in document_id_rows]
        
        if not document_ids:
            return []
        
        # Get documents
        stmt = select(self.document_table).where(
            self.document_table.c.id.in_(document_ids)
        )
        
        document_rows = self.connection.execute(stmt).fetchall()
        
        documents = []
        for row in document_rows:
            metadata = json.loads(row.metadata) if row.metadata else {}
            
            document = Document(
                id=row.id,
                content=row.content,
                source=row.source,
                timestamp=row.timestamp,
                metadata=metadata
            )
            
            documents.append(document)
        
        return documents
    
    def _cleanup_document(self, document_id: str) -> None:
        """
        Clean up a document if it's no longer referenced.
        
        Args:
            document_id: The ID of the document to clean up
        """
        # Check if the document is still referenced
        stmt = select(self.memory_document_table).where(
            self.memory_document_table.c.document_id == document_id
        )
        
        result = self.connection.execute(stmt).fetchone()
        
        if not result:
            # Document is no longer referenced, remove it
            stmt = delete(self.document_table).where(
                self.document_table.c.id == document_id
            )
            
            self.connection.execute(stmt)
            self.logger.debug(f"Removed unreferenced document: {document_id}")
    
    def _find_similar_queries(self, query_text: str) -> List[Tuple[str, float]]:
        """
        Find queries similar to the given text.
        
        Args:
            query_text: The query text to match
            
        Returns:
            A list of tuples (query_id, similarity_score) sorted by score
        """
        # In a production system, this would use proper vector embeddings
        # and semantic search. For now, use a simple keyword matching approach.
        query_keywords = set(query_text.lower().split())
        
        # Get all queries
        stmt = select(self.query_table)
        query_rows = self.connection.execute(stmt).fetchall()
        
        similarities = []
        
        for row in query_rows:
            stored_text = row.text
            stored_keywords = set(stored_text.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(query_keywords.intersection(stored_keywords))
            union = len(query_keywords.union(stored_keywords))
            
            if union == 0:
                similarity = 0.0
            else:
                similarity = intersection / union
            
            similarities.append((row.id, similarity))
        
        # Sort by similarity score in descending order
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities