#!/usr/bin/env python3
"""
ATLAS Unified Model Calling Interface

Provides standardized, scalable interfaces for all AI model providers.
Supports multiple invocation methods per provider for optimal performance and flexibility.
"""

import asyncio
import time
import os
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor

# Import model providers
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

try:
    import groq
except ImportError:
    groq = None

try:
    from langchain.chat_models import ChatOpenAI, ChatAnthropic
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
except ImportError:
    ChatOpenAI = ChatAnthropic = HumanMessage = SystemMessage = AIMessage = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported model providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROQ = "groq"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"


class InvocationMethod(Enum):
    """Different invocation methods for providers."""
    DIRECT = "direct"           # Direct SDK calls
    LANGCHAIN = "langchain"     # LangChain integration
    HTTP = "http"              # Direct HTTP calls
    STREAMING = "streaming"     # Streaming responses


@dataclass
class ModelRequest:
    """Standardized model request structure."""
    model_name: str                                    # Required
    system_prompt: Optional[Any] = None               # Optional
    conversation_history: Optional[Any] = None        # Optional
    event_history: Optional[Any] = None              # Optional
    most_recent_message: Optional[Any] = None        # Optional
    
    # Additional parameters
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    
    # Scaling and performance options
    timeout: Optional[float] = 30.0
    retry_attempts: int = 3
    enable_caching: bool = True
    enable_streaming: bool = False


@dataclass
class ModelResponse:
    """Standardized model response structure."""
    success: bool
    content: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    invocation_method: Optional[str] = None
    
    # Performance metrics
    response_time: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    
    # Error information
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # Raw response for advanced usage
    raw_response: Optional[Any] = None


