-- Database schema for Agentic RAG system
-- This schema defines the tables used by the long-term memory component

-- Create memory entries table
CREATE TABLE IF NOT EXISTS long_term_memory_entries (
    id VARCHAR(36) PRIMARY KEY,
    query_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER NOT NULL DEFAULT 0,
    relevance_score FLOAT NOT NULL DEFAULT 0.0,
    memory_type VARCHAR(20) NOT NULL,
    metadata JSONB,
    
    INDEX idx_memory_query_id (query_id),
    INDEX idx_memory_relevance (relevance_score DESC),
    INDEX idx_memory_accessed_at (accessed_at DESC)
);

-- Create documents table
CREATE TABLE IF NOT EXISTS long_term_memory_documents (
    id VARCHAR(36) PRIMARY KEY,
    content TEXT NOT NULL,
    source VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    INDEX idx_document_source (source),
    INDEX idx_document_timestamp (timestamp DESC)
);

-- Create memory-document mapping table
CREATE TABLE IF NOT EXISTS long_term_memory_memory_document (
    memory_id VARCHAR(36) NOT NULL,
    document_id VARCHAR(36) NOT NULL,
    
    PRIMARY KEY (memory_id, document_id),
    FOREIGN KEY (memory_id) REFERENCES long_term_memory_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (document_id) REFERENCES long_term_memory_documents(id) ON DELETE CASCADE
);

-- Create queries table
CREATE TABLE IF NOT EXISTS long_term_memory_queries (
    id VARCHAR(36) PRIMARY KEY,
    text TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    INDEX idx_query_timestamp (timestamp DESC)
);

-- Create embeddings table for vector search
CREATE TABLE IF NOT EXISTS long_term_memory_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    entity_id VARCHAR(36) NOT NULL,
    entity_type VARCHAR(20) NOT NULL, -- 'query', 'document', or 'memory'
    embedding VECTOR(1536), -- Assuming 1536-dimensional embeddings (e.g., for OpenAI models)
    
    INDEX idx_embedding_entity (entity_id, entity_type),
    INDEX idx_embedding_vector (embedding) USING ivfflat -- Vector index for similarity search
);

-- Create analytics table for query patterns
CREATE TABLE IF NOT EXISTS long_term_memory_analytics (
    id VARCHAR(36) PRIMARY KEY,
    query_pattern VARCHAR(255) NOT NULL,
    frequency INTEGER NOT NULL DEFAULT 1,
    last_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_analytics_pattern (query_pattern),
    INDEX idx_analytics_frequency (frequency DESC)
);

-- Create table for tracking system performance
CREATE TABLE IF NOT EXISTS long_term_memory_performance (
    id VARCHAR(36) PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL, -- 'store', 'retrieve', 'update', etc.
    duration_ms INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    INDEX idx_performance_operation (operation_type),
    INDEX idx_performance_timestamp (timestamp DESC)
);

-- Create maintenance table for cleanup operations
CREATE TABLE IF NOT EXISTS long_term_memory_maintenance (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50) NOT NULL, -- 'cleanup', 'optimization', etc.
    entities_affected INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed'
    error_message TEXT,
    
    INDEX idx_maintenance_status (status),
    INDEX idx_maintenance_started (started_at DESC)
);