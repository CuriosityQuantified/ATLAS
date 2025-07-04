-- Chat History Schema for ATLAS
-- This schema supports persistent chat storage and MLflow integration

-- Chat Sessions Table
-- Links chat conversations to tasks and MLflow runs
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    mlflow_run_id VARCHAR(255),
    user_id VARCHAR(255) DEFAULT 'default_user',
    session_metadata JSONB DEFAULT '{}'::jsonb,
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10,6) DEFAULT 0.0,
    UNIQUE(task_id)
);

-- Chat Messages Table
-- Stores individual messages in conversations
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(50) NOT NULL, -- 'user', 'agent', 'system'
    content TEXT NOT NULL,
    agent_id VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0.0,
    processing_time_ms INTEGER DEFAULT 0,
    model_used VARCHAR(100),
    response_quality DECIMAL(3,2) -- Quality score 0.0-5.0
);

-- Performance Indexes
CREATE INDEX idx_chat_sessions_task_id ON chat_sessions(task_id);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);
CREATE INDEX idx_chat_messages_agent_id ON chat_messages(agent_id);
CREATE INDEX idx_chat_messages_type ON chat_messages(message_type);

-- Update trigger for chat_sessions updated_at
CREATE OR REPLACE FUNCTION update_chat_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_chat_sessions_timestamp
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_session_timestamp();

-- Update trigger for message counts and costs
CREATE OR REPLACE FUNCTION update_chat_session_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE chat_sessions 
        SET 
            message_count = message_count + 1,
            total_tokens = total_tokens + COALESCE(NEW.tokens_used, 0),
            total_cost_usd = total_cost_usd + COALESCE(NEW.cost_usd, 0.0),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.session_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE chat_sessions 
        SET 
            message_count = message_count - 1,
            total_tokens = total_tokens - COALESCE(OLD.tokens_used, 0),
            total_cost_usd = total_cost_usd - COALESCE(OLD.cost_usd, 0.0),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.session_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_chat_session_stats
    AFTER INSERT OR DELETE ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_session_stats();

-- Grant permissions to atlas_main_user
GRANT ALL PRIVILEGES ON chat_sessions TO atlas_main_user;
GRANT ALL PRIVILEGES ON chat_messages TO atlas_main_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO atlas_main_user;

-- Comments for documentation
COMMENT ON TABLE chat_sessions IS 'Chat session management linked to tasks and MLflow runs';
COMMENT ON TABLE chat_messages IS 'Individual messages within chat conversations';
COMMENT ON COLUMN chat_sessions.mlflow_run_id IS 'Links chat session to MLflow experiment run';
COMMENT ON COLUMN chat_messages.message_type IS 'Type: user, agent, system';
COMMENT ON COLUMN chat_messages.response_quality IS 'Quality score 0.0-5.0 for response assessment';