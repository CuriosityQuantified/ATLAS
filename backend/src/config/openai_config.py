"""OpenAI model configuration for ATLAS agents."""

import os
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class OpenAIModel:
    """OpenAI model configuration."""
    model: str
    context_window: int
    use_case: str
    cost_per_1k_input: float  # in USD
    cost_per_1k_output: float  # in USD


class OpenAIConfig:
    """Manages OpenAI model selection for different agent types."""

    # Model definitions with current pricing (as of January 2025)
    MODELS = {
        "supervisor": OpenAIModel(
            model="gpt-4o",
            context_window=128000,
            use_case="Complex reasoning, supervision, and writing",
            cost_per_1k_input=0.0025,
            cost_per_1k_output=0.01
        ),
        "writing": OpenAIModel(
            model="gpt-4o",
            context_window=128000,
            use_case="High-quality content generation",
            cost_per_1k_input=0.0025,
            cost_per_1k_output=0.01
        ),
        "research": OpenAIModel(
            model="gpt-4o-mini",
            context_window=128000,
            use_case="Research and information gathering",
            cost_per_1k_input=0.00015,
            cost_per_1k_output=0.0006
        ),
        "analysis": OpenAIModel(
            model="gpt-4o-mini",
            context_window=128000,
            use_case="Data analysis and processing",
            cost_per_1k_input=0.00015,
            cost_per_1k_output=0.0006
        ),
        "default": OpenAIModel(
            model="gpt-4o-mini",
            context_window=128000,
            use_case="General purpose tasks",
            cost_per_1k_input=0.00015,
            cost_per_1k_output=0.0006
        )
    }

    # Embedding model configuration
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIM = 1536
    EMBEDDING_CHUNK_SIZE = 300

    @classmethod
    def get_llm_config(cls, agent_type: str = "default", api_key: Optional[str] = None) -> Dict:
        """Generate Letta LLM config for OpenAI models.

        Args:
            agent_type: Type of agent (supervisor, writing, research, analysis, default)
            api_key: OpenAI API key (optional, will use environment if not provided)

        Returns:
            Dictionary with LLM configuration for Letta
        """
        # Get model configuration for agent type
        model_config = cls.MODELS.get(agent_type, cls.MODELS["default"])

        # Get API key from parameter or environment
        openai_api_key = api_key or os.getenv("OPENAI_API_KEY")

        config = {
            "model": model_config.model,
            "model_endpoint_type": "openai",
            "model_endpoint": "https://api.openai.com/v1",
            "context_window": model_config.context_window,
        }

        # Add API key if available
        if openai_api_key:
            config["model_api_key"] = openai_api_key

        return config

    @classmethod
    def get_embedding_config(cls, api_key: Optional[str] = None) -> Dict:
        """Generate Letta embedding config for OpenAI embeddings.

        Args:
            api_key: OpenAI API key (optional, will use environment if not provided)

        Returns:
            Dictionary with embedding configuration for Letta
        """
        # Get API key from parameter or environment
        openai_api_key = api_key or os.getenv("OPENAI_API_KEY")

        config = {
            "embedding_model": cls.EMBEDDING_MODEL,
            "embedding_endpoint_type": "openai",
            "embedding_endpoint": "https://api.openai.com/v1",
            "embedding_dim": cls.EMBEDDING_DIM,
            "embedding_chunk_size": cls.EMBEDDING_CHUNK_SIZE,
        }

        # Add API key if available
        if openai_api_key:
            config["embedding_api_key"] = openai_api_key

        return config

    @classmethod
    def get_model_for_agent(cls, agent_type: str) -> str:
        """Get the model name for a specific agent type.

        Args:
            agent_type: Type of agent

        Returns:
            Model name string
        """
        model_config = cls.MODELS.get(agent_type, cls.MODELS["default"])
        return model_config.model

    @classmethod
    def estimate_cost(cls, agent_type: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate the cost for a given agent type and token usage.

        Args:
            agent_type: Type of agent
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        model_config = cls.MODELS.get(agent_type, cls.MODELS["default"])

        input_cost = (input_tokens / 1000) * model_config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model_config.cost_per_1k_output

        return input_cost + output_cost

    @classmethod
    def get_all_models(cls) -> Dict[str, str]:
        """Get all configured models by agent type.

        Returns:
            Dictionary mapping agent type to model name
        """
        return {
            agent_type: model_config.model
            for agent_type, model_config in cls.MODELS.items()
        }