# ATLAS LLM Routing Architecture: Multi-Provider Strategy

## Overview

ATLAS uses a sophisticated LLM routing system that automatically selects optimal models based on agent role, task complexity, and system performance. The system supports graceful fallbacks and cost optimization.

## Model Tier Strategy

### Supervisor Models (High Reasoning)
```python
SUPERVISOR_MODEL_TIERS = {
    'tier_1_primary': [
        {
            'provider': 'anthropic',
            'model': 'claude-3-opus',
            'use_cases': ['complex_reasoning', 'coordination_decisions', 'error_recovery'],
            'max_tokens': 100000,
            'cost_per_1k_tokens': 0.015,
            'reasoning_score': 9.5
        }
    ],
    'tier_2_fallback': [
        {
            'provider': 'openai',
            'model': 'gpt-4-turbo',
            'use_cases': ['supervisor_fallback', 'tool_calling_backup'],
            'max_tokens': 128000,
            'cost_per_1k_tokens': 0.01,
            'reasoning_score': 9.0
        }
    ],
    'tier_3_emergency': [
        {
            'provider': 'google',
            'model': 'gemini-pro-1.5',
            'use_cases': ['emergency_fallback', 'high_availability'],
            'max_tokens': 1000000,
            'cost_per_1k_tokens': 0.0035,
            'reasoning_score': 8.5
        }
    ]
}

WORKER_MODEL_TIERS = {
    'tier_1_primary': [
        {
            'provider': 'anthropic',
            'model': 'claude-3-sonnet',
            'use_cases': ['specialized_tasks', 'analysis_work', 'content_generation'],
            'max_tokens': 50000,
            'cost_per_1k_tokens': 0.003,
            'speed_score': 8.0
        }
    ],
    'tier_2_fast': [
        {
            'provider': 'openai', 
            'model': 'gpt-4o-mini',
            'use_cases': ['quick_tasks', 'simple_research', 'formatting'],
            'max_tokens': 128000,
            'cost_per_1k_tokens': 0.00015,
            'speed_score': 9.5
        }
    ],
    'tier_3_speed': [
        {
            'provider': 'groq',
            'model': 'llama-70b-8192',
            'use_cases': ['high_speed_inference', 'simple_analysis'],
            'max_tokens': 8192,
            'cost_per_1k_tokens': 0.0008,
            'speed_score': 10.0
        }
    ]
}
```

## LLM Router Implementation