class CallModel:
    """
    Unified model calling interface with multiple invocation methods per provider.
    Designed for vertical and horizontal scaling with AG-UI and MLflow integration.
    """
    
    def __init__(
        self, 
        enable_threading: bool = True, 
        max_workers: int = 10,
        task_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        agui_broadcaster = None,
        mlflow_tracker = None
    ):
        """
        Initialize the CallModel with scaling configurations and tracking.
        
        Args:
            enable_threading: Enable thread pool for concurrent requests
            max_workers: Maximum number of worker threads
            task_id: Task ID for AG-UI event broadcasting
            agent_id: Agent ID for tracking and attribution
            agui_broadcaster: AG-UI event broadcaster instance
            mlflow_tracker: MLflow tracking instance
        """
        self.enable_threading = enable_threading
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers) if enable_threading else None
        
        # Tracking configuration
        self.task_id = task_id
        self.agent_id = agent_id
        self.agui_broadcaster = agui_broadcaster
        self.mlflow_tracker = mlflow_tracker
        
        # Initialize provider clients (lazy loading)
        self._anthropic_client = None
        self._openai_client = None
        self._groq_client = None
        self._langchain_openai = None
        self._langchain_anthropic = None
        
        # Performance tracking
        self._request_cache: Dict[str, ModelResponse] = {}
        self._performance_stats: Dict[str, List[float]] = {}
    
    async def _track_model_call(
        self,
        request: ModelRequest,
        response: ModelResponse,
        start_time: float,
        run_id: Optional[str] = None
    ) -> None:
        """
        Track model call with both AG-UI events and MLflow metrics.
        
        Args:
            request: The original model request
            response: The model response
            start_time: When the call started (for latency calculation)
            run_id: MLflow run ID for tracking
        """
        try:
            # Track performance statistics
            provider_method = f"{response.provider}_{response.invocation_method}"
            if provider_method not in self._performance_stats:
                self._performance_stats[provider_method] = []
            self._performance_stats[provider_method].append(response.response_time or 0.0)
            
            # AG-UI Event Broadcasting
            if self.agui_broadcaster and self.task_id:
                # Broadcast model call metrics
                if response.success:
                    from ..agui.events import AGUIEventFactory
                    
                    # Cost update event
                    if response.cost_usd and response.total_tokens:
                        cost_event = AGUIEventFactory.cost_update(
                            task_id=self.task_id,
                            agent_id=self.agent_id or "call_model",
                            cost_usd=response.cost_usd,
                            token_count=response.total_tokens,
                            model_name=response.model_name or request.model_name
                        )
                        await self.agui_broadcaster._broadcast_event(cost_event)
                    
                    # Performance metrics event
                    metrics = {
                        "model_name": response.model_name or request.model_name,
                        "provider": response.provider,
                        "invocation_method": response.invocation_method,
                        "response_time_ms": (response.response_time or 0.0) * 1000,
                        "input_tokens": response.input_tokens or 0,
                        "output_tokens": response.output_tokens or 0,
                        "total_tokens": response.total_tokens or 0,
                        "cost_usd": response.cost_usd or 0.0,
                        "success": True
                    }
                    
                    perf_event = AGUIEventFactory.performance_metrics_update(
                        task_id=self.task_id,
                        agent_id=self.agent_id or "call_model",
                        metrics=metrics
                    )
                    await self.agui_broadcaster._broadcast_event(perf_event)
                    
                else:
                    # Error event
                    from ..agui.events import AGUIEventFactory
                    error_event = AGUIEventFactory.error_occurred(
                        task_id=self.task_id,
                        agent_id=self.agent_id or "call_model",
                        error_type=response.error_type or "ModelCallError",
                        error_message=response.error or "Unknown error",
                        traceback=""
                    )
                    await self.agui_broadcaster._broadcast_event(error_event)
            
            # MLflow Tracking
            if self.mlflow_tracker and run_id:
                if response.success:
                    self.mlflow_tracker.log_llm_call(
                        run_id=run_id,
                        model_provider=response.provider or "unknown",
                        model_name=response.model_name or request.model_name,
                        input_tokens=response.input_tokens or 0,
                        output_tokens=response.output_tokens or 0,
                        total_cost=response.cost_usd or 0.0,
                        latency=response.response_time or 0.0,
                        success=True
                    )
                else:
                    self.mlflow_tracker.log_error(
                        run_id=run_id,
                        error_type=response.error_type or "ModelCallError",
                        error_message=response.error or "Unknown error",
                        error_context={
                            "model_name": request.model_name,
                            "provider": response.provider,
                            "invocation_method": response.invocation_method
                        }
                    )
        
        except Exception as e:
            logger.error(f"Error in tracking model call: {e}")
            # Don't let tracking errors break the main flow
    
    # ===============================
    # ANTHROPIC PROVIDER METHODS
    # ===============================
    
    def _get_anthropic_client(self) -> anthropic.Anthropic:
        """Get or create Anthropic client (lazy loading)."""
        if self._anthropic_client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self._anthropic_client = anthropic.Anthropic(api_key=api_key)
        return self._anthropic_client
    
    async def call_anthropic_direct(self, request: ModelRequest) -> ModelResponse:
        """Direct Anthropic SDK call - fastest for single requests."""
        if not anthropic:
            return ModelResponse(
                success=False, 
                error="anthropic package not installed",
                error_type="ImportError"
            )
        
        try:
            start_time = time.time()
            client = self._get_anthropic_client()
            
            # Build messages
            messages = []
            
            # Add conversation history
            if request.conversation_history:
                if isinstance(request.conversation_history, list):
                    for msg in request.conversation_history:
                        if isinstance(msg, dict):
                            messages.append(msg)
                        else:
                            messages.append({"role": "user", "content": str(msg)})
            
            # Add most recent message
            if request.most_recent_message:
                if isinstance(request.most_recent_message, dict):
                    messages.append(request.most_recent_message)
                else:
                    messages.append({"role": "user", "content": str(request.most_recent_message)})
            
            # If no messages, create a default one
            if not messages:
                messages = [{"role": "user", "content": "Hello"}]
            
            # Prepare request parameters
            call_params = {
                "model": request.model_name,
                "max_tokens": request.max_tokens or 1000,
                "messages": messages
            }
            
            if request.system_prompt:
                call_params["system"] = str(request.system_prompt)
            
            if request.temperature is not None:
                call_params["temperature"] = request.temperature
            
            if request.top_p is not None:
                call_params["top_p"] = request.top_p
            
            if request.stop_sequences:
                call_params["stop_sequences"] = request.stop_sequences
            
            # Make API call
            response = client.messages.create(**call_params)
            
            processing_time = time.time() - start_time
            
            # Extract response data
            content = response.content[0].text if response.content else ""
            input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else 0
            output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else 0
            
            return ModelResponse(
                success=True,
                content=content,
                provider="anthropic",
                model_name=request.model_name,
                invocation_method="direct",
                response_time=processing_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                raw_response=response
            )
            
        except Exception as e:
            return ModelResponse(
                success=False,
                provider="anthropic",
                model_name=request.model_name,
                invocation_method="direct",
                error=str(e),
                error_type=type(e).__name__
            )
    
    async def call_anthropic_langchain(self, request: ModelRequest) -> ModelResponse:
        """LangChain Anthropic call - better for complex workflows."""
        if not ChatAnthropic:
            return ModelResponse(
                success=False,
                error="langchain package not installed",
                error_type="ImportError"
            )
        
        try:
            start_time = time.time()
            
            if self._langchain_anthropic is None:
                self._langchain_anthropic = ChatAnthropic(
                    model=request.model_name,
                    temperature=request.temperature or 0.7,
                    max_tokens=request.max_tokens or 1000
                )
            
            # Build message chain
            messages = []
            
            if request.system_prompt:
                messages.append(SystemMessage(content=str(request.system_prompt)))
            
            if request.conversation_history:
                if isinstance(request.conversation_history, list):
                    for msg in request.conversation_history:
                        if isinstance(msg, dict):
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            if role == "system":
                                messages.append(SystemMessage(content=content))
                            elif role == "assistant":
                                messages.append(AIMessage(content=content))
                            else:
                                messages.append(HumanMessage(content=content))
                        else:
                            messages.append(HumanMessage(content=str(msg)))
            
            if request.most_recent_message:
                if isinstance(request.most_recent_message, dict):
                    content = request.most_recent_message.get("content", "")
                else:
                    content = str(request.most_recent_message)
                messages.append(HumanMessage(content=content))
            
            # Make call
            response = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                lambda: self._langchain_anthropic(messages)
            )
            
            processing_time = time.time() - start_time
            
            return ModelResponse(
                success=True,
                content=response.content,
                provider="anthropic",
                model_name=request.model_name,
                invocation_method="langchain",
                response_time=processing_time,
                raw_response=response
            )
            
        except Exception as e:
            return ModelResponse(
                success=False,
                provider="anthropic",
                model_name=request.model_name,
                invocation_method="langchain",
                error=str(e),
                error_type=type(e).__name__
            )
    
    # ===============================
    # OPENAI PROVIDER METHODS
    # ===============================
    
    def _get_openai_client(self) -> openai.OpenAI:
        """Get or create OpenAI client (lazy loading)."""
        if self._openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self._openai_client = openai.OpenAI(api_key=api_key)
        return self._openai_client
    
    async def call_openai_direct(self, request: ModelRequest) -> ModelResponse:
        """Direct OpenAI SDK call - fastest for single requests."""
        if not openai:
            return ModelResponse(
                success=False,
                error="openai package not installed",
                error_type="ImportError"
            )
        
        try:
            start_time = time.time()
            client = self._get_openai_client()
            
            # Build messages
            messages = []
            
            if request.system_prompt:
                messages.append({"role": "system", "content": str(request.system_prompt)})
            
            if request.conversation_history:
                if isinstance(request.conversation_history, list):
                    for msg in request.conversation_history:
                        if isinstance(msg, dict):
                            messages.append(msg)
                        else:
                            messages.append({"role": "user", "content": str(msg)})
            
            if request.most_recent_message:
                if isinstance(request.most_recent_message, dict):
                    messages.append(request.most_recent_message)
                else:
                    messages.append({"role": "user", "content": str(request.most_recent_message)})
            
            if not messages:
                messages = [{"role": "user", "content": "Hello"}]
            
            # Prepare request parameters
            call_params = {
                "model": request.model_name,
                "messages": messages,
                "max_tokens": request.max_tokens or 1000,
                "temperature": request.temperature or 0.7
            }
            
            if request.top_p is not None:
                call_params["top_p"] = request.top_p
            
            if request.frequency_penalty is not None:
                call_params["frequency_penalty"] = request.frequency_penalty
            
            if request.presence_penalty is not None:
                call_params["presence_penalty"] = request.presence_penalty
            
            if request.stop_sequences:
                call_params["stop"] = request.stop_sequences
            
            # Make API call
            response = client.chat.completions.create(**call_params)
            
            processing_time = time.time() - start_time
            
            # Extract response data
            content = response.choices[0].message.content if response.choices else ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            
            return ModelResponse(
                success=True,
                content=content,
                provider="openai",
                model_name=request.model_name,
                invocation_method="direct",
                response_time=processing_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                raw_response=response
            )
            
        except Exception as e:
            return ModelResponse(
                success=False,
                provider="openai",
                model_name=request.model_name,
                invocation_method="direct",
                error=str(e),
                error_type=type(e).__name__
            )
    
    async def call_openai_langchain(self, request: ModelRequest) -> ModelResponse:
        """LangChain OpenAI call - better for complex workflows."""
        if not ChatOpenAI:
            return ModelResponse(
                success=False,
                error="langchain package not installed",
                error_type="ImportError"
            )
        
        try:
            start_time = time.time()
            
            if self._langchain_openai is None:
                self._langchain_openai = ChatOpenAI(
                    model=request.model_name,
                    temperature=request.temperature or 0.7,
                    max_tokens=request.max_tokens or 1000
                )
            
            # Build message chain (same as Anthropic LangChain)
            messages = []
            
            if request.system_prompt:
                messages.append(SystemMessage(content=str(request.system_prompt)))
            
            if request.conversation_history:
                if isinstance(request.conversation_history, list):
                    for msg in request.conversation_history:
                        if isinstance(msg, dict):
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            if role == "system":
                                messages.append(SystemMessage(content=content))
                            elif role == "assistant":
                                messages.append(AIMessage(content=content))
                            else:
                                messages.append(HumanMessage(content=content))
                        else:
                            messages.append(HumanMessage(content=str(msg)))
            
            if request.most_recent_message:
                if isinstance(request.most_recent_message, dict):
                    content = request.most_recent_message.get("content", "")
                else:
                    content = str(request.most_recent_message)
                messages.append(HumanMessage(content=content))
            
            # Make call
            response = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                lambda: self._langchain_openai(messages)
            )
            
            processing_time = time.time() - start_time
            
            return ModelResponse(
                success=True,
                content=response.content,
                provider="openai",
                model_name=request.model_name,
                invocation_method="langchain",
                response_time=processing_time,
                raw_response=response
            )
            
        except Exception as e:
            return ModelResponse(
                success=False,
                provider="openai",
                model_name=request.model_name,
                invocation_method="langchain",
                error=str(e),
                error_type=type(e).__name__
            )
    
    # ===============================
    # GROQ PROVIDER METHODS
    # ===============================
    
    def _get_groq_client(self) -> groq.Groq:
        """Get or create Groq client (lazy loading)."""
        if self._groq_client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            self._groq_client = groq.Groq(api_key=api_key)
        return self._groq_client
    
    async def call_groq_direct(self, request: ModelRequest) -> ModelResponse:
        """Direct Groq SDK call - optimized for speed."""
        if not groq:
            return ModelResponse(
                success=False,
                error="groq package not installed",
                error_type="ImportError"
            )
        
        try:
            start_time = time.time()
            client = self._get_groq_client()
            
            # Build messages (same structure as OpenAI)
            messages = []
            
            if request.system_prompt:
                messages.append({"role": "system", "content": str(request.system_prompt)})
            
            if request.conversation_history:
                if isinstance(request.conversation_history, list):
                    for msg in request.conversation_history:
                        if isinstance(msg, dict):
                            messages.append(msg)
                        else:
                            messages.append({"role": "user", "content": str(msg)})
            
            if request.most_recent_message:
                if isinstance(request.most_recent_message, dict):
                    messages.append(request.most_recent_message)
                else:
                    messages.append({"role": "user", "content": str(request.most_recent_message)})
            
            if not messages:
                messages = [{"role": "user", "content": "Hello"}]
            
            # Make API call
            response = client.chat.completions.create(
                model=request.model_name,
                messages=messages,
                max_tokens=request.max_tokens or 1000,
                temperature=request.temperature or 0.7,
                stop=request.stop_sequences
            )
            
            processing_time = time.time() - start_time
            
            # Extract response data
            content = response.choices[0].message.content if response.choices else ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            
            return ModelResponse(
                success=True,
                content=content,
                provider="groq",
                model_name=request.model_name,
                invocation_method="direct",
                response_time=processing_time,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                raw_response=response
            )
            
        except Exception as e:
            return ModelResponse(
                success=False,
                provider="groq",
                model_name=request.model_name,
                invocation_method="direct",
                error=str(e),
                error_type=type(e).__name__
            )
    
    # ===============================
    # GOOGLE PROVIDER METHODS
    # ===============================
    
    async def call_google_direct(self, request: ModelRequest) -> ModelResponse:
        """Direct Google Gemini SDK call."""
        if not genai:
            return ModelResponse(
                success=False,
                error="google-generativeai package not installed",
                error_type="ImportError"
            )
        
        try:
            start_time = time.time()
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            
            genai.configure(api_key=api_key)
            
            # Create model instance
            model = genai.GenerativeModel(request.model_name)
            
            # Build prompt from all sources
            prompt_parts = []
            
            if request.system_prompt:
                prompt_parts.append(f"System: {request.system_prompt}")
            
            if request.conversation_history:
                if isinstance(request.conversation_history, list):
                    for msg in request.conversation_history:
                        if isinstance(msg, dict):
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            prompt_parts.append(f"{role.title()}: {content}")
                        else:
                            prompt_parts.append(f"User: {msg}")
            
            if request.most_recent_message:
                if isinstance(request.most_recent_message, dict):
                    content = request.most_recent_message.get("content", "")
                else:
                    content = str(request.most_recent_message)
                prompt_parts.append(f"User: {content}")
            
            prompt = "\n".join(prompt_parts) if prompt_parts else "Hello"
            
            # Make API call
            response = model.generate_content(prompt)
            
            processing_time = time.time() - start_time
            
            return ModelResponse(
                success=True,
                content=response.text,
                provider="google",
                model_name=request.model_name,
                invocation_method="direct",
                response_time=processing_time,
                raw_response=response
            )
            
        except Exception as e:
            return ModelResponse(
                success=False,
                provider="google",
                model_name=request.model_name,
                invocation_method="direct",
                error=str(e),
                error_type=type(e).__name__
            )
    
    # ===============================
    # HUGGINGFACE PROVIDER METHODS
    # ===============================
    
    async def call_huggingface_http(self, request: ModelRequest) -> ModelResponse:
        """HTTP call to HuggingFace Inference API."""
        if not httpx:
            return ModelResponse(
                success=False,
                error="httpx package not installed",
                error_type="ImportError"
            )
        
        try:
            start_time = time.time()
            
            api_key = os.getenv("HUGGINGFACE_API_KEY")
            if not api_key:
                raise ValueError("HUGGINGFACE_API_KEY not found in environment")
            
            # Build input text
            input_parts = []
            
            if request.system_prompt:
                input_parts.append(f"System: {request.system_prompt}")
            
            if request.conversation_history:
                if isinstance(request.conversation_history, list):
                    for msg in request.conversation_history:
                        if isinstance(msg, dict):
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            input_parts.append(f"{role.title()}: {content}")
                        else:
                            input_parts.append(f"User: {msg}")
            
            if request.most_recent_message:
                if isinstance(request.most_recent_message, dict):
                    content = request.most_recent_message.get("content", "")
                else:
                    content = str(request.most_recent_message)
                input_parts.append(f"User: {content}")
            
            input_text = "\n".join(input_parts) if input_parts else "Hello"
            
            # Make HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{request.model_name}",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "inputs": input_text,
                        "parameters": {
                            "max_new_tokens": request.max_tokens or 1000,
                            "temperature": request.temperature or 0.7,
                            "return_full_text": False
                        }
                    },
                    timeout=request.timeout or 30.0
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list) and len(data) > 0:
                    content = data[0].get("generated_text", "")
                elif isinstance(data, dict):
                    content = data.get("generated_text", str(data))
                else:
                    content = str(data)
                
                return ModelResponse(
                    success=True,
                    content=content,
                    provider="huggingface",
                    model_name=request.model_name,
                    invocation_method="http",
                    response_time=processing_time,
                    raw_response=data
                )
            else:
                return ModelResponse(
                    success=False,
                    provider="huggingface",
                    model_name=request.model_name,
                    invocation_method="http",
                    error=f"HTTP {response.status_code}: {response.text}",
                    error_type="HTTPError"
                )
            
        except Exception as e:
            return ModelResponse(
                success=False,
                provider="huggingface",
                model_name=request.model_name,
                invocation_method="http",
                error=str(e),
                error_type=type(e).__name__
            )
    
    # ===============================
    # OPENROUTER PROVIDER METHODS
    # ===============================
    
    async def call_openrouter_http(self, request: ModelRequest) -> ModelResponse:
        """HTTP call to OpenRouter API."""
        if not httpx:
            return ModelResponse(
                success=False,
                error="httpx package not installed",
                error_type="ImportError"
            )
        
        try:
            start_time = time.time()
            
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY not found in environment")
            
            # Build messages (OpenAI format)
            messages = []
            
            if request.system_prompt:
                messages.append({"role": "system", "content": str(request.system_prompt)})
            
            if request.conversation_history:
                if isinstance(request.conversation_history, list):
                    for msg in request.conversation_history:
                        if isinstance(msg, dict):
                            messages.append(msg)
                        else:
                            messages.append({"role": "user", "content": str(msg)})
            
            if request.most_recent_message:
                if isinstance(request.most_recent_message, dict):
                    messages.append(request.most_recent_message)
                else:
                    messages.append({"role": "user", "content": str(request.most_recent_message)})
            
            if not messages:
                messages = [{"role": "user", "content": "Hello"}]
            
            # Make HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://atlas.local",
                        "X-Title": "ATLAS Multi-Agent System"
                    },
                    json={
                        "model": request.model_name,
                        "messages": messages,
                        "max_tokens": request.max_tokens or 1000,
                        "temperature": request.temperature or 0.7,
                        "stop": request.stop_sequences
                    },
                    timeout=request.timeout or 30.0
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
                
                return ModelResponse(
                    success=True,
                    content=content,
                    provider="openrouter",
                    model_name=request.model_name,
                    invocation_method="http",
                    response_time=processing_time,
                    raw_response=data
                )
            else:
                return ModelResponse(
                    success=False,
                    provider="openrouter",
                    model_name=request.model_name,
                    invocation_method="http",
                    error=f"HTTP {response.status_code}: {response.text}",
                    error_type="HTTPError"
                )
            
        except Exception as e:
            return ModelResponse(
                success=False,
                provider="openrouter",
                model_name=request.model_name,
                invocation_method="http",
                error=str(e),
                error_type=type(e).__name__
            )
    
    # ===============================
    # UNIFIED INTERFACE METHODS
    # ===============================
    
    async def call_model(
        self,
        model_name: str,
        provider: Optional[ModelProvider] = None,
        invocation_method: Optional[InvocationMethod] = None,
        system_prompt: Optional[Any] = None,
        conversation_history: Optional[Any] = None,
        event_history: Optional[Any] = None,
        most_recent_message: Optional[Any] = None,
        run_id: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Unified interface to call any model with any provider.
        Auto-detects provider and uses best invocation method if not specified.
        Includes comprehensive AG-UI and MLflow tracking.
        
        Args:
            model_name: The model to call (required)
            provider: Provider to use (auto-detected if None)
            invocation_method: Method to use (auto-selected if None)
            system_prompt: System prompt for the model
            conversation_history: Previous conversation context
            event_history: Event context for agents
            most_recent_message: Latest user message
            run_id: MLflow run ID for tracking
            **kwargs: Additional parameters for the model
        """
        
        start_time = time.time()
        
        # Create request object
        request = ModelRequest(
            model_name=model_name,
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            event_history=event_history,
            most_recent_message=most_recent_message,
            **kwargs
        )
        
        # Auto-detect provider if not specified
        if provider is None:
            provider = self._detect_provider(model_name)
        
        # Auto-select best invocation method if not specified
        if invocation_method is None:
            invocation_method = self._select_best_method(provider)
        
        # Route to appropriate method
        method_map = {
            (ModelProvider.ANTHROPIC, InvocationMethod.DIRECT): self.call_anthropic_direct,
            (ModelProvider.ANTHROPIC, InvocationMethod.LANGCHAIN): self.call_anthropic_langchain,
            (ModelProvider.OPENAI, InvocationMethod.DIRECT): self.call_openai_direct,
            (ModelProvider.OPENAI, InvocationMethod.LANGCHAIN): self.call_openai_langchain,
            (ModelProvider.GROQ, InvocationMethod.DIRECT): self.call_groq_direct,
            (ModelProvider.GOOGLE, InvocationMethod.DIRECT): self.call_google_direct,
            (ModelProvider.HUGGINGFACE, InvocationMethod.HTTP): self.call_huggingface_http,
            (ModelProvider.OPENROUTER, InvocationMethod.HTTP): self.call_openrouter_http,
        }
        
        method = method_map.get((provider, invocation_method))
        if method:
            response = await method(request)
            
            # Track the call with AG-UI and MLflow
            await self._track_model_call(request, response, start_time, run_id)
            
            return response
        else:
            error_response = ModelResponse(
                success=False,
                error=f"Unsupported combination: {provider.value} with {invocation_method.value}",
                error_type="UnsupportedConfiguration",
                provider=provider.value,
                model_name=model_name,
                invocation_method=invocation_method.value,
                response_time=time.time() - start_time
            )
            
            # Track the error
            await self._track_model_call(request, error_response, start_time, run_id)
            
            return error_response
    
    async def call_multiple_models(
        self,
        requests: List[Tuple[str, Dict[str, Any]]],
        run_id: Optional[str] = None
    ) -> List[ModelResponse]:
        """
        Call multiple models concurrently for horizontal scaling.
        
        Args:
            requests: List of (model_name, kwargs) tuples
            run_id: MLflow run ID for tracking all calls
        
        Returns:
            List of ModelResponse objects in same order as requests
        """
        tasks = []
        for model_name, kwargs in requests:
            # Inject run_id into kwargs if not already present
            if run_id and 'run_id' not in kwargs:
                kwargs['run_id'] = run_id
            task = self.call_model(model_name, **kwargs)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def _detect_provider(self, model_name: str) -> ModelProvider:
        """Auto-detect provider based on model name."""
        model_lower = model_name.lower()
        
        if "claude" in model_lower or "anthropic" in model_lower:
            return ModelProvider.ANTHROPIC
        elif "gpt" in model_lower or "o1" in model_lower:
            return ModelProvider.OPENAI
        elif "llama" in model_lower or "mixtral" in model_lower or "groq" in model_lower:
            return ModelProvider.GROQ
        elif "gemini" in model_lower or "google" in model_lower:
            return ModelProvider.GOOGLE
        elif "/" in model_lower:  # HuggingFace format
            return ModelProvider.HUGGINGFACE
        else:
            return ModelProvider.OPENAI  # Default fallback
    
    def _select_best_method(self, provider: ModelProvider) -> InvocationMethod:
        """Select best invocation method for provider."""
        # Optimized for performance and reliability
        method_preferences = {
            ModelProvider.ANTHROPIC: InvocationMethod.DIRECT,
            ModelProvider.OPENAI: InvocationMethod.DIRECT,
            ModelProvider.GROQ: InvocationMethod.DIRECT,
            ModelProvider.GOOGLE: InvocationMethod.DIRECT,
            ModelProvider.HUGGINGFACE: InvocationMethod.HTTP,
            ModelProvider.OPENROUTER: InvocationMethod.HTTP,
        }
        
        return method_preferences.get(provider, InvocationMethod.DIRECT)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for optimization."""
        stats = {}
        for provider_method, times in self._performance_stats.items():
            if times:
                stats[provider_method] = {
                    "average_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "total_calls": len(times)
                }
        return stats
    
    def cleanup(self):
        """Cleanup resources."""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)


