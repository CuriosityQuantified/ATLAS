# ATLAS LLM Logging Guide

## Overview

The ATLAS system now includes comprehensive logging for all LLM (Language Model) interactions. This logging captures:

1. **Exact prompts sent to LLM models**
2. **Exact responses received from models**
3. **Token usage and costs**
4. **Timing information**
5. **Error details**
6. **Agent-specific context (for Letta agents)**

## Log Files

Logs are stored in the `./logs/` directory (configurable via `ATLAS_LOG_DIR` environment variable):

- `llm_calls_YYYYMMDD.log` - All LLM interactions
- `letta_llm_calls_YYYYMMDD.log` - Letta agent-specific context

## Log Format

### Standard LLM Call Log

```
================================================================================
[LLM CALL START] 2024-12-19T10:30:45.123456
Provider: ANTHROPIC | Method: DIRECT
Model: claude-3-5-haiku-20241022
Agent ID: global_supervisor
Task ID: task_123
System Prompt: You are a helpful AI assistant...
Messages:
  [1] USER: What is the capital of France?
Parameters: max_tokens=1000, temperature=0.7
Response: The capital of France is Paris...
Tokens - Input: 45, Output: 23, Total: 68
Cost: $0.0012
Response Time: 1.234s
[LLM CALL END] 2024-12-19T10:30:46.357890
================================================================================
```

### Letta Agent Context Log

```
================================================================================
[LETTA AGENT CONTEXT] 2024-12-19T10:30:45.123456
Agent ID: simple_global_supervisor
Memory Context:
Long-term Memory:
- project_type: research_analysis
- client: test_user
Current Task Context:
- task_id: task_123
- status: in_progress
Available Tools:
- call_research_team: Call Research Team Supervisor for information gathering
- call_analysis_team: Call Analysis Team Supervisor for data analysis
User Message: Research quantum computing developments
================================================================================
```

### Error Log

```
================================================================================
[LLM CALL ERROR] 2024-12-19T10:30:47.123456
Provider: OPENAI | Method: DIRECT | Model: gpt-4
Error Type: RateLimitError
Error Message: Rate limit exceeded. Please try again later.
================================================================================
```

## Implementation Details

### 1. CallModel Integration

The `CallModel` utility automatically logs all LLM interactions:

```python
from utils.call_model import CallModel

call_model = CallModel(
    task_id="task_123",
    agent_id="my_agent"
)

response = await call_model.call_model(
    model_name="claude-3-5-haiku-20241022",
    system_prompt="You are a helpful assistant",
    most_recent_message="Hello, how are you?",
    max_tokens=100
)
# This call is automatically logged
```

### 2. SimpleLettaAgentMixin Integration

Letta agents automatically log their memory context:

```python
# In any agent inheriting from SimpleLettaAgentMixin
response = await self.send_to_letta(message)
# Memory context and tool usage are automatically logged
```

### 3. Centralized Logging Module

The `llm_logging.py` module provides:

- `LLMCallLogger` class with static methods
- Automatic file rotation (daily)
- Configurable log levels
- Separate loggers for different components

## Configuration

### Environment Variables

- `ATLAS_LOG_DIR` - Directory for log files (default: `./logs`)
- `ATLAS_LOG_LEVEL` - Logging level (default: `INFO`)

### Logging Levels

- `INFO` - Standard logging (prompts, responses, costs)
- `DEBUG` - Include additional context
- `WARNING` - Only log warnings and errors
- `ERROR` - Only log errors

## Viewing Logs

### Real-time Monitoring

```bash
# Watch all LLM calls
tail -f logs/llm_calls_$(date +%Y%m%d).log

# Watch Letta agent calls
tail -f logs/letta_llm_calls_$(date +%Y%m%d).log

# Search for specific model calls
grep "Model: claude-3-5-haiku" logs/llm_calls_*.log

# Find all errors
grep "ERROR" logs/llm_calls_*.log
```

### Analysis Scripts

```python
# Count total tokens used today
import re
from datetime import datetime

log_file = f"logs/llm_calls_{datetime.now().strftime('%Y%m%d')}.log"
total_tokens = 0

with open(log_file, 'r') as f:
    for line in f:
        if "Tokens - Input:" in line:
            match = re.search(r'Total: (\d+)', line)
            if match:
                total_tokens += int(match.group(1))

print(f"Total tokens used today: {total_tokens}")
```

## Privacy and Security

- Logs contain full prompts and responses
- Ensure logs directory has appropriate permissions
- Consider log rotation and archival policies
- Sensitive data in prompts will be logged

## Testing

Run the test script to verify logging is working:

```bash
python test_llm_logging.py
```

This will:
1. Make direct LLM calls
2. Test Global Supervisor with Letta
3. Test error logging
4. Create sample log files

## Troubleshooting

### Logs Not Appearing

1. Check `./logs/` directory exists and is writable
2. Verify logging level is set appropriately
3. Ensure `LLMCallLogger` is imported correctly

### Performance Impact

- Logging is asynchronous and shouldn't impact performance
- Large prompts/responses are truncated in logs
- File I/O is buffered

### Log File Size

- Logs rotate daily
- Consider implementing log cleanup for old files
- Monitor disk space in production

## Future Enhancements

1. **Structured Logging** - JSON format for easier parsing
2. **Metrics Dashboard** - Real-time cost and usage tracking
3. **Alerting** - Notifications for errors or cost thresholds
4. **Log Aggregation** - Centralized logging service integration
5. **Prompt Templates** - Track which prompts are most effective