```python
class LLMRouter:
    """Intelligent model selection and fallback management"""
    
    def __init__(self, config: Dict):
        self.model_tiers = self._load_model_tiers(config)
        self.providers = self._initialize_providers(config)
        self.performance_tracker = ModelPerformanceTracker()
        self.cost_tracker = CostTracker()
        self.health_monitor = ProviderHealthMonitor()
    
    async def select_model(
        self,
        agent_type: str,
        task_complexity: str,
        context_length: int,
        performance_requirements: Dict = None
    ) -> ModelSelection:
        """Select optimal model based on requirements and system state"""
        
        # Determine model tier based on agent type
        if 'supervisor' in agent_type:
            model_tiers = self.model_tiers['supervisor']
        else:
            model_tiers = self.model_tiers['worker']
        
        # Get available models from health monitor
        available_models = await self.health_monitor.get_available_models()
        
        # Filter by context length requirements
        suitable_models = [
            model for model in model_tiers 
            if model['max_tokens'] >= context_length
            and model['model'] in available_models
        ]
        
        # Apply selection criteria
        selection_criteria = SelectionCriteria(
            task_complexity=task_complexity,
            performance_requirements=performance_requirements or {},
            cost_budget=await self.cost_tracker.get_remaining_budget(),
            current_load=await self.performance_tracker.get_current_load()
        )
        
        selected_model = await self._evaluate_models(suitable_models, selection_criteria)
        
        return ModelSelection(
            provider=selected_model['provider'],
            model=selected_model['model'],
            config=selected_model,
            fallback_models=self._get_fallback_models(selected_model, suitable_models)
        )
    
    async def _evaluate_models(
        self,
        models: List[Dict],
        criteria: SelectionCriteria
    ) -> Dict:
        """Evaluate models against selection criteria"""
        
        scored_models = []
        
        for model in models:
            score = await self._calculate_model_score(model, criteria)
            scored_models.append((model, score))
        
        # Sort by score (higher is better)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        return scored_models[0][0]  # Return highest scoring model
    
    async def _calculate_model_score(
        self,
        model: Dict,
        criteria: SelectionCriteria
    ) -> float:
        """Calculate weighted score for model selection"""
        
        # Base scores from model configuration
        reasoning_score = model.get('reasoning_score', 0)
        speed_score = model.get('speed_score', 0)
        
        # Performance history adjustment
        historical_performance = await self.performance_tracker.get_model_performance(
            model['provider'], model['model']
        )
        
        # Cost efficiency factor
        cost_efficiency = self._calculate_cost_efficiency(
            model, criteria.cost_budget
        )
        
        # Availability and reliability
        reliability_score = await self.health_monitor.get_reliability_score(
            model['provider'], model['model']
        )
        
        # Weighted scoring based on task complexity
        if criteria.task_complexity == 'high':
            weights = {'reasoning': 0.4, 'reliability': 0.3, 'cost': 0.2, 'speed': 0.1}
        elif criteria.task_complexity == 'medium':
            weights = {'reasoning': 0.3, 'reliability': 0.2, 'cost': 0.3, 'speed': 0.2}
        else:  # low complexity
            weights = {'reasoning': 0.2, 'reliability': 0.2, 'cost': 0.4, 'speed': 0.2}
        
        final_score = (
            reasoning_score * weights['reasoning'] +
            reliability_score * weights['reliability'] +
            cost_efficiency * weights['cost'] +
            speed_score * weights['speed']
        ) * historical_performance.success_rate
        
        return final_score

class ProviderHealthMonitor:
    """Monitor health and availability of LLM providers"""
    
    def __init__(self):
        self.provider_status = {}
        self.response_times = {}
        self.error_rates = {}
        self.rate_limits = {}
    
    async def check_provider_health(self, provider: str) -> ProviderHealth:
        """Check health of specific provider"""
        
        try:
            # Test API connectivity
            start_time = time.time()
            test_response = await self._test_provider_api(provider)
            response_time = time.time() - start_time
            
            # Update metrics
            self.response_times[provider] = response_time
            self.provider_status[provider] = 'healthy'
            
            # Check rate limits
            rate_limit_status = await self._check_rate_limits(provider)
            
            return ProviderHealth(
                provider=provider,
                status='healthy',
                response_time=response_time,
                rate_limit_remaining=rate_limit_status.remaining,
                last_checked=datetime.now()
            )
            
        except Exception as e:
            self.provider_status[provider] = 'unhealthy'
            self.error_rates[provider] = self.error_rates.get(provider, 0) + 1
            
            return ProviderHealth(
                provider=provider,
                status='unhealthy',
                error=str(e),
                last_checked=datetime.now()
            )
    
    async def get_available_models(self) -> List[str]:
        """Get list of currently available models"""
        
        available_models = []
        
        for provider in ['anthropic', 'openai', 'google', 'groq']:
            health = await self.check_provider_health(provider)
            
            if health.status == 'healthy' and health.rate_limit_remaining > 10:
                provider_models = self._get_provider_models(provider)
                available_models.extend(provider_models)
        
        return available_models

class FallbackManager:
    """Manage model fallbacks and error recovery"""
    
    async def execute_with_fallback(
        self,
        primary_model: ModelSelection,
        request: LLMRequest,
        max_retries: int = 3
    ) -> LLMResponse:
        """Execute LLM request with automatic fallback"""
        
        models_to_try = [primary_model.model] + primary_model.fallback_models
        
        for attempt, model in enumerate(models_to_try):
            try:
                response = await self._execute_llm_request(model, request)
                
                # Track successful execution
                await self.performance_tracker.record_success(
                    model, request, response, attempt
                )
                
                return response
                
            except RateLimitError as e:
                # Try next model immediately for rate limits
                await self.performance_tracker.record_rate_limit(model, request)
                continue
                
            except TemporaryError as e:
                # Retry with backoff for temporary errors
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    await self.performance_tracker.record_failure(model, request, e)
                    continue
                    
            except PermanentError as e:
                # Skip to next model for permanent errors
                await self.performance_tracker.record_failure(model, request, e)
                continue
        
        # All models failed
        raise AllModelsFailedError(
            "All models failed to process request",
            models_tried=models_to_try,
            last_errors=self._get_last_errors()
        )

class CostTracker:
    """Track and optimize LLM costs across providers"""
    
    def __init__(self, daily_budget: float = 100.0):
        self.daily_budget = daily_budget
        self.current_spend = 0.0
        self.provider_spend = {}
        self.model_costs = {}
    
    async def track_request_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_per_1k_input: float,
        cost_per_1k_output: float = None
    ):
        """Track cost of individual request"""
        
        if cost_per_1k_output is None:
            cost_per_1k_output = cost_per_1k_input
        
        input_cost = (input_tokens / 1000) * cost_per_1k_input
        output_cost = (output_tokens / 1000) * cost_per_1k_output
        total_cost = input_cost + output_cost
        
        # Update tracking
        self.current_spend += total_cost
        self.provider_spend[provider] = self.provider_spend.get(provider, 0) + total_cost
        
        model_key = f"{provider}:{model}"
        if model_key not in self.model_costs:
            self.model_costs[model_key] = {'requests': 0, 'total_cost': 0, 'tokens': 0}
        
        self.model_costs[model_key]['requests'] += 1
        self.model_costs[model_key]['total_cost'] += total_cost
        self.model_costs[model_key]['tokens'] += input_tokens + output_tokens
    
    async def get_remaining_budget(self) -> float:
        """Get remaining budget for the day"""
        return max(0, self.daily_budget - self.current_spend)
    
    async def should_use_cost_optimization(self) -> bool:
        """Determine if cost optimization should be enabled"""
        remaining_budget = await self.get_remaining_budget()
        return remaining_budget < (self.daily_budget * 0.2)  # Less than 20% remaining
```

