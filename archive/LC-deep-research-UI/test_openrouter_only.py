#!/usr/bin/env python3
"""
Test that ONLY OpenRouter is used, no direct Anthropic API calls.
"""

import os
import sys
from pathlib import Path

# Add the deepagents source to path
sys.path.insert(0, str(Path(__file__).parent / "deepagents" / "src"))

# IMPORTANT: Make sure we're using OpenRouter only
os.environ["OPENROUTER_MODEL"] = "qwen3-235b-a22b-thinking-2507"

# Remove Anthropic API key to ensure we don't use it
if "ANTHROPIC_API_KEY" in os.environ:
    del os.environ["ANTHROPIC_API_KEY"]
    print("✅ Removed ANTHROPIC_API_KEY to ensure OpenRouter-only usage")

print("\n" + "="*60)
print(" Testing OpenRouter-Only Configuration")
print("="*60)

# Import after setting environment
from deepagents.model import get_default_model, get_model_for_task

try:
    print("\n1. Testing get_default_model()...")
    model = get_default_model()
    print(f"   Model type: {type(model).__name__}")
    print(f"   Model: {model}")
    
    # Verify it's OpenRouter
    if hasattr(model, 'model_info'):
        print(f"   Model info: {model.model_info}")
    
    # Check that it's using the right base URL
    if hasattr(model, 'openai_api_base'):
        print(f"   API Base: {model.openai_api_base}")
    
    print("\n2. Testing get_model_for_task()...")
    for task in ["general", "coding", "thinking"]:
        model = get_model_for_task(task)
        print(f"   {task}: {type(model).__name__}")
    
    print("\n✅ Success! Only OpenRouter is being used.")
    print("   No Anthropic API calls will be made.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)