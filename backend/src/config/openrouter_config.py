"""OpenRouter model configuration with provider preferences."""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class OpenRouterModel:
    model: str
    provider: str
    priority: int
    context_window: int = 32768

class OpenRouterConfig:
    """Manages OpenRouter model selection and fallback."""

    MODELS = [
        # Groq tier - fastest response
        OpenRouterModel("moonshotai/kimi-k2-0905", "Groq", 1, 200000),

        # Cerebras tier - powerful Qwen models
        OpenRouterModel("qwen/qwen3-235b-a22b-thinking-2507", "Cerebras", 2, 32768),
        OpenRouterModel("qwen/qwen3-235b-a22b-2507", "Cerebras", 3, 32768),
        OpenRouterModel("qwen/qwen3-coder", "Cerebras", 4, 32768),

        # Sambanova tier - DeepSeek models
        OpenRouterModel("deepseek/deepseek-chat-v3.1", "Sambanova", 5, 64000),
        OpenRouterModel("deepseek/deepseek-chat-v3-0324", "Sambanova", 6, 64000),
        OpenRouterModel("moonshotai/kimi-k2-0905", "Sambanova", 7, 200000),
    ]

    @classmethod
    def get_primary_model(cls) -> str:
        """Get the primary (highest priority) model."""
        return cls.MODELS[0].model

    @classmethod
    def get_model_by_priority(cls, priority: int) -> Optional[OpenRouterModel]:
        """Get model by priority number."""
        for model in cls.MODELS:
            if model.priority == priority:
                return model
        return None

    @classmethod
    def get_llm_config(cls, model_priority: int = 0, api_key: str = None):
        """Generate Letta LLM config for OpenRouter model.

        Args:
            model_priority: Index in the MODELS list (0 = highest priority)
            api_key: OpenRouter API key (optional, will use environment if not provided)

        Returns:
            Dictionary with LLM configuration for Letta
        """
        import os

        model_config = cls.MODELS[model_priority] if model_priority < len(cls.MODELS) else cls.MODELS[0]

        # Get API key from parameter or environment
        openrouter_api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        config = {
            "model": f"openrouter/{model_config.model}",
            "model_endpoint_type": "openai",
            "model_endpoint": "https://openrouter.ai/api/v1",
            "context_window": model_config.context_window,
            "extra_headers": {
                "HTTP-Referer": "https://atlas.local",
                "X-Title": "ATLAS Multi-Agent System"
            }
        }

        # Add API key if available
        if openrouter_api_key:
            config["model_api_key"] = openrouter_api_key

        return config

    @classmethod
    def get_provider_order(cls) -> list[str]:
        """Get the provider order for OpenRouter requests.

        Returns:
            List of provider names in priority order
        """
        # Return unique providers in priority order
        seen = set()
        providers = []
        for model in cls.MODELS:
            provider_lower = model.provider.lower()
            if provider_lower not in seen:
                seen.add(provider_lower)
                providers.append(provider_lower)
        return providers

    @classmethod
    def get_extra_body(cls, model_priority: int = 0) -> dict:
        """Get the extra_body configuration for OpenRouter API calls.

        Args:
            model_priority: Index in the MODELS list to determine primary provider

        Returns:
            Dictionary with provider configuration for extra_body
        """
        model_config = cls.MODELS[model_priority] if model_priority < len(cls.MODELS) else cls.MODELS[0]

        # Build provider order starting from the specified model's provider
        provider_order = []
        primary_provider = model_config.provider.lower()
        provider_order.append(primary_provider)

        # Add other providers in fallback order
        for provider in cls.get_provider_order():
            if provider != primary_provider and provider not in provider_order:
                provider_order.append(provider)

        return {
            "provider": {
                "order": provider_order,
                "allow_fallbacks": True
            }
        }

    @classmethod
    def get_fallback_list(cls) -> List[Dict[str, any]]:
        """Get the complete fallback list as dictionaries.

        Returns:
            List of model configurations in priority order
        """
        return [
            {
                "model": m.model,
                "provider": m.provider,
                "priority": m.priority,
                "context_window": m.context_window
            }
            for m in cls.MODELS
        ]