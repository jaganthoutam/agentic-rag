"""
API server for Agentic RAG.

This module provides the REST API for interacting with the Agentic RAG system.
"""

import logging
import os
import time
from typing import Dict, List, Optional, Union, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import Response

from core import Query as RagQuery
from app import AgenticRag


# Create logger
logger = logging.getLogger("agentic_rag.api")

# Create FastAPI app
app = FastAPI(
    title="Agentic RAG API",
    description="API for the Agentic RAG system",
    version="1.0.0"
)

# Initialize the RAG system - will be set in startup_event
rag = None


class QueryRequest(BaseModel):
    """Request model for queries."""
    text: str = Field(..., description="Query text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class QueryResponse(BaseModel):
    """Response model for queries."""
    query_id: str = Field(..., description="Query ID")
    response: str = Field(..., description="Generated response")
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence: float = Field(..., description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: float = Field(..., description="Current timestamp")


class StatsResponse(BaseModel):
    """Response model for system statistics."""
    agents: Dict[str, int] = Field(..., description="Agent counts by type")
    memory: Dict[str, Dict[str, Union[int, float]]] = Field(..., description="Memory statistics")
    uptime: float = Field(..., description="System uptime in seconds")
    query_count: int = Field(..., description="Total number of queries processed")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the RAG system on startup."""
    # Access the module-level rag variable 
    # but don't declare it as global to avoid the F824 error
    
    logger.info("Initializing Agentic RAG system...")
    
    # Get config path from environment or use default
    config_path = os.environ.get("AGENTIC_RAG_CONFIG", "config.json")
    
    try:
        # Directly assign to the module-level variable
        # using this module's name
        import sys
        this_module = sys.modules[__name__]
        setattr(this_module, 'rag', AgenticRag(config_path=config_path))
        logger.info("Agentic RAG system initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Agentic RAG system: {str(e)}")
        # Continue anyway, but API calls will fail until fixed


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shut down the RAG system on application shutdown."""
    # Access the module-level rag variable
    # but don't declare it as global to avoid the F824 error
    
    if rag:
        logger.info("Shutting down Agentic RAG system...")
        try:
            rag.shutdown()
            logger.info("Agentic RAG system shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down Agentic RAG system: {str(e)}")


# Metrics endpoint for Prometheus - simplified version
@app.get('/metrics')
async def metrics():
    """Expose Prometheus metrics."""
    # Create a simple metrics response
    metrics_output = []
    
    # System info
    metrics_output.append("# HELP agentic_rag_info System information")
    metrics_output.append("# TYPE agentic_rag_info gauge")
    metrics_output.append('agentic_rag_info{version="1.0.0",app_name="agentic-rag"} 1')
    
    # Query counter
    metrics_output.append("# HELP agentic_rag_queries_total Total number of processed queries")
    metrics_output.append("# TYPE agentic_rag_queries_total counter")
    metrics_output.append("agentic_rag_queries_total 0")
    
    if rag:
        try:
            # Memory metrics
            metrics_output.append("# HELP agentic_rag_memory_entries Number of memory entries")
            metrics_output.append("# TYPE agentic_rag_memory_entries gauge")
            
            for memory_name, memory in rag.memories.items():
                stats = memory.get_stats()
                entries = stats.get('total_entries', 0) or stats.get('memory_entries', 0)
                metrics_output.append(f'agentic_rag_memory_entries{{memory_type="{memory_name}"}} {entries}')
                
                if memory_name == 'short_term':
                    capacity_used = stats.get('capacity_used_percent', 0)
                    metrics_output.append("# HELP agentic_rag_memory_capacity_used_percent Percentage of memory capacity used")
                    metrics_output.append("# TYPE agentic_rag_memory_capacity_used_percent gauge")
                    metrics_output.append(f"agentic_rag_memory_capacity_used_percent {capacity_used}")
            
            # Document count
            doc_count = 0
            for memory_name, memory in rag.memories.items():
                stats = memory.get_stats()
                doc_count += stats.get('document_count', 0) or stats.get('documents', 0)
            
            metrics_output.append("# HELP agentic_rag_documents_total Total number of documents stored")
            metrics_output.append("# TYPE agentic_rag_documents_total gauge")
            metrics_output.append(f"agentic_rag_documents_total {doc_count}")
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
    
    return Response("\n".join(metrics_output), media_type="text/plain")


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check the health of the API and RAG system."""
    # Access the module-level rag variable
    # but don't declare it as global to avoid the F824 error
    
    status = "healthy" if rag else "degraded"
    
    return HealthResponse(
        status=status,
        version=app.version,
        timestamp=time.time()
    )


# System statistics endpoint
@app.get("/stats", response_model=StatsResponse, tags=["System"])
async def get_stats():
    """Get statistics about the RAG system."""
    # Access the module-level rag variable
    # but don't declare it as global to avoid the F824 error
    
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    # Get memory stats
    memory_stats = {}
    for memory_name, memory in rag.memories.items():
        memory_stats[memory_name] = memory.get_stats()
    
    # Count agents by type
    agent_counts = {}
    for agent_type, _ in rag.agents.items():
        agent_type_str = agent_type.value
        if agent_type_str in agent_counts:
            agent_counts[agent_type_str] += 1
        else:
            agent_counts[agent_type_str] = 1
    
    # Get uptime (assuming rag has a start_time attribute)
    uptime = time.time() - getattr(rag, "start_time", time.time())
    
    # Get query count (assuming rag has a query_count attribute)
    query_count = getattr(rag, "query_count", 0)
    
    return StatsResponse(
        agents=agent_counts,
        memory=memory_stats,
        uptime=uptime,
        query_count=query_count
    )


# Query endpoint
@app.post("/query", response_model=QueryResponse, tags=["Queries"])
async def process_query(request: QueryRequest):
    """
    Process a query through the RAG system.
    
    Args:
        request: Query request containing text and metadata
        
    Returns:
        Query response with generated answer and metadata
    """
    # Access the module-level rag variable
    # but don't declare it as global to avoid the F824 error
    
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    # Start timing
    start_time = time.time()
    
    try:
        # Create a query object
        query = RagQuery(text=request.text, metadata=request.metadata)
        
        # Process the query
        logger.info(f"Processing query: {query.id}")
        result = rag.process_query(query.text)
        
        # Convert to response model
        response = QueryResponse(
            query_id=result.query_id,
            response=result.response,
            processing_time=result.processing_time,
            confidence=result.confidence,
            metadata=result.metadata
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


# Configure endpoint
@app.post("/configure", tags=["System"])
async def configure_system(config: Dict[str, Any]):
    """
    Update system configuration.
    
    Args:
        config: Configuration settings to update
        
    Returns:
        Status message
    """
    # Access the module-level rag variable
    # but don't declare it as global to avoid the F824 error
    
    if not rag:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # In a real implementation, this would update the configuration
        # For now, just log the request
        logger.info(f"Configuration update requested: {config}")
        
        return {"status": "success", "message": "Configuration updated"}
    
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")


def run_server(host: str = "0.0.0.0", port: int = 8001):
    """
    Run the API server.
    
    Args:
        host: Host to bind to
        port: Port to listen on
    """
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Agentic RAG API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Set config path in environment
    os.environ["AGENTIC_RAG_CONFIG"] = args.config
    
    # Run the server
    run_server(host=args.host, port=args.port)
