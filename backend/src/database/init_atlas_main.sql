-- ATLAS Main Database Initialization Script
-- Database: atlas_main
-- Purpose: Core application data and task management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSONB GIN indexing
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Tasks table - Core task tracking
CREATE TABLE IF NOT EXISTS tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100), -- Determined via LLM analysis (future feature)
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_duration_seconds INTEGER,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    summary TEXT, -- LLM-generated summary (future feature)
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'medium', 'high', 'critical'))
);

-- Agents table - Agent configurations and metadata
CREATE TABLE IF NOT EXISTS agents (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type VARCHAR(100) NOT NULL, -- 'global_supervisor', 'research_supervisor', 'research_worker', etc.
    team VARCHAR(50) NOT NULL, -- 'global', 'research', 'analysis', 'writing', 'rating'
    persona_config JSONB NOT NULL,
    tools JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    CONSTRAINT valid_team CHECK (team IN ('global', 'research', 'analysis', 'writing', 'rating'))
);

-- Executions table - Task execution history
CREATE TABLE IF NOT EXISTS executions (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(agent_id),
    sequence_number INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10, 4) DEFAULT 0,
    model_name VARCHAR(100),
    model_provider VARCHAR(50),
    error_message TEXT,
    result JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_exec_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'timeout'))
);

-- File metadata table for multi-modal content storage
CREATE TABLE IF NOT EXISTS file_metadata (
    file_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(task_id) ON DELETE CASCADE,
    project_name VARCHAR(255) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- 'image', 'audio', 'video', '3d_model', 'document'
    file_extension VARCHAR(10) NOT NULL,
    file_path TEXT NOT NULL, -- Local filesystem path
    file_size_bytes BIGINT NOT NULL,
    checksum VARCHAR(64) NOT NULL, -- SHA-256 checksum
    mime_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_file_type CHECK (file_type IN ('image', 'audio', 'video', '3d_model', 'document', 'other'))
);

-- Project metrics table for analytics (future optimization feature)
CREATE TABLE IF NOT EXISTS project_metrics (
    metric_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(20, 4),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    time_period VARCHAR(50), -- 'hourly', 'daily', 'weekly', 'monthly'
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_metric_type CHECK (metric_type IN (
        'total_tasks', 'avg_cost_per_task', 'total_tokens', 'avg_duration',
        'total_cost', 'success_rate', 'avg_quality_score', 'model_diversity'
    ))
);

-- Model pricing table (already exists from cost_calculator.py)
CREATE TABLE IF NOT EXISTS model_pricing (
    model_name VARCHAR(255) PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    input_cost_per_million_tokens NUMERIC(10, 4) NOT NULL,
    output_cost_per_million_tokens NUMERIC(10, 4) NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_tasks_project_name ON tasks(project_name);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type) WHERE task_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_team ON agents(team);
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_executions_task_id ON executions(task_id);
CREATE INDEX IF NOT EXISTS idx_executions_agent_id ON executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_executions_model_provider ON executions(model_provider);
CREATE INDEX IF NOT EXISTS idx_executions_model_name ON executions(model_name);
CREATE INDEX IF NOT EXISTS idx_executions_started_at ON executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);

CREATE INDEX IF NOT EXISTS idx_file_metadata_task_id ON file_metadata(task_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_project ON file_metadata(project_name);
CREATE INDEX IF NOT EXISTS idx_file_metadata_type ON file_metadata(file_type);
CREATE INDEX IF NOT EXISTS idx_file_metadata_created ON file_metadata(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_project_metrics_project_time ON project_metrics(project_name, calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_metrics_type ON project_metrics(metric_type);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_tasks_metadata_gin ON tasks USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_executions_metadata_gin ON executions USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_file_metadata_gin ON file_metadata USING GIN (metadata);

-- Comments for documentation
COMMENT ON TABLE tasks IS 'Core task tracking and management';
COMMENT ON TABLE agents IS 'Agent configurations and metadata';
COMMENT ON TABLE executions IS 'Task execution history and performance data';
COMMENT ON TABLE file_metadata IS 'Multi-modal file storage metadata and references';
COMMENT ON TABLE project_metrics IS 'Project analytics and metrics (future feature)';
COMMENT ON TABLE model_pricing IS 'LLM model pricing for cost calculations';

COMMENT ON COLUMN tasks.task_type IS 'Task classification via LLM analysis (future feature)';
COMMENT ON COLUMN tasks.summary IS 'LLM-generated task summary (future feature)';
COMMENT ON COLUMN file_metadata.file_path IS 'Local filesystem path: /data/files/{project_name}/{file_type}/{file_id}.{ext}';
COMMENT ON COLUMN file_metadata.checksum IS 'SHA-256 checksum for file integrity verification';

-- Insert default model pricing data (if not already present)
INSERT INTO model_pricing (model_name, provider, input_cost_per_million_tokens, output_cost_per_million_tokens) VALUES
-- Anthropic
('claude-4-opus', 'Anthropic', 15.00, 75.00),
('claude-4-sonnet', 'Anthropic', 3.00, 15.00),
('claude-3.5-haiku', 'Anthropic', 0.80, 1.25),
('claude-3-opus', 'Anthropic', 15.00, 75.00),
('claude-3.7-sonnet', 'Anthropic', 3.00, 15.00),
('claude-3-haiku', 'Anthropic', 0.25, 1.25),

-- OpenAI
('gpt-4o', 'OpenAI', 2.50, 10.00),
('gpt-4o-mini', 'OpenAI', 0.15, 0.60),
('gpt-4.1', 'OpenAI', 2.00, 8.00),
('gpt-4.1-mini', 'OpenAI', 0.40, 1.60),
('o1-mini', 'OpenAI', 1.10, 4.40),
('o3-mini', 'OpenAI', 1.10, 4.40),
('gpt-3.5-turbo', 'OpenAI', 0.50, 1.50),

-- Google
('gemini-2.5-pro', 'Google', 3.50, 10.50),
('gemini-2.5-flash', 'Google', 0.30, 0.60),
('gemini-1.5-pro', 'Google', 3.50, 10.50),
('gemini-1.5-flash', 'Google', 0.35, 0.70),

-- Groq
('llama-3.3-70b-versatile', 'Groq', 0.59, 0.79),
('llama3-70b-8192', 'Groq', 0.59, 0.79),
('llama3-8b-8192', 'Groq', 0.05, 0.10),
('gemma2-9b-it', 'Groq', 0.20, 0.20),

('default', 'Unknown', 0.00, 0.00)
ON CONFLICT (model_name) DO NOTHING;

-- Create a simple view for task summaries (foundation for future analytics)
CREATE OR REPLACE VIEW task_summary_view AS
SELECT 
    t.project_name,
    COUNT(DISTINCT t.task_id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks,
    ROUND(AVG(t.total_cost), 4) as avg_cost_per_task,
    SUM(t.total_input_tokens + t.total_output_tokens) as total_tokens,
    ROUND(AVG(t.total_duration_seconds), 2) as avg_duration_seconds,
    SUM(t.total_cost) as total_project_cost,
    MAX(t.created_at) as last_task_created,
    COUNT(DISTINCT e.agent_id) as unique_agents_used
FROM tasks t
LEFT JOIN executions e ON t.task_id = e.task_id
GROUP BY t.project_name;

COMMENT ON VIEW task_summary_view IS 'Basic project metrics view (foundation for future analytics dashboard)';

-- Create a function to generate file paths
CREATE OR REPLACE FUNCTION generate_file_path(
    p_project_name VARCHAR(255),
    p_file_type VARCHAR(50),
    p_file_id UUID,
    p_file_extension VARCHAR(10)
) RETURNS TEXT AS $$
BEGIN
    RETURN '/data/files/' || p_project_name || '/' || p_file_type || '/' || p_file_id::text || '.' || p_file_extension;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION generate_file_path IS 'Generate standardized file paths for multi-modal content storage';

-- Success message
DO $$ 
BEGIN 
    RAISE NOTICE 'ATLAS Main database initialized successfully!';
    RAISE NOTICE 'Tables created: tasks, agents, executions, file_metadata, project_metrics, model_pricing';
    RAISE NOTICE 'View created: task_summary_view';
    RAISE NOTICE 'Function created: generate_file_path()';
END $$;