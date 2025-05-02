"""
Local data agent implementation for Agentic RAG.

This module implements an agent that retrieves information from local data sources.
"""

import json
import os
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any

from core import AgentType, Query, Document, AgentResult
from agents.base import BaseAgent


class LocalDataAgent(BaseAgent):
    """
    Local data agent implementation.
    
    This agent retrieves information from local data sources.
    """
    
    def __init__(self, data_path: str = "./data", formats: List[str] = None) -> None:
        """
        Initialize the local data agent.
        
        Args:
            data_path: Path to the local data directory
            formats: List of supported file formats (default: ["csv", "json", "pdf"])
        """
        super().__init__(agent_type=AgentType.LOCAL_DATA)
        self.data_path = data_path
        self.formats = formats or ["csv", "json", "pdf"]
        self.logger.info(f"Local data agent initialized with data_path={data_path}, formats={self.formats}")
        
        # Initialize file index
        self.file_index = {}
        self.last_indexed = 0
        self._build_file_index()
    
    @BaseAgent.measure_execution_time
    def process(self, query: Query) -> AgentResult:
        """
        Process the query by retrieving relevant information from local data.
        
        Args:
            query: The query to process
            
        Returns:
            An AgentResult containing the retrieved information
        """
        self.logger.debug(f"Processing query: {query.id}")
        
        try:
            # Update file index if necessary
            self._update_file_index()
            
            # Find relevant files
            relevant_files = self._find_relevant_files(query.text)
            
            if not relevant_files:
                self.logger.info(f"No relevant files found for query: {query.text}")
                return AgentResult(
                    agent_id=self.id,
                    agent_type=self.agent_type,
                    query_id=query.id,
                    documents=[],
                    confidence=0.0,
                    processing_time=0.0,  # Will be set by decorator
                    metadata={
                        "file_count": 0,
                        "formats_searched": self.formats,
                        "data_path": self.data_path
                    }
                )
            
            # Process relevant files and extract information
            documents = []
            relevance_scores = []
            
            for file_path, relevance in relevant_files:
                file_docs = self._process_file(file_path, query.text)
                
                if file_docs:
                    documents.extend(file_docs)
                    relevance_scores.extend([relevance] * len(file_docs))
            
            # Calculate overall confidence
            if relevance_scores:
                confidence = sum(relevance_scores) / len(relevance_scores)
            else:
                confidence = 0.0
            
            self.logger.info(f"Found {len(documents)} relevant documents with average confidence: {confidence:.2f}")
            
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=documents,
                confidence=confidence,
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "file_count": len(relevant_files),
                    "document_count": len(documents),
                    "formats_found": list(set(os.path.splitext(path)[1][1:] for path, _ in relevant_files)),
                    "data_path": self.data_path
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error processing local data: {str(e)}")
            
            return AgentResult(
                agent_id=self.id,
                agent_type=self.agent_type,
                query_id=query.id,
                documents=[],
                confidence=0.0,
                processing_time=0.0,  # Will be set by decorator
                metadata={
                    "error": str(e),
                    "data_path": self.data_path
                }
            )
    
    def _build_file_index(self) -> None:
        """Build an index of local files."""
        if not os.path.exists(self.data_path):
            self.logger.warning(f"Data path does not exist: {self.data_path}")
            return
        
        self.file_index = {}
        count = 0
        
        for root, _, files in os.walk(self.data_path):
            for file in files:
                file_ext = os.path.splitext(file)[1][1:].lower()
                
                if file_ext in self.formats:
                    file_path = os.path.join(root, file)
                    
                    # Get file metadata
                    try:
                        file_stat = os.stat(file_path)
                        size = file_stat.st_size
                        mtime = file_stat.st_mtime
                        
                        self.file_index[file_path] = {
                            "size": size,
                            "mtime": mtime,
                            "format": file_ext,
                            "name": file,
                            "keywords": set(file.lower().replace(".", " ").replace("_", " ").replace("-", " ").split())
                        }
                        
                        count += 1
                    except OSError as e:
                        self.logger.warning(f"Error accessing file {file_path}: {str(e)}")
        
        self.last_indexed = time.time()
        self.logger.info(f"Built file index with {count} files")
    
    def _update_file_index(self) -> None:
        """Update the file index if necessary."""
        # Check if it's been more than 5 minutes since the last indexing
        if time.time() - self.last_indexed > 300:
            self._build_file_index()
    
    def _find_relevant_files(self, query_text: str) -> List[Tuple[str, float]]:
        """
        Find files relevant to the query.
        
        Args:
            query_text: The query text
            
        Returns:
            List of tuples (file_path, relevance_score)
        """
        query_keywords = set(query_text.lower().split())
        relevant_files = []
        
        for file_path, meta in self.file_index.items():
            # Calculate relevance based on keyword overlap
            file_keywords = meta["keywords"]
            common_keywords = query_keywords.intersection(file_keywords)
            
            if common_keywords:
                # Calculate Jaccard similarity
                similarity = len(common_keywords) / len(query_keywords.union(file_keywords))
                
                if similarity >= 0.1:  # Threshold to exclude very low relevance
                    relevant_files.append((file_path, similarity))
        
        # Sort by relevance in descending order
        relevant_files.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to top 5
        return relevant_files[:5]
    
    def _process_file(self, file_path: str, query_text: str) -> List[Document]:
        """
        Process a file and extract relevant information.
        
        Args:
            file_path: Path to the file
            query_text: The query text
            
        Returns:
            List of Document objects containing extracted information
        """
        file_format = os.path.splitext(file_path)[1][1:].lower()
        
        try:
            if file_format == "json":
                return self._process_json_file(file_path, query_text)
            elif file_format == "csv":
                return self._process_csv_file(file_path, query_text)
            elif file_format == "pdf":
                return self._process_pdf_file(file_path, query_text)
            else:
                self.logger.warning(f"Unsupported file format: {file_format}")
                return []
        
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            return []
    
    def _process_json_file(self, file_path: str, query_text: str) -> List[Document]:
        """
        Process a JSON file.
        
        Args:
            file_path: Path to the file
            query_text: The query text
            
        Returns:
            List of Document objects
        """
        self.logger.debug(f"Processing JSON file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # In a real implementation, we would analyze the JSON structure
            # and extract relevant sections based on the query
            # For now, just return the whole file as a document
            
            # Convert to string representation
            if isinstance(data, list):
                # For arrays, limit to 10 items
                if len(data) > 10:
                    content = json.dumps(data[:10], indent=2) + f"\n\n... (and {len(data) - 10} more items)"
                else:
                    content = json.dumps(data, indent=2)
            else:
                # For objects, include all
                content = json.dumps(data, indent=2)
            
            document = Document(
                content=content,
                source=file_path,
                metadata={
                    "file_type": "json",
                    "file_name": os.path.basename(file_path),
                    "file_size": os.path.getsize(file_path),
                    "relevance": 0.8  # Placeholder
                }
            )
            
            return [document]
        
        except Exception as e:
            self.logger.error(f"Error processing JSON file {file_path}: {str(e)}")
            return []
    
    def _process_csv_file(self, file_path: str, query_text: str) -> List[Document]:
        """
        Process a CSV file.
        
        Args:
            file_path: Path to the file
            query_text: The query text
            
        Returns:
            List of Document objects
        """
        self.logger.debug(f"Processing CSV file: {file_path}")
        
        try:
            # In a real implementation, we would use pandas to read and analyze the CSV
            # For now, just read the first few lines
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()[:10]]
            
            if len(lines) > 0:
                # First line is usually the header
                header = lines[0]
                
                # Create document content
                content = f"CSV File: {os.path.basename(file_path)}\n\n"
                content += f"Header: {header}\n\n"
                
                if len(lines) > 1:
                    content += "Sample data:\n"
                    for i, line in enumerate(lines[1:]):
                        content += f"{i+1}. {line}\n"
                
                if len(lines) == 10:
                    content += "\n(showing first 9 data rows)"
                
                document = Document(
                    content=content,
                    source=file_path,
                    metadata={
                        "file_type": "csv",
                        "file_name": os.path.basename(file_path),
                        "file_size": os.path.getsize(file_path),
                        "header": header,
                        "relevance": 0.8  # Placeholder
                    }
                )
                
                return [document]
            
            return []
        
        except Exception as e:
            self.logger.error(f"Error processing CSV file {file_path}: {str(e)}")
            return []
    
    def _process_pdf_file(self, file_path: str, query_text: str) -> List[Document]:
        """
        Process a PDF file.
        
        Args:
            file_path: Path to the file
            query_text: The query text
            
        Returns:
            List of Document objects
        """
        self.logger.debug(f"Processing PDF file: {file_path}")
        
        try:
            # In a real implementation, we would use a PDF parsing library
            # For now, just create a placeholder document
            
            document = Document(
                content=f"PDF File: {os.path.basename(file_path)}\n\n"
                        f"This is a placeholder for PDF content. In a real implementation, "
                        f"we would extract text from the PDF and analyze it.",
                source=file_path,
                metadata={
                    "file_type": "pdf",
                    "file_name": os.path.basename(file_path),
                    "file_size": os.path.getsize(file_path),
                    "relevance": 0.7  # Placeholder
                }
            )
            
            return [document]
        
        except Exception as e:
            self.logger.error(f"Error processing PDF file {file_path}: {str(e)}")
            return []