-- ATLAS Memory Database Initialization Script
-- Database: atlas_memory
-- Purpose: Long-term memory and knowledge management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB GIN indexing
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Enable full-text search extensions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Memory chunks for retrieval (also stored in ChromaDB)
CREATE TABLE IF NOT EXISTS memory_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'task', 'document', 'conversation', 'agent_memory'
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_size INTEGER NOT NULL,
    embedding_id VARCHAR(255), -- Reference to ChromaDB
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_source_type CHECK (source_type IN ('task', 'document', 'conversation', 'agent_memory')),
    CONSTRAINT positive_chunk_index CHECK (chunk_index >= 0),
    CONSTRAINT positive_chunk_size CHECK (chunk_size > 0),
    CONSTRAINT non_empty_text CHECK (length(trim(chunk_text)) > 0)
);

-- Knowledge entities extracted from content
CREATE TABLE IF NOT EXISTS knowledge_entities (
    entity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(100) NOT NULL, -- 'person', 'organization', 'concept', 'tool', 'technology'
    entity_name VARCHAR(255) NOT NULL,
    description TEXT,
    properties JSONB DEFAULT '{}'::jsonb,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confidence_score DECIMAL(3, 2) DEFAULT 1.0,
    source_count INTEGER DEFAULT 1,
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT positive_source_count CHECK (source_count > 0),
    CONSTRAINT unique_entity_name_type UNIQUE (entity_name, entity_type)
);

-- Document metadata for source tracking
CREATE TABLE IF NOT EXISTS document_metadata (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(50),
    source_url TEXT,
    project_name VARCHAR(255),
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    file_size_bytes BIGINT,
    checksum VARCHAR(64),
    processing_status VARCHAR(50) DEFAULT 'pending',
    extracted_metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_processing_status CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    CONSTRAINT positive_file_size CHECK (file_size_bytes >= 0)
);

-- Task summaries for analytics (future feature)
CREATE TABLE IF NOT EXISTS task_summaries (
    summary_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    summary_type VARCHAR(50) NOT NULL, -- 'executive', 'technical', 'detailed'
    summary_text TEXT NOT NULL,
    key_findings JSONB DEFAULT '[]'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    generated_by_model VARCHAR(100),
    quality_score DECIMAL(3, 2),
    -- Foreign key constraint references other database (will be managed at application level)
    -- CONSTRAINT fk_summary_task FOREIGN KEY (task_id) REFERENCES atlas_main.tasks(task_id)
    CONSTRAINT valid_summary_type CHECK (summary_type IN ('executive', 'technical', 'detailed', 'quick')),
    CONSTRAINT valid_quality_score CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)),
    CONSTRAINT non_empty_summary CHECK (length(trim(summary_text)) > 0)
);

