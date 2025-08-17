"""
OpenRouter integration for LangChain models.
Provides access to 100+ LLM models through OpenRouter's unified API.
"""

import os
from typing import Optional, Dict, Any, ClassVar
from langchain_openai import ChatOpenAI


class ChatOpenRouter(ChatOpenAI):
    """
    LangChain-compatible chat model that uses OpenRouter's API.
    
    OpenRouter provides access to models from:
    - Anthropic (Claude 3 series)
    - OpenAI (GPT-4, GPT-3.5)
    - Google (Gemini, PaLM)
    - Meta (Llama series)
    - Mistral AI
    - DeepSeek
    - Qwen
    - And many more...
    """
    
    # Common model configurations with their token limits
    MODEL_CONFIGS: ClassVar[Dict[str, Dict[str, Any]]] = {
        # Thinking/Reasoning Models (with dedicated CoT)
        "claude-opus-4-20250514-thinking-16k": {"max_tokens": 16384, "cost_per_1m": 20.00, "thinking": True},
        "claude-sonnet-4-20250514-thinking-32k": {"max_tokens": 32768, "cost_per_1m": 8.00, "thinking": True},
        "claude-3-7-sonnet-20250219-thinking-32k": {"max_tokens": 32768, "cost_per_1m": 6.00, "thinking": True},
        "qwen3-235b-a22b-thinking-2507": {"max_tokens": 65536, "cost_per_1m": 2.50, "thinking": True},
        "deepseek-r1-0528": {"max_tokens": 32768, "cost_per_1m": 1.50, "thinking": True},
        "deepseek-r1": {"max_tokens": 32768, "cost_per_1m": 1.50, "thinking": True},
        
        # Hybrid Models (optional thinking modes)
        "claude-opus-4-1-20250805": {"max_tokens": 200000, "cost_per_1m": 15.00, "hybrid": True},
        "claude-opus-4-20250514": {"max_tokens": 200000, "cost_per_1m": 15.00, "hybrid": True},
        "gemini-2.5-pro": {"max_tokens": 1000000, "cost_per_1m": 1.25, "hybrid": True},
        "gemini-2.5-flash": {"max_tokens": 1000000, "cost_per_1m": 0.30, "hybrid": True},
        "hunyuan-turbos-20250416": {"max_tokens": 128000, "cost_per_1m": 0.80, "hybrid": True},
        
        # Standard Models (no thinking modes)
        "claude-sonnet-4-20250514": {"max_tokens": 200000, "cost_per_1m": 3.00},
        "qwen3-235b-a22b-instruct-2507": {"max_tokens": 65536, "cost_per_1m": 1.80},
        "qwen3-235b-a22b-no-thinking": {"max_tokens": 65536, "cost_per_1m": 1.80},
        "qwen3-30b-a3b-instruct-2507": {"max_tokens": 32768, "cost_per_1m": 0.35},
        "qwen3-coder-480b-a35b-instruct": {"max_tokens": 32768, "cost_per_1m": 3.00},
        "kimi-k2-0711-preview": {"max_tokens": 128000, "cost_per_1m": 0.60},
        "deepseek-v3-0324": {"max_tokens": 32768, "cost_per_1m": 0.27},
        "glm-4.5": {"max_tokens": 128000, "cost_per_1m": 0.50},
        "glm-4.5-air": {"max_tokens": 128000, "cost_per_1m": 0.30},
        "mistral-medium-2505": {"max_tokens": 128000, "cost_per_1m": 2.70},
        
        # Legacy models (keeping for backward compatibility)
        "anthropic/claude-3-opus": {"max_tokens": 200000, "cost_per_1m": 15.00},
        "anthropic/claude-3-sonnet": {"max_tokens": 200000, "cost_per_1m": 3.00},
        "anthropic/claude-3-haiku": {"max_tokens": 200000, "cost_per_1m": 0.25},
        "openai/gpt-4o": {"max_tokens": 128000, "cost_per_1m": 5.00},
        "google/gemini-pro": {"max_tokens": 1000000, "cost_per_1m": 0.50},
        "deepseek/deepseek-chat": {"max_tokens": 32768, "cost_per_1m": 0.14},
        
        # Default fallback
        "default": {"max_tokens": 32768, "cost_per_1m": 1.00}
    }
    
    def __init__(
        self,
        model_name: str = "qwen3-235b-a22b-thinking-2507",
        api_key: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize ChatOpenRouter with OpenRouter's API endpoint.
        
        Args:
            model_name: The model identifier (e.g., "anthropic/claude-3-sonnet")
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            max_tokens: Maximum tokens for response (defaults to model's limit)
            temperature: Sampling temperature (0-2, default 0.7)
            **kwargs: Additional arguments passed to ChatOpenAI
        """
        # Get API key from environment if not provided
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API key not found. "
                "Please set OPENROUTER_API_KEY environment variable or pass api_key parameter."
            )
        
        # Get model configuration
        model_config = self.MODEL_CONFIGS.get(model_name, self.MODEL_CONFIGS["default"])
        
        # Use provided max_tokens or fall back to model's default
        if max_tokens is None:
            max_tokens = model_config["max_tokens"]
        
        # Ensure max_tokens doesn't exceed model's limit
        max_tokens = min(max_tokens, model_config["max_tokens"])
        
        # Initialize with OpenRouter's base URL
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
    
    @classmethod
    def list_available_models(cls) -> Dict[str, Dict[str, Any]]:
        """List all available models with their configurations."""
        return cls.MODEL_CONFIGS.copy()
    
    @classmethod
    def get_cheapest_model(cls, min_tokens: int = 16384) -> str:
        """
        Get the cheapest model that supports at least min_tokens.
        
        Args:
            min_tokens: Minimum token limit required
            
        Returns:
            Model identifier for the cheapest suitable model
        """
        suitable_models = [
            (name, config) 
            for name, config in cls.MODEL_CONFIGS.items() 
            if name != "default" and config["max_tokens"] >= min_tokens
        ]
        
        if not suitable_models:
            return "anthropic/claude-3-haiku"  # Reasonable default
        
        # Sort by cost
        suitable_models.sort(key=lambda x: x[1]["cost_per_1m"])
        return suitable_models[0][0]
    
    @classmethod
    def get_most_capable_model(cls) -> str:
        """Get the most capable model (typically highest token limit)."""
        best_model = max(
            [(name, config) for name, config in cls.MODEL_CONFIGS.items() if name != "default"],
            key=lambda x: x[1]["max_tokens"]
        )
        return best_model[0]


# Removed create_model_with_fallback function - using OpenRouter exclusively