## Provider Integration Layer

```python
class UnifiedLLMProvider:
    """Unified interface for all LLM providers"""
    
    def __init__(self, config: Dict):
        self.providers = {
            'anthropic': AnthropicProvider(config['anthropic']),
            'openai': OpenAIProvider(config['openai']), 
            'google': GoogleProvider(config['google']),
            'groq': GroqProvider(config['groq'])
        }
        self.router = LLMRouter(config)
        self.fallback_manager = FallbackManager()
    
    async def generate(
        self,
        agent_type: str,
        messages: List[Dict],
        tools: List[Dict] = None,
        task_complexity: str = 'medium',
        **kwargs
    ) -> LLMResponse:
        """Generate response using optimal model selection"""
        
        # Calculate context length
        context_length = self._estimate_context_length(messages, tools)
        
        # Select optimal model
        model_selection = await self.router.select_model(
            agent_type=agent_type,
            task_complexity=task_complexity,
            context_length=context_length,
            performance_requirements=kwargs.get('performance_requirements')
        )
        
        # Create request object
        request = LLMRequest(
            messages=messages,
            tools=tools,
            model=model_selection.model,
            provider=model_selection.provider,
            **kwargs
        )
        
        # Execute with fallback
        response = await self.fallback_manager.execute_with_fallback(
            model_selection, request
        )
        
        return response

class AnthropicProvider:
    """Anthropic-specific provider implementation"""
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        response = await client.messages.create(
            model=request.model,
            messages=request.messages,
            tools=request.tools,
            max_tokens=request.max_tokens or 4096
        )
        
        return LLMResponse(
            content=response.content[0].text,
            usage=response.usage,
            model=request.model,
            provider='anthropic'
        )

class OpenAIProvider:
    """OpenAI-specific provider implementation"""
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        client = openai.AsyncOpenAI(api_key=self.api_key)
        
        response = await client.chat.completions.create(
            model=request.model,
            messages=request.messages,
            tools=request.tools,
            max_tokens=request.max_tokens
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            usage=response.usage,
            model=request.model,
            provider='openai'
        )
```

This multi-provider routing system provides:

1. **Intelligent Model Selection**: Based on agent type, task complexity, and system state
2. **Automatic Fallbacks**: Graceful degradation when providers fail
3. **Cost Optimization**: Budget tracking and model selection based on cost efficiency
4. **Performance Monitoring**: Real-time tracking of provider health and performance
5. **Unified Interface**: Single API regardless of underlying provider

The system ensures ATLAS maintains high availability and performance while optimizing for cost and quality based on your specified model preferences.