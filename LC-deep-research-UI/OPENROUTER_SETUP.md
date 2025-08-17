# OpenRouter Integration for Deep Agents UI

## Overview

OpenRouter support has been successfully integrated into the Deep Agents UI system. This allows you to use alternative LLM models when Anthropic credits are exhausted or when you want to use specialized models for specific tasks.

## What Was Implemented

### 1. **OpenRouter LangChain Adapter** (`deepagents/src/deepagents/openrouter_model.py`)
- Custom `ChatOpenRouter` class that extends LangChain's `ChatOpenAI`
- Support for 100+ models through OpenRouter's unified API
- Model-specific configurations (token limits, pricing)
- Helper methods for model selection based on task or cost

### 2. **Enhanced Model Selection** (`deepagents/src/deepagents/model.py`)
- Automatic fallback from Anthropic to OpenRouter
- Environment variable configuration
- Task-specific model selection
- Graceful error handling

### 3. **Dependencies Updated** (`deepagents/pyproject.toml`)
- Added `langchain-openai>=0.1.0` dependency
- Maintains compatibility with existing `langchain-anthropic`

## Configuration

### Environment Variables

Add these to your `.env` file or set them in your environment:

```bash
# Required - Your OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

# Optional - Force OpenRouter usage (default: false)
USE_OPENROUTER=true

# Optional - Specify which model to use with OpenRouter
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# Optional - Override maximum tokens (default: 64000)
MAX_TOKENS=32768

# Optional - Override default Anthropic model
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

## Usage Modes

### 1. **Automatic Fallback Mode** (Default)
When `USE_OPENROUTER` is not set or false:
- Primary: Uses Anthropic directly
- Fallback: Automatically switches to OpenRouter if Anthropic fails
- Best for: Normal operation with cost optimization

### 2. **Forced OpenRouter Mode**
When `USE_OPENROUTER=true`:
- Always uses OpenRouter, even if Anthropic is available
- Useful for: Testing, specific model requirements, or when Anthropic credits are exhausted

### 3. **Task-Specific Models**
The system can automatically select optimal models based on task type:

```python
from deepagents.model import get_model_for_task

# Specialized models for different tasks
coding_model = get_model_for_task("coding")      # Qwen Coder
research_model = get_model_for_task("research")  # Gemini Pro (large context)
creative_model = get_model_for_task("creative")  # Claude Opus
cheap_model = get_model_for_task("cheap")        # Gemini Flash
```

## Available Models via OpenRouter

### Top Recommended Models

| Model | Token Limit | Cost/1M | Best For |
|-------|------------|---------|----------|
| `anthropic/claude-3-sonnet` | 200K | $3.00 | General purpose, balanced |
| `anthropic/claude-3-haiku` | 200K | $0.25 | Fast, cheap responses |
| `openai/gpt-4o` | 128K | $5.00 | Advanced reasoning |
| `google/gemini-pro-1.5` | 1M | $0.50 | Large context research |
| `google/gemini-flash-1.5` | 1M | $0.075 | Very cheap, fast |
| `qwen/qwen-2.5-coder-32b-instruct` | 32K | $0.18 | Specialized coding |
| `deepseek/deepseek-chat` | 32K | $0.14 | General purpose, cheap |
| `meta-llama/llama-3.1-70b-instruct` | 131K | $0.52 | Open source, powerful |

## Installation

1. **Install Dependencies**
```bash
pip install langchain-openai
```

2. **Set Environment Variables**
```bash
export OPENROUTER_API_KEY="your-api-key-here"
export USE_OPENROUTER=true  # Optional: force OpenRouter
export OPENROUTER_MODEL="google/gemini-flash-1.5"  # Optional: specific model
```

3. **Run Your Application**
The system will automatically use OpenRouter based on your configuration.

## Testing the Integration

Run the provided test script to verify everything works:

```bash
python3 test_openrouter_simple.py
```

This will test:
- Direct OpenRouter API calls
- Model selection logic
- Fallback behavior
- LangChain compatibility

## Cost Optimization Tips

1. **Use Tiered Models**: Start with cheaper models (Gemini Flash) and escalate only when needed
2. **Set Token Limits**: Use `MAX_TOKENS` to control response length
3. **Task-Specific Models**: Use specialized models for better performance/cost ratio
4. **Monitor Usage**: OpenRouter provides detailed usage statistics in their dashboard

## Troubleshooting

### "No module named 'langchain_openai'"
```bash
pip install langchain-openai
```

### "OPENROUTER_API_KEY not found"
Make sure your API key is set in the environment or `.env` file.

### Model Not Available
Check the OpenRouter dashboard for available models. Some models may require specific permissions.

### Python Version Issues
The deep agents package requires Python 3.11+. If you're on an older version, you can still use the OpenRouter integration by importing the modules directly.

## Benefits of This Integration

1. **Cost Savings**: Access to models that are 10-100x cheaper than Claude
2. **No Downtime**: Automatic fallback when Anthropic credits are exhausted
3. **Model Variety**: Access to 100+ models for different use cases
4. **Future Proof**: Easy to add new providers as they become available
5. **Backward Compatible**: Existing code continues to work without changes

## Next Steps

1. **Monitor Performance**: Track which models work best for your use cases
2. **Optimize Costs**: Adjust model selection based on usage patterns
3. **Expand Integration**: Consider adding more providers (Together AI, Replicate, etc.)
4. **User Interface**: Add model selection dropdown in the UI for manual override

## Support

For issues or questions about the OpenRouter integration:
- Check OpenRouter documentation: https://openrouter.ai/docs
- Review the test files: `test_openrouter_simple.py`
- Check the implementation: `deepagents/src/deepagents/openrouter_model.py`