-- Knowledge relationships and connections
CREATE TABLE IF NOT EXISTS knowledge_relationships (
    relationship_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_1_id UUID NOT NULL REFERENCES knowledge_entities(entity_id) ON DELETE CASCADE,
    entity_2_id UUID NOT NULL REFERENCES knowledge_entities(entity_id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    strength DECIMAL(3, 2) DEFAULT 0.5, -- Relationship strength 0.0 to 1.0
    evidence TEXT, -- Supporting evidence for the relationship
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_confirmed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT different_entities CHECK (entity_1_id != entity_2_id),
    CONSTRAINT valid_strength CHECK (strength >= 0 AND strength <= 1),
    CONSTRAINT unique_entity_relationship UNIQUE (entity_1_id, entity_2_id, relationship_type)
);

-- Semantic search cache for performance
CREATE TABLE IF NOT EXISTS semantic_search_cache (
    cache_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    query_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash of normalized query
    results JSONB NOT NULL,
    search_type VARCHAR(50) NOT NULL, -- 'memory', 'knowledge', 'document'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    CONSTRAINT valid_search_type CHECK (search_type IN ('memory', 'knowledge', 'document', 'mixed')),
    CONSTRAINT positive_access_count CHECK (access_count > 0)
);

-- Indexes for query optimization
CREATE INDEX IF NOT EXISTS idx_memory_chunks_source ON memory_chunks(source_id, source_type);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_created ON memory_chunks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_embedding ON memory_chunks(embedding_id) WHERE embedding_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_knowledge_entities_type_name ON knowledge_entities(entity_type, entity_name);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_updated ON knowledge_entities(last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_confidence ON knowledge_entities(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_name_trgm ON knowledge_entities USING gin (entity_name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_document_metadata_name ON document_metadata(document_name);
CREATE INDEX IF NOT EXISTS idx_document_metadata_project ON document_metadata(project_name);
CREATE INDEX IF NOT EXISTS idx_document_metadata_status ON document_metadata(processing_status);
CREATE INDEX IF NOT EXISTS idx_document_metadata_upload ON document_metadata(upload_date DESC);

CREATE INDEX IF NOT EXISTS idx_task_summaries_task ON task_summaries(task_id);
CREATE INDEX IF NOT EXISTS idx_task_summaries_type ON task_summaries(summary_type);
CREATE INDEX IF NOT EXISTS idx_task_summaries_generated ON task_summaries(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_task_summaries_quality ON task_summaries(quality_score DESC) WHERE quality_score IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_entity1 ON knowledge_relationships(entity_1_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_entity2 ON knowledge_relationships(entity_2_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_type ON knowledge_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_strength ON knowledge_relationships(strength DESC);

CREATE INDEX IF NOT EXISTS idx_semantic_cache_hash ON semantic_search_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_semantic_cache_type ON semantic_search_cache(search_type);
CREATE INDEX IF NOT EXISTS idx_semantic_cache_accessed ON semantic_search_cache(last_accessed DESC);

-- GIN indexes for JSONB columns and full-text search
CREATE INDEX IF NOT EXISTS idx_memory_chunks_metadata_gin ON memory_chunks USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_text_gin ON memory_chunks USING gin (to_tsvector('english', chunk_text));

CREATE INDEX IF NOT EXISTS idx_knowledge_entities_properties_gin ON knowledge_entities USING GIN (properties);
CREATE INDEX IF NOT EXISTS idx_knowledge_entities_desc_gin ON knowledge_entities USING gin (to_tsvector('english', description)) WHERE description IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_document_metadata_gin ON document_metadata USING GIN (extracted_metadata);

CREATE INDEX IF NOT EXISTS idx_task_summaries_findings_gin ON task_summaries USING GIN (key_findings);
CREATE INDEX IF NOT EXISTS idx_task_summaries_recommendations_gin ON task_summaries USING GIN (recommendations);
CREATE INDEX IF NOT EXISTS idx_task_summaries_text_gin ON task_summaries USING gin (to_tsvector('english', summary_text));

CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_metadata_gin ON knowledge_relationships USING GIN (metadata);

-- Comments for documentation
COMMENT ON TABLE memory_chunks IS 'Text chunks for retrieval (hybrid storage with ChromaDB)';
COMMENT ON TABLE knowledge_entities IS 'Extracted entities and concepts from processed content';
COMMENT ON TABLE document_metadata IS 'Source document tracking and processing status';
COMMENT ON TABLE task_summaries IS 'LLM-generated task summaries (future feature)';
COMMENT ON TABLE knowledge_relationships IS 'Relationships and connections between knowledge entities';
COMMENT ON TABLE semantic_search_cache IS 'Cache for semantic search results to improve performance';

COMMENT ON COLUMN memory_chunks.embedding_id IS 'Reference to corresponding ChromaDB embedding';
COMMENT ON COLUMN memory_chunks.chunk_text IS 'Text content (also embedded in ChromaDB for semantic search)';
COMMENT ON COLUMN knowledge_entities.confidence_score IS 'Confidence in entity extraction accuracy (0.0 to 1.0)';
COMMENT ON COLUMN knowledge_relationships.strength IS 'Relationship strength score (0.0 to 1.0)';
COMMENT ON COLUMN semantic_search_cache.query_hash IS 'SHA-256 hash of normalized query for efficient lookup';

-- Create views for common queries

-- Knowledge entity summary
CREATE OR REPLACE VIEW knowledge_entity_summary AS
SELECT 
    entity_type,
    COUNT(*) as entity_count,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    ROUND(AVG(source_count), 1) as avg_source_count,
    MAX(last_updated) as most_recent_update,
    COUNT(CASE WHEN confidence_score >= 0.8 THEN 1 END) as high_confidence_count
FROM knowledge_entities
GROUP BY entity_type
ORDER BY entity_count DESC;

-- Document processing status
CREATE OR REPLACE VIEW document_processing_status AS
SELECT 
    processing_status,
    COUNT(*) as document_count,
    ROUND(AVG(file_size_bytes / 1024.0 / 1024.0), 2) as avg_size_mb,
    MIN(upload_date) as oldest_upload,
    MAX(upload_date) as newest_upload
FROM document_metadata
GROUP BY processing_status
ORDER BY document_count DESC;

-- Memory chunk statistics
CREATE OR REPLACE VIEW memory_chunk_statistics AS
SELECT 
    source_type,
    COUNT(*) as chunk_count,
    ROUND(AVG(chunk_size), 0) as avg_chunk_size,
    SUM(chunk_size) as total_text_size,
    COUNT(CASE WHEN embedding_id IS NOT NULL THEN 1 END) as embedded_count,
    MAX(created_at) as most_recent_chunk
FROM memory_chunks
GROUP BY source_type
ORDER BY chunk_count DESC;

COMMENT ON VIEW knowledge_entity_summary IS 'Summary statistics for knowledge entities by type';
COMMENT ON VIEW document_processing_status IS 'Document processing pipeline status overview';
COMMENT ON VIEW memory_chunk_statistics IS 'Memory chunk storage and embedding statistics';

-- Create functions for common operations

-- Function to create memory chunk with automatic embedding ID
CREATE OR REPLACE FUNCTION create_memory_chunk(
    p_source_id UUID,
    p_source_type VARCHAR(50),
    p_chunk_text TEXT,
    p_chunk_index INTEGER,
    p_metadata JSONB DEFAULT '{}'::jsonb
) RETURNS UUID AS $$
DECLARE
    v_chunk_id UUID;
    v_chunk_size INTEGER;
BEGIN
    v_chunk_size := length(p_chunk_text);
    
    INSERT INTO memory_chunks (
        source_id, source_type, chunk_text, chunk_index, chunk_size, metadata
    )
    VALUES (
        p_source_id, p_source_type, p_chunk_text, p_chunk_index, v_chunk_size, p_metadata
    )
    RETURNING chunk_id INTO v_chunk_id;
    
    RETURN v_chunk_id;
END;
$$ LANGUAGE plpgsql;

-- Function to upsert knowledge entity
CREATE OR REPLACE FUNCTION upsert_knowledge_entity(
    p_entity_type VARCHAR(100),
    p_entity_name VARCHAR(255),
    p_description TEXT DEFAULT NULL,
    p_properties JSONB DEFAULT '{}'::jsonb,
    p_confidence_score DECIMAL(3,2) DEFAULT 1.0
) RETURNS UUID AS $$
DECLARE
    v_entity_id UUID;
BEGIN
    INSERT INTO knowledge_entities (
        entity_type, entity_name, description, properties, confidence_score
    )
    VALUES (
        p_entity_type, p_entity_name, p_description, p_properties, p_confidence_score
    )
    ON CONFLICT (entity_name, entity_type)
    DO UPDATE SET
        description = COALESCE(p_description, knowledge_entities.description),
        properties = p_properties,
        last_updated = CURRENT_TIMESTAMP,
        confidence_score = GREATEST(knowledge_entities.confidence_score, p_confidence_score),
        source_count = knowledge_entities.source_count + 1
    RETURNING entity_id INTO v_entity_id;
    
    RETURN v_entity_id;
END;
$$ LANGUAGE plpgsql;

-- Function to create knowledge relationship
CREATE OR REPLACE FUNCTION create_knowledge_relationship(
    p_entity_1_id UUID,
    p_entity_2_id UUID,
    p_relationship_type VARCHAR(100),
    p_strength DECIMAL(3,2) DEFAULT 0.5,
    p_evidence TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_relationship_id UUID;
BEGIN
    INSERT INTO knowledge_relationships (
        entity_1_id, entity_2_id, relationship_type, strength, evidence
    )
    VALUES (
        p_entity_1_id, p_entity_2_id, p_relationship_type, p_strength, p_evidence
    )
    ON CONFLICT (entity_1_id, entity_2_id, relationship_type)
    DO UPDATE SET
        strength = GREATEST(knowledge_relationships.strength, p_strength),
        evidence = COALESCE(p_evidence, knowledge_relationships.evidence),
        last_confirmed = CURRENT_TIMESTAMP
    RETURNING relationship_id INTO v_relationship_id;
    
    RETURN v_relationship_id;
END;
$$ LANGUAGE plpgsql;

-- Function to search memory chunks by text
CREATE OR REPLACE FUNCTION search_memory_chunks(
    p_search_text TEXT,
    p_source_type VARCHAR(50) DEFAULT NULL,
    p_limit INTEGER DEFAULT 20
) RETURNS TABLE (
    chunk_id UUID,
    chunk_text TEXT,
    source_type VARCHAR(50),
    relevance_score REAL,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mc.chunk_id,
        mc.chunk_text,
        mc.source_type,
        ts_rank(to_tsvector('english', mc.chunk_text), plainto_tsquery('english', p_search_text)) as relevance_score,
        mc.created_at
    FROM memory_chunks mc
    WHERE to_tsvector('english', mc.chunk_text) @@ plainto_tsquery('english', p_search_text)
      AND (p_source_type IS NULL OR mc.source_type = p_source_type)
    ORDER BY relevance_score DESC, mc.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to cache semantic search results
CREATE OR REPLACE FUNCTION cache_semantic_search(
    p_query_text TEXT,
    p_search_type VARCHAR(50),
    p_results JSONB
) RETURNS UUID AS $$
DECLARE
    v_cache_id UUID;
    v_query_hash VARCHAR(64);
BEGIN
    -- Create hash of normalized query
    v_query_hash := encode(sha256(lower(trim(p_query_text))::bytea), 'hex');
    
    INSERT INTO semantic_search_cache (
        query_text, query_hash, results, search_type
    )
    VALUES (
        p_query_text, v_query_hash, p_results, p_search_type
    )
    ON CONFLICT (query_hash)
    DO UPDATE SET
        results = p_results,
        last_accessed = CURRENT_TIMESTAMP,
        access_count = semantic_search_cache.access_count + 1
    RETURNING cache_id INTO v_cache_id;
    
    RETURN v_cache_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_memory_chunk IS 'Create memory chunk with automatic size calculation';
COMMENT ON FUNCTION upsert_knowledge_entity IS 'Insert or update knowledge entity with confidence merging';
COMMENT ON FUNCTION create_knowledge_relationship IS 'Create or update relationship between knowledge entities';
COMMENT ON FUNCTION search_memory_chunks IS 'Full-text search across memory chunks with relevance scoring';
COMMENT ON FUNCTION cache_semantic_search IS 'Cache semantic search results for performance optimization';

-- Create cleanup function for old cache entries
CREATE OR REPLACE FUNCTION cleanup_semantic_cache(
    p_max_age_days INTEGER DEFAULT 7,
    p_min_access_count INTEGER DEFAULT 2
) RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM semantic_search_cache
    WHERE (
        last_accessed < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_max_age_days
        AND access_count < p_min_access_count
    );
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_semantic_cache IS 'Clean up old semantic search cache entries';

-- Success message
DO $$ 
BEGIN 
    RAISE NOTICE 'ATLAS Memory database initialized successfully!';
    RAISE NOTICE 'Tables created: memory_chunks, knowledge_entities, document_metadata, task_summaries, knowledge_relationships, semantic_search_cache';
    RAISE NOTICE 'Views created: knowledge_entity_summary, document_processing_status, memory_chunk_statistics';
    RAISE NOTICE 'Functions created: create_memory_chunk(), upsert_knowledge_entity(), create_knowledge_relationship(), search_memory_chunks(), cache_semantic_search(), cleanup_semantic_cache()';
    RAISE NOTICE 'Full-text search and semantic caching capabilities enabled';
END $$;