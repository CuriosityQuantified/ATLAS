# Models with dedicated thinking/reasoning modes that cannot be disabled
thinking_models = [
    "claude-opus-4-20250514-thinking-16k",        # Claude thinking mode with 16k context
    "claude-sonnet-4-20250514-thinking-32k",       # Claude thinking mode with 32k context
    "claude-3-7-sonnet-20250219-thinking-32k",     # Claude 3.7 thinking mode
    "qwen3-235b-a22b-thinking-2507",               # Qwen3 dedicated thinking model
    "deepseek-r1-0528",                             # DeepSeek reasoning model with CoT
    "deepseek-r1",                                  # DeepSeek R1 reasoning model
]

# Models that support optional/hybrid thinking modes (can be turned on/off)
hybrid_models = [
    "claude-opus-4-1-20250805",                    # Claude Opus 4.1 with hybrid reasoning
    "claude-opus-4-20250514",                      # Claude Opus 4 with extended thinking
    "gemini-2.5-pro",                               # Gemini 2.5 Pro with Deep Think mode
    "gemini-2.5-flash",                             # First fully hybrid reasoning model
    "hunyuan-turbos-20250416",                     # Adaptive long-short CoT mechanism
]

# Standard models without dedicated thinking/reasoning capabilities
non_thinking_models = [
    "claude-sonnet-4-20250514",                    # Standard Claude Sonnet 4
    "qwen3-235b-a22b-instruct-2507",              # Qwen3 standard instruct model
    "qwen3-235b-a22b-no-thinking",                # Qwen3 explicitly non-thinking variant
    "qwen3-30b-a3b-instruct-2507",                # Smaller Qwen3 instruct model
    "qwen3-coder-480b-a35b-instruct",             # Qwen3 coding-focused model
    "kimi-k2-0711-preview",                        # Kimi K2 standard model
    "deepseek-v3-0324",                            # DeepSeek V3 standard model
    "glm-4.5",                                     # GLM-4.5 standard model
    "glm-4.5-air",                                 # GLM-4.5 Air variant
    "mistral-medium-2505",                         # Mistral Medium standard model
]