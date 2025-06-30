-- ATLAS Agents Database Initialization Script
-- Database: atlas_agents
-- Purpose: Agent-specific operational data with foreign key relationships

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB GIN indexing
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Agent sessions table
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL,
    task_id UUID NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    state JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT true,
    total_messages INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    -- Foreign key constraints reference other databases (will be managed at application level)
    -- CONSTRAINT fk_agent FOREIGN KEY (agent_id) REFERENCES atlas_main.agents(agent_id),
    -- CONSTRAINT fk_task FOREIGN KEY (task_id) REFERENCES atlas_main.tasks(task_id)
    CONSTRAINT positive_messages CHECK (total_messages >= 0),
    CONSTRAINT positive_tokens CHECK (total_tokens >= 0),
    CONSTRAINT positive_cost CHECK (total_cost >= 0)
);

-- Agent memory table - Conversation history (stored in both PostgreSQL and ChromaDB)
CREATE TABLE IF NOT EXISTS agent_memory (
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER DEFAULT 0,
    model_name VARCHAR(100),
    embedding_id VARCHAR(255), -- Reference to ChromaDB
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_role CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    CONSTRAINT positive_tokens_used CHECK (tokens_used >= 0),
    CONSTRAINT positive_sequence CHECK (sequence_number > 0),
    CONSTRAINT unique_session_sequence UNIQUE (session_id, sequence_number)
);

-- Agent tools usage tracking
CREATE TABLE IF NOT EXISTS agent_tools (
    tool_usage_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    tool_category VARCHAR(50),
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_execution_time CHECK (execution_time_ms >= 0)
);

-- Agent performance metrics
CREATE TABLE IF NOT EXISTS agent_performance (
    performance_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL,
    task_id UUID NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10, 4),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    time_period VARCHAR(50), -- 'hourly', 'daily', 'weekly'
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Foreign key constraints reference other databases (will be managed at application level)
    -- CONSTRAINT fk_perf_agent FOREIGN KEY (agent_id) REFERENCES atlas_main.agents(agent_id),
    -- CONSTRAINT fk_perf_task FOREIGN KEY (task_id) REFERENCES atlas_main.tasks(task_id)
    CONSTRAINT valid_time_period CHECK (time_period IN ('hourly', 'daily', 'weekly', 'monthly'))
);

-- Agent collaborations tracking
CREATE TABLE IF NOT EXISTS agent_collaborations (
    collaboration_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    agent_1_id UUID NOT NULL,
    agent_2_id UUID NOT NULL,
    collaboration_type VARCHAR(100),
    success_score DECIMAL(3, 2),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    -- Foreign key constraints reference other databases (will be managed at application level)
    -- CONSTRAINT fk_collab_task FOREIGN KEY (task_id) REFERENCES atlas_main.tasks(task_id),
    -- CONSTRAINT fk_collab_agent1 FOREIGN KEY (agent_1_id) REFERENCES atlas_main.agents(agent_id),
    -- CONSTRAINT fk_collab_agent2 FOREIGN KEY (agent_2_id) REFERENCES atlas_main.agents(agent_id)
    CONSTRAINT valid_success_score CHECK (success_score >= 0 AND success_score <= 1),
    CONSTRAINT different_agents CHECK (agent_1_id != agent_2_id)
);

-- Agent state snapshots for checkpointing
CREATE TABLE IF NOT EXISTS agent_state_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES agent_sessions(session_id) ON DELETE CASCADE,
    snapshot_type VARCHAR(50) NOT NULL, -- 'checkpoint', 'error_recovery', 'manual'
    agent_state JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    CONSTRAINT valid_snapshot_type CHECK (snapshot_type IN ('checkpoint', 'error_recovery', 'manual', 'completion'))
);

