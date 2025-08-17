import os
from deepagents.openrouter_model import ChatOpenRouter


def get_default_model():
    """
    Get the default model for deep agents.
    
    ALWAYS uses OpenRouter for all models (including Anthropic models).
    No direct Anthropic API calls - everything goes through OpenRouter.
    
    Environment Variables:
    - OPENROUTER_MODEL: Specify which model to use (default: qwen3-235b-a22b-thinking-2507)
    - MAX_TOKENS: Override default max tokens (default: 64000)
    """
    max_tokens = int(os.getenv("MAX_TOKENS", "64000"))
    
    # ALWAYS use OpenRouter - no direct Anthropic API
    model_name = os.getenv("OPENROUTER_MODEL", "qwen3-235b-a22b-thinking-2507")
    print(f"Using OpenRouter with model: {model_name}")
    
    # You can still use Anthropic models through OpenRouter!
    # Examples:
    # - claude-opus-4-20250514-thinking-16k
    # - claude-sonnet-4-20250514-thinking-32k
    # - claude-3-7-sonnet-20250219-thinking-32k
    # - qwen3-235b-a22b-thinking-2507 (default)
    
    return ChatOpenRouter(model_name=model_name, max_tokens=max_tokens)


def get_model_for_task(task_type: str = "general"):
    """
    Get an optimized model for a specific task type.
    All models are accessed through OpenRouter.
    
    Args:
        task_type: Type of task ("general", "coding", "research", "creative", "cheap", "thinking")
    
    Returns:
        LangChain chat model optimized for the task (via OpenRouter)
    """
    task_models = {
        "coding": "qwen3-coder-480b-a35b-instruct",  # Specialized Qwen3 coding model
        "research": "gemini-2.5-pro",  # Large context with thinking mode
        "creative": "claude-opus-4-20250514",  # Best for creative tasks with hybrid reasoning
        "cheap": "deepseek-v3-0324",  # Very cost-effective ($0.27/1M)
        "thinking": "qwen3-235b-a22b-thinking-2507",  # Dedicated thinking/reasoning
        "general": "qwen3-235b-a22b-thinking-2507"  # Default to thinking model
    }
    
    model_name = task_models.get(task_type, task_models["general"])
    max_tokens = int(os.getenv("MAX_TOKENS", "64000"))
    
    # ALWAYS use OpenRouter
    return ChatOpenRouter(model_name=model_name, max_tokens=max_tokens)