# Convenience functions for common use cases
async def quick_call(
    model_name: str,
    message: str,
    system_prompt: Optional[str] = None,
    task_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    agui_broadcaster = None,
    mlflow_tracker = None,
    run_id: Optional[str] = None,
    **kwargs
) -> str:
    """
    Quick convenience function for simple model calls with optional tracking.
    
    Args:
        model_name: The model to call
        message: The message to send
        system_prompt: Optional system prompt
        task_id: Task ID for AG-UI tracking
        agent_id: Agent ID for tracking
        agui_broadcaster: AG-UI broadcaster for events
        mlflow_tracker: MLflow tracker for metrics
        run_id: MLflow run ID
        **kwargs: Additional parameters
    """
    call_model = CallModel(
        task_id=task_id,
        agent_id=agent_id,
        agui_broadcaster=agui_broadcaster,
        mlflow_tracker=mlflow_tracker
    )
    try:
        response = await call_model.call_model(
            model_name=model_name,
            most_recent_message=message,
            system_prompt=system_prompt,
            run_id=run_id,
            **kwargs
        )
        return response.content or ""
    finally:
        call_model.cleanup()


# Example usage and testing
if __name__ == "__main__":
    async def test_call_model():
        """Test the CallModel class with different providers."""
        call_model = CallModel()
        
        try:
            # Test quick call
            result = await quick_call(
                "claude-3-5-haiku-20241022",
                "Hello! Please respond with 'ATLAS CallModel working' if you can see this.",
                system_prompt="You are a helpful AI assistant in the ATLAS system."
            )
            print(f"Quick call result: {result}")
            
            # Test detailed call
            response = await call_model.call_model(
                model_name="gpt-4o-mini",
                provider=ModelProvider.OPENAI,
                invocation_method=InvocationMethod.DIRECT,
                system_prompt="You are a helpful AI assistant.",
                most_recent_message="What is 2+2?",
                max_tokens=100
            )
            
            print(f"Detailed call - Success: {response.success}")
            print(f"Content: {response.content}")
            print(f"Response time: {response.response_time}s")
            print(f"Tokens: {response.total_tokens}")
            
        finally:
            call_model.cleanup()
    
    # Run test
    asyncio.run(test_call_model())