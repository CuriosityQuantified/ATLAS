#!/usr/bin/env python3
"""
Download and cache the Osmosis-Structure-0.6B model
"""

import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Set environment variable to use HF token
os.environ["HF_TOKEN"] = os.getenv("HUGGINGFACE_API_KEY", "")

print("🤖 Downloading Osmosis-Structure-0.6B model...")
print("This may take several minutes depending on your internet connection.")
print("-" * 60)

model_name = "osmosis-ai/Osmosis-Structure-0.6B"

# Download tokenizer
print("\n📥 Downloading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    trust_remote_code=True,
    token=True  # Use the new parameter name
)
print("✅ Tokenizer downloaded successfully!")

# Download model
print("\n📥 Downloading model weights (this is the large part)...")
print("Model size is approximately 1.2GB")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🖥️  Target device: {device}")

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None,
    trust_remote_code=True,
    token=True  # Use the new parameter name
)

print("✅ Model downloaded successfully!")

# Get cache directory
from transformers import file_utils
cache_dir = file_utils.default_cache_path
print(f"\n📁 Model cached in: {cache_dir}")

# Test the model with a simple prompt
print("\n🧪 Testing model with a simple prompt...")
test_prompt = "Convert to JSON: The user wants to research renewable energy"
inputs = tokenizer(test_prompt, return_tensors="pt", truncation=True, max_length=512)

# Move inputs to device if using CUDA
if torch.cuda.is_available():
    inputs = {k: v.to(device) for k, v in inputs.items()}

# Generate a short response to verify model works
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        temperature=0.1,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"Model response: {response[:200]}...")

print("\n✅ Model is ready to use!")
print("You can now run the structure service tests.")