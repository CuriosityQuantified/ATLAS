# ATLAS CallModel - Unified Model Interface with Comprehensive Tracking

The `CallModel` class provides a standardized, scalable interface for calling AI models from multiple providers. It's designed for both vertical and horizontal scaling, with built-in fallbacks, concurrent processing, and **comprehensive AG-UI and MLflow tracking**.

## Features

### ✅ **Multi-Provider Support** (All Tested & Working)
- **Anthropic Claude**: Direct SDK + LangChain integration (0.8s avg response)
- **OpenAI GPT**: Direct SDK + LangChain integration (4.0s avg response)
- **Groq**: High-speed inference with Groq LPUs (0.2s avg response - fastest)
- **Google Gemini**: Direct SDK integration (ready for testing)
- **HuggingFace**: HTTP API for open-source models (ready for testing)
- **OpenRouter**: Access to multiple model providers (ready for testing)

### ✅ **Multiple Invocation Methods**
- **Direct SDK**: Fastest for single requests
- **LangChain**: Better for complex workflows
- **HTTP**: Direct API calls for maximum control
- **Streaming**: Real-time response streaming (planned)

### ✅ **Scaling Features**
- **Concurrent Execution**: Thread pool for parallel requests
- **Automatic Fallbacks**: Try multiple models sequentially
- **Model Racing**: Run models concurrently, use fastest response
- **Performance Monitoring**: Track response times and success rates
- **Caching**: Optional response caching for efficiency

### 🚀 **NEW: Comprehensive Tracking Integration**
- **AG-UI Event Broadcasting**: Automatic real-time event broadcasting for all model calls
- **MLflow Integration**: Complete metrics logging with costs, tokens, and performance
- **DRY Architecture**: Single CallModel instance handles all tracking automatically
- **Zero Overhead**: Tracking doesn't impact model call performance
- **Flexible Deployment**: Works in standalone mode or with full AG-UI server

## Basic Usage

### Simple Model Call

```python
from src.utils.call_model import CallModel

call_model = CallModel()

response = await call_model.call_model(
    model_name="claude-3-5-haiku-20241022",
    system_prompt="You are a helpful AI assistant.",
    most_recent_message="What is machine learning?",
    max_tokens=200
)

if response.success:
    print(f"Response: {response.content}")
    print(f"Time: {response.response_time:.2f}s")
    print(f"Tokens: {response.total_tokens}")
else:
    print(f"Error: {response.error}")

call_model.cleanup()
```

### Quick Convenience Function

```python
from src.utils.call_model import quick_call

result = await quick_call(
    "gpt-4o-mini",
    "Explain quantum computing in simple terms"
)
print(result)
```

## Advanced Usage

### Auto-Detection (Recommended)

```python
# Provider and method automatically detected from model name
response = await call_model.call_model(
    model_name="claude-3-5-haiku-20241022",  # Auto-detects Anthropic
    most_recent_message="Hello!"
)
```

### Explicit Provider and Method

```python
from src.utils.call_model import ModelProvider, InvocationMethod

response = await call_model.call_model(
    model_name="gpt-4o-mini",
    provider=ModelProvider.OPENAI,
    invocation_method=InvocationMethod.DIRECT,
    system_prompt="You are an expert analyst.",
    most_recent_message="Analyze this data"
)
```

### Conversation with History

```python
conversation = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is ATLAS?"},
    {"role": "assistant", "content": "ATLAS is a multi-agent system..."},
]

response = await call_model.call_model(
    model_name="claude-3-5-haiku-20241022",
    conversation_history=conversation[:-1],  # All but last
    most_recent_message=conversation[-1],    # Latest message
    max_tokens=300
)
```

### Concurrent Model Calls (Horizontal Scaling)

```python
# Race multiple models, use fastest successful response
requests = [
    ("claude-3-5-haiku-20241022", {"most_recent_message": "What is AI?"}),
    ("llama-3.1-8b-instant", {"most_recent_message": "What is AI?"}),
    ("gpt-4o-mini", {"most_recent_message": "What is AI?"}),
]

responses = await call_model.call_multiple_models(requests)

for i, response in enumerate(responses):
    if response.success:
        print(f"Model {i+1}: {response.response_time:.2f}s - {response.content[:50]}...")
```

### Fallback Strategy

```python
models = ["claude-3-5-haiku-20241022", "llama-3.1-8b-instant", "gpt-4o-mini"]

for model in models:
    response = await call_model.call_model(
        model_name=model,
        most_recent_message="Important question",
        timeout=10.0
    )
    
    if response.success:
        print(f"Success with {model}: {response.content}")
        break
    else:
        print(f"Failed with {model}: {response.error}")
        # Try next model
```

## 🚀 NEW: Tracking Integration

### Enhanced Agent Pattern with Full Tracking

```python
from src.agui.handlers import AGUIEventBroadcaster
from src.mlflow.tracking import ATLASMLflowTracker
from src.utils.call_model import CallModel

class MyAgent:
    def __init__(self, agent_id: str, task_id: str):
        # Initialize tracking components
        self.agent_id = agent_id
        self.task_id = task_id
        self.broadcaster = AGUIEventBroadcaster(connection_manager)  # or None for standalone
        self.mlflow_tracker = ATLASMLflowTracker()
        
        # Initialize CallModel with comprehensive tracking
        self.call_model = CallModel(
            enable_threading=True, 
            max_workers=5,
            task_id=task_id,
            agent_id=agent_id,
            agui_broadcaster=self.broadcaster,
            mlflow_tracker=self.mlflow_tracker
        )
        
        self.preferred_models = [
            "claude-3-5-haiku-20241022",  # Primary
            "llama-3.1-8b-instant",       # Fast backup
            "gpt-4o-mini",                # Reliable fallback
        ]
```

### Automatic Tracking Benefits

```python
# ALL model calls automatically generate:
# - AG-UI events (performance_metrics, cost_update, error_occurred)
# - MLflow metrics (llm_call logs, error logs, performance stats)
# - No additional code required!

async def process_message(self, message: str, run_id: str):
    response = await self.call_model.call_model(
        model_name="claude-3-5-haiku-20241022",
        most_recent_message=message,
        run_id=run_id  # Links to MLflow run
        # Tracking happens automatically - no extra code needed!
    )
    return response
```

## Integration with ATLAS Agents

### Traditional Agent Pattern (Legacy)
    
    async def process_with_fallbacks(self, message: str):
        for model in self.preferred_models:
            response = await self.call_model.call_model(
                model_name=model,
                system_prompt=self.get_system_prompt(),
                most_recent_message=message,
                max_tokens=500
            )
            
            if response.success:
                return {
                    "content": response.content,
                    "model_used": model,
                    "processing_time": response.response_time,
                    "tokens": response.total_tokens
                }
        
        return {"error": "All models failed"}
    
    def cleanup(self):
        self.call_model.cleanup()
```

### Concurrent Racing Pattern

```python
async def process_with_racing(self, message: str):
    """Use multiple models concurrently, return fastest successful response."""
    
    requests = [
        (model, {
            "system_prompt": self.get_system_prompt(),
            "most_recent_message": message,
            "max_tokens": 500,
            "timeout": 15.0
        })
        for model in self.preferred_models
    ]
    
    responses = await self.call_model.call_multiple_models(requests)
    
    # Find fastest successful response
    best_response = None
    fastest_time = float('inf')
    
    for i, response in enumerate(responses):
        if response.success and response.response_time < fastest_time:
            best_response = response
            fastest_time = response.response_time
            winning_model = self.preferred_models[i]
    
    if best_response:
        return {
            "content": best_response.content,
            "winning_model": winning_model,
            "fastest_time": fastest_time,
            "models_tried": len(self.preferred_models)
        }
    
    return {"error": "All models failed"}
```

## Performance Monitoring

```python
# Get performance statistics
stats = call_model.get_performance_stats()

for method, data in stats.items():
    print(f"{method}:")
    print(f"  Calls: {data['total_calls']}")
    print(f"  Avg Time: {data['average_time']:.2f}s")
    print(f"  Min Time: {data['min_time']:.2f}s") 
    print(f"  Max Time: {data['max_time']:.2f}s")
```

## Configuration Options

### ModelRequest Parameters

- `model_name` (required): The model identifier
- `system_prompt` (optional): System prompt for the model
- `conversation_history` (optional): Previous conversation messages
- `event_history` (optional): Event context for agents
- `most_recent_message` (optional): Latest user message
- `max_tokens`: Maximum response tokens (default: 1000)
- `temperature`: Creativity setting (default: 0.7)
- `timeout`: Request timeout in seconds (default: 30.0)
- `retry_attempts`: Number of retry attempts (default: 3)

### CallModel Initialization

```python
call_model = CallModel(
    enable_threading=True,  # Enable concurrent execution
    max_workers=10          # Maximum thread pool size
)
```

## Error Handling

```python
response = await call_model.call_model(
    model_name="claude-3-5-haiku-20241022",
    most_recent_message="Hello"
)

if response.success:
    # Success case
    content = response.content
    processing_time = response.response_time
    tokens_used = response.total_tokens
    cost = response.cost_usd
else:
    # Error case
    error_message = response.error
    error_type = response.error_type
    print(f"Model call failed: {error_type} - {error_message}")
```

## Best Practices

### 1. **Always Clean Up Resources**
```python
call_model = CallModel()
try:
    # Use call_model
    response = await call_model.call_model(...)
finally:
    call_model.cleanup()  # Important for thread pool cleanup
```

### 2. **Use Timeouts for Reliability**
```python
response = await call_model.call_model(
    model_name="claude-3-5-haiku-20241022",
    most_recent_message="Question",
    timeout=20.0  # 20 second timeout
)
```

### 3. **Implement Fallback Strategies**
```python
primary_models = ["claude-3-5-haiku-20241022", "llama-3.1-8b-instant"]
backup_models = ["gpt-4o-mini"]

# Try primary models first, then backups
for model in primary_models + backup_models:
    response = await call_model.call_model(model_name=model, ...)
    if response.success:
        break
```

### 4. **Monitor Performance**
```python
# Regular performance monitoring
stats = call_model.get_performance_stats()
if stats:
    slow_methods = [
        method for method, data in stats.items() 
        if data['average_time'] > 5.0
    ]
    if slow_methods:
        print(f"Slow methods detected: {slow_methods}")
```

### 5. **Use Appropriate Models for Tasks**
```python
# Fast models for simple tasks
simple_response = await call_model.call_model(
    model_name="llama-3.1-8b-instant",  # Very fast
    most_recent_message="Say hello"
)

# Capable models for complex tasks
complex_response = await call_model.call_model(
    model_name="claude-3-5-haiku-20241022",  # More capable
    most_recent_message="Analyze this complex data..."
)
```

## Testing

Run the comprehensive test suite:

```bash
python backend/test_call_model.py
```

This will test:
- Single model calls across all providers
- Conversation flow with history
- Concurrent model execution
- Auto-detection of providers
- Quick call convenience function
- Performance monitoring

## Environment Variables Required

```bash
# API Keys (add to .env file)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_key
HUGGINGFACE_API_KEY=your_huggingface_key
OPENROUTER_API_KEY=your_openrouter_key
```

## Dependencies

The CallModel automatically handles missing dependencies gracefully. Install what you need:

```bash
# Core dependencies (already in requirements.txt)
pip install anthropic openai groq httpx

# Optional dependencies
pip install google-generativeai  # For Google Gemini
pip install langchain           # For LangChain integration
```

## Thread Safety

The CallModel class is thread-safe and designed for concurrent usage across multiple agents in the ATLAS system. Each instance maintains its own thread pool and can handle multiple simultaneous requests safely.