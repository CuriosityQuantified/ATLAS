import os
from deepagents.openrouter_model import ChatOpenRouter


def get_default_model():
    """
    Get the default model for deep agents with throughput optimization.
    
    ALWAYS uses OpenRouter for all models with highest throughput providers.
    No direct Anthropic API calls - everything goes through OpenRouter.
    
    Environment Variables:
    - OPENROUTER_MODEL: Specify which model to use (default: qwen/qwen3-235b-a22b-thinking-2507)
    - MAX_TOKENS: Override default max tokens (default: 64000)
    """
    max_tokens = int(os.getenv("MAX_TOKENS", "64000"))
    
    # ALWAYS use OpenRouter with throughput optimization
    model_name = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-235b-a22b-thinking-2507")
    print(f"Using OpenRouter with model: {model_name} (throughput-optimized)")
    
    # Create throughput-optimized model instance
    return ChatOpenRouter.create_throughput_optimized(
        model_name=model_name, 
        max_tokens=max_tokens,
        site_url="https://atlas.deepagents.ai",  # For OpenRouter rankings
        site_name="ATLAS Deep Research Agents"
    )


def get_model_for_task(task_type: str = "general"):
    """
    Get an optimized model for a specific task type with throughput optimization.
    All models are accessed through OpenRouter with highest throughput providers.
    
    Args:
        task_type: Type of task ("general", "coding", "research", "creative", "cheap", "thinking")
    
    Returns:
        LangChain chat model optimized for the task (via OpenRouter with throughput optimization)
    """
    task_models = {
        "coding": "qwen/qwen3-coder-480b-a35b-instruct",  # Specialized Qwen3 coding model
        "research": "google/gemini-2.5-pro",  # Large context with thinking mode
        "creative": "anthropic/claude-opus-4",  # Best for creative tasks with hybrid reasoning
        "cheap": "deepseek-v3-0324",  # Very cost-effective ($0.27/1M)
        "thinking": "qwen/qwen3-235b-a22b-thinking-2507",  # Dedicated thinking/reasoning
        "general": "qwen/qwen3-235b-a22b-thinking-2507"  # Default to thinking model
    }
    
    model_name = task_models.get(task_type, task_models["general"])
    max_tokens = int(os.getenv("MAX_TOKENS", "64000"))
    
    # ALWAYS use OpenRouter with throughput optimization
    return ChatOpenRouter.create_throughput_optimized(
        model_name=model_name, 
        max_tokens=max_tokens,
        site_url="https://atlas.deepagents.ai",
        site_name="ATLAS Deep Research Agents"
    )