-- Indexes for query optimization
CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_task ON agent_sessions(agent_id, task_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_active ON agent_sessions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_agent_sessions_started ON agent_sessions(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_memory_session ON agent_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_timestamp ON agent_memory(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_agent_memory_role ON agent_memory(role);
CREATE INDEX IF NOT EXISTS idx_agent_memory_model ON agent_memory(model_name);

CREATE INDEX IF NOT EXISTS idx_agent_tools_session ON agent_tools(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_tools_name ON agent_tools(tool_name);
CREATE INDEX IF NOT EXISTS idx_agent_tools_category ON agent_tools(tool_category);
CREATE INDEX IF NOT EXISTS idx_agent_tools_success ON agent_tools(success);
CREATE INDEX IF NOT EXISTS idx_agent_tools_timestamp ON agent_tools(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_agent_performance_agent_metric ON agent_performance(agent_id, metric_type);
CREATE INDEX IF NOT EXISTS idx_agent_performance_task ON agent_performance(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_performance_calculated ON agent_performance(calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_collaborations_task ON agent_collaborations(task_id);
CREATE INDEX IF NOT EXISTS idx_agent_collaborations_agents ON agent_collaborations(agent_1_id, agent_2_id);
CREATE INDEX IF NOT EXISTS idx_agent_collaborations_timestamp ON agent_collaborations(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_agent_snapshots_session ON agent_state_snapshots(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_snapshots_type ON agent_state_snapshots(snapshot_type);
CREATE INDEX IF NOT EXISTS idx_agent_snapshots_created ON agent_state_snapshots(created_at DESC);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_agent_sessions_state_gin ON agent_sessions USING GIN (state);
CREATE INDEX IF NOT EXISTS idx_agent_memory_metadata_gin ON agent_memory USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_agent_tools_input_gin ON agent_tools USING GIN (input_data);
CREATE INDEX IF NOT EXISTS idx_agent_tools_output_gin ON agent_tools USING GIN (output_data);
CREATE INDEX IF NOT EXISTS idx_agent_performance_metadata_gin ON agent_performance USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_agent_collaborations_metadata_gin ON agent_collaborations USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_agent_snapshots_state_gin ON agent_state_snapshots USING GIN (agent_state);

-- Comments for documentation
COMMENT ON TABLE agent_sessions IS 'Active agent sessions with task associations';
COMMENT ON TABLE agent_memory IS 'Agent conversation history (hybrid storage with ChromaDB)';
COMMENT ON TABLE agent_tools IS 'Agent tool usage tracking and performance metrics';
COMMENT ON TABLE agent_performance IS 'Agent performance metrics and analytics';
COMMENT ON TABLE agent_collaborations IS 'Agent collaboration patterns and effectiveness tracking';
COMMENT ON TABLE agent_state_snapshots IS 'Agent state checkpoints for recovery and analysis';

COMMENT ON COLUMN agent_memory.embedding_id IS 'Reference to corresponding ChromaDB embedding';
COMMENT ON COLUMN agent_memory.content IS 'Message content (also embedded in ChromaDB for semantic search)';
COMMENT ON COLUMN agent_tools.execution_time_ms IS 'Tool execution time in milliseconds';
COMMENT ON COLUMN agent_performance.time_period IS 'Aggregation period for metrics calculation';
COMMENT ON COLUMN agent_collaborations.success_score IS 'Collaboration effectiveness score (0.0 to 1.0)';

-- Create views for common queries

-- Active sessions summary
CREATE OR REPLACE VIEW active_sessions_view AS
SELECT 
    s.session_id,
    s.agent_id,
    s.task_id,
    s.started_at,
    s.total_messages,
    s.total_tokens,
    s.total_cost,
    EXTRACT(EPOCH FROM (NOW() - s.started_at)) / 60 as duration_minutes,
    COUNT(m.memory_id) as current_memory_count,
    MAX(m.timestamp) as last_message_time
FROM agent_sessions s
LEFT JOIN agent_memory m ON s.session_id = m.session_id
WHERE s.is_active = true
GROUP BY s.session_id, s.agent_id, s.task_id, s.started_at, s.total_messages, s.total_tokens, s.total_cost;

-- Tool usage summary
CREATE OR REPLACE VIEW tool_usage_summary AS
SELECT 
    tool_name,
    tool_category,
    COUNT(*) as usage_count,
    COUNT(CASE WHEN success = true THEN 1 END) as success_count,
    ROUND(AVG(execution_time_ms), 2) as avg_execution_time_ms,
    COUNT(CASE WHEN success = false THEN 1 END) as error_count,
    ROUND(COUNT(CASE WHEN success = false THEN 1 END)::DECIMAL / COUNT(*) * 100, 2) as error_rate_percent
FROM agent_tools
GROUP BY tool_name, tool_category
ORDER BY usage_count DESC;

-- Agent collaboration effectiveness
CREATE OR REPLACE VIEW collaboration_effectiveness AS
SELECT 
    agent_1_id,
    agent_2_id,
    collaboration_type,
    COUNT(*) as collaboration_count,
    ROUND(AVG(success_score), 3) as avg_success_score,
    MAX(timestamp) as last_collaboration
FROM agent_collaborations
WHERE success_score IS NOT NULL
GROUP BY agent_1_id, agent_2_id, collaboration_type
HAVING COUNT(*) >= 2
ORDER BY avg_success_score DESC, collaboration_count DESC;

COMMENT ON VIEW active_sessions_view IS 'Summary of currently active agent sessions';
COMMENT ON VIEW tool_usage_summary IS 'Tool usage statistics and performance metrics';
COMMENT ON VIEW collaboration_effectiveness IS 'Agent collaboration patterns and effectiveness scores';

-- Create functions for common operations

-- Function to create a new agent session
CREATE OR REPLACE FUNCTION create_agent_session(
    p_agent_id UUID,
    p_task_id UUID,
    p_initial_state JSONB DEFAULT '{}'::jsonb
) RETURNS UUID AS $$
DECLARE
    v_session_id UUID;
BEGIN
    INSERT INTO agent_sessions (agent_id, task_id, state)
    VALUES (p_agent_id, p_task_id, p_initial_state)
    RETURNING session_id INTO v_session_id;
    
    RETURN v_session_id;
END;
$$ LANGUAGE plpgsql;

-- Function to add memory to session
CREATE OR REPLACE FUNCTION add_agent_memory(
    p_session_id UUID,
    p_role VARCHAR(50),
    p_content TEXT,
    p_tokens_used INTEGER DEFAULT 0,
    p_model_name VARCHAR(100) DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
) RETURNS UUID AS $$
DECLARE
    v_memory_id UUID;
    v_sequence_number INTEGER;
BEGIN
    -- Get next sequence number for this session
    SELECT COALESCE(MAX(sequence_number), 0) + 1 
    INTO v_sequence_number 
    FROM agent_memory 
    WHERE session_id = p_session_id;
    
    INSERT INTO agent_memory (
        session_id, sequence_number, role, content, 
        tokens_used, model_name, metadata
    )
    VALUES (
        p_session_id, v_sequence_number, p_role, p_content, 
        p_tokens_used, p_model_name, p_metadata
    )
    RETURNING memory_id INTO v_memory_id;
    
    -- Update session totals
    UPDATE agent_sessions 
    SET 
        total_messages = total_messages + 1,
        total_tokens = total_tokens + p_tokens_used
    WHERE session_id = p_session_id;
    
    RETURN v_memory_id;
END;
$$ LANGUAGE plpgsql;

-- Function to end agent session
CREATE OR REPLACE FUNCTION end_agent_session(
    p_session_id UUID,
    p_final_state JSONB DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE agent_sessions 
    SET 
        is_active = false,
        ended_at = CURRENT_TIMESTAMP,
        state = COALESCE(p_final_state, state)
    WHERE session_id = p_session_id AND is_active = true;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_agent_session IS 'Create a new agent session for task execution';
COMMENT ON FUNCTION add_agent_memory IS 'Add memory entry to agent session with automatic sequence numbering';
COMMENT ON FUNCTION end_agent_session IS 'End an active agent session and store final state';

-- Success message
DO $$ 
BEGIN 
    RAISE NOTICE 'ATLAS Agents database initialized successfully!';
    RAISE NOTICE 'Tables created: agent_sessions, agent_memory, agent_tools, agent_performance, agent_collaborations, agent_state_snapshots';
    RAISE NOTICE 'Views created: active_sessions_view, tool_usage_summary, collaboration_effectiveness';
    RAISE NOTICE 'Functions created: create_agent_session(), add_agent_memory(), end_agent_session()';
    RAISE NOTICE 'Note: Cross-database foreign keys will be managed at application level';
END $$;