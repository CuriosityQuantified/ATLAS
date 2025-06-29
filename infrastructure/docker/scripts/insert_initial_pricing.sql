-- Create the table to hold model pricing information
CREATE TABLE IF NOT EXISTS model_pricing (
    model_name VARCHAR(255) PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    input_cost_per_million_tokens NUMERIC(10, 4) NOT NULL,
    output_cost_per_million_tokens NUMERIC(10, 4) NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial data, avoiding conflicts if it already exists
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
('gpt-4.1-nano', 'OpenAI', 0.10, 0.40),
('o1-mini', 'OpenAI', 1.10, 4.40),
('o3-mini', 'OpenAI', 1.10, 4.40),
('o4-mini', 'OpenAI', 1.10, 4.40),
('o3', 'OpenAI', 2.00, 8.00),
('o3-pro', 'OpenAI', 20.00, 80.00),
('gpt-3.5-turbo', 'OpenAI', 0.50, 1.50),

-- Google
('gemini-2.5-pro', 'Google', 3.50, 10.50),
('gemini-2.5-flash', 'Google', 0.30, 0.60),
('gemini-1.5-pro', 'Google', 3.50, 10.50),
('gemini-1.5-flash', 'Google', 0.35, 0.70),

-- Groq
('qwen/qwen3-32b', 'Groq', 0.29, 0.59),
('meta-llama/llama-prompt-guard-2-86m', 'Groq', 0.00, 0.00),
('meta-llama/llama-prompt-guard-2-22m', 'Groq', 0.00, 0.00),
('playai-tts-arabic', 'Groq', 0.00, 0.00),
('meta-llama/llama-guard-4-12b', 'Groq', 0.20, 0.20),
('meta-llama/llama-4-maverick-17b-128e-instruct', 'Groq', 0.20, 0.60),
('llama-3.3-70b-versatile', 'Groq', 0.59, 0.79),
('mistral-saba-24b', 'Groq', 0.79, 0.79),
('compound-beta-mini', 'Groq', 0.00, 0.00),
('compound-beta', 'Groq', 0.00, 0.00),
('qwen-qwq-32b', 'Groq', 0.29, 0.39),
('llama-3.1-8b-instant', 'Groq', 0.00, 0.00),
('deepseek-r1-distill-llama-70b', 'Groq', 0.75, 0.99),
('llama3-8b-8192', 'Groq', 0.05, 0.10),
('playai-tts', 'Groq', 0.00, 0.00),
('allam-2-7b', 'Groq', 0.00, 0.00),
('distil-whisper-large-v3-en', 'Groq', 0.00, 0.00),
('whisper-large-v3', 'Groq', 0.00, 0.00),
('whisper-large-v3-turbo', 'Groq', 0.00, 0.00),
('llama3-70b-8192', 'Groq', 0.59, 0.79),
('gemma2-9b-it', 'Groq', 0.20, 0.20),
('meta-llama/llama-4-scout-17b-16e-instruct', 'Groq', 0.11, 0.34),

('default', 'Unknown', 0.00, 0.00)
ON CONFLICT (model_name) DO NOTHING;
