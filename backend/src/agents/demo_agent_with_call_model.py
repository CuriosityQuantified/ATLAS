#!/usr/bin/env python3
"""
Enhanced Demo Agent using the unified CallModel interface
Demonstrates best practices for model calling in ATLAS agents
"""

import os
import sys
import asyncio
import time
from typing import Dict, Optional, List, Any
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agui.handlers import AGUIEventBroadcaster
from src.mlflow.tracking import ATLASMLflowTracker
from src.utils.call_model import CallModel, ModelProvider, InvocationMethod, quick_call
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EnhancedDemoAgent:
    """Enhanced demo agent using unified CallModel interface with multi-provider support."""
    
    def __init__(self, agent_id: str = "enhanced_demo_agent", name: str = "Enhanced Demo Agent"):
        self.agent_id = agent_id
        self.name = name
        # Initialize broadcaster without connection manager for standalone testing
        self.broadcaster = AGUIEventBroadcaster(connection_manager=None)
        self.mlflow_tracker = ATLASMLflowTracker()
        # Initialize CallModel with tracking integration
        self.call_model = CallModel(
            enable_threading=True, 
            max_workers=5,
            agent_id=self.agent_id,
            agui_broadcaster=self.broadcaster,
            mlflow_tracker=self.mlflow_tracker
        )
        self.messages = []
        
        # Agent configuration
        self.preferred_models = [
            "claude-3-5-haiku-20241022",  # Fast and capable
            "llama-3.1-8b-instant",       # Very fast backup
            "gpt-4o-mini",                # Reliable fallback
        ]
        self.system_prompt = f"""You are {self.name}, an advanced AI assistant working as part of the ATLAS multi-agent system.

ATLAS (Agentic Task Logic & Analysis System) is a hierarchical multi-agent platform that decomposes complex tasks into specialized sub-processes. You are designed to:

1. Process information efficiently and accurately
2. Communicate clearly and concisely  
3. Collaborate effectively with other agents
4. Provide helpful analysis and insights
5. Maintain context across conversations

Respond professionally and helpfully while being part of this sophisticated multi-agent ecosystem."""
    
    async def process_task_with_fallbacks(self, task_id: str, user_input: str, 
                                        preferred_model: Optional[str] = None) -> Dict:
        """Process a task with automatic fallbacks to different models."""
        
        # Start MLflow run
        with self.mlflow_tracker.start_agent_run(
            agent_id=self.agent_id,
            agent_type="enhanced_demo",
            task_id=task_id,
            parent_run_id=None
        ) as run_id:
            
            # Broadcast agent activation
            await self.broadcaster.broadcast_agent_status(
                task_id, self.agent_id, "idle", "active"
            )
            
            # Broadcast received input
            input_message_id = str(uuid.uuid4())
            await self.broadcaster.broadcast_dialogue_update(
                task_id=task_id,
                agent_id=self.agent_id,
                message_id=input_message_id,
                direction="input",
                content={
                    "type": "text",
                    "data": user_input,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "tokens": len(user_input.split())
                    }
                },
                sender="user"
            )
            
            # Update status to processing
            await self.broadcaster.broadcast_agent_status(
                task_id, self.agent_id, "active", "processing"
            )
            
            # Determine models to try
            models_to_try = []
            if preferred_model:
                models_to_try.append(preferred_model)
            models_to_try.extend([m for m in self.preferred_models if m != preferred_model])
            
            # Try models with fallbacks
            for attempt, model_name in enumerate(models_to_try):
                try:
                    print(f"🤖 Attempting with {model_name} (attempt {attempt + 1})")
                    
                    start_time = time.time()
                    
                    # Use CallModel for unified interface with tracking
                    self.call_model.task_id = task_id  # Update task_id for current task
                    response = await self.call_model.call_model(
                        model_name=model_name,
                        system_prompt=self.system_prompt,
                        conversation_history=self.messages,
                        most_recent_message=user_input,
                        max_tokens=500,
                        temperature=0.7,
                        timeout=20.0,
                        run_id=run_id
                    )
                    
                    if response.success:
                        processing_time = time.time() - start_time
                        
                        # Calculate cost using the response data
                        total_cost = response.cost_usd or 0.0
                        
                        # Log LLM metrics to MLflow
                        self.mlflow_tracker.log_llm_call(
                            run_id,
                            model_provider=response.provider or "unknown",
                            model_name=model_name,
                            input_tokens=response.input_tokens or 0,
                            output_tokens=response.output_tokens or 0,
                            total_cost=total_cost,
                            latency=processing_time,
                            success=True
                        )
                        
                        # Broadcast the response
                        output_message_id = str(uuid.uuid4())
                        await self.broadcaster.broadcast_dialogue_update(
                            task_id=task_id,
                            agent_id=self.agent_id,
                            message_id=output_message_id,
                            direction="output",
                            content={
                                "type": "text",
                                "data": response.content,
                                "metadata": {
                                    "timestamp": datetime.now().isoformat(),
                                    "model": model_name,
                                    "provider": response.provider,
                                    "invocation_method": response.invocation_method,
                                    "tokens": response.total_tokens,
                                    "processing_time": processing_time,
                                    "cost": total_cost,
                                    "attempt": attempt + 1
                                }
                            },
                            sender=self.agent_id
                        )
                        
                        # Store message in memory (without timestamps for API compatibility)
                        self.messages.extend([
                            {"role": "user", "content": user_input},
                            {"role": "assistant", "content": response.content}
                        ])
                        
                        # Update status back to active
                        await self.broadcaster.broadcast_agent_status(
                            task_id, self.agent_id, "processing", "active"
                        )
                        
                        # Broadcast completion
                        from src.agui.events import AGUIEvent, AGUIEventType
                        completion_event = AGUIEvent(
                            event_type=AGUIEventType.AGENT_COMPLETED,
                            task_id=task_id,
                            agent_id=self.agent_id,
                            data={
                                "success": True,
                                "model_used": model_name,
                                "provider": response.provider,
                                "processing_time": processing_time,
                                "cost": total_cost,
                                "attempts": attempt + 1
                            }
                        )
                        await self.broadcaster._broadcast_event(completion_event)
                        
                        return {
                            "success": True,
                            "response": response.content,
                            "metadata": {
                                "model": model_name,
                                "provider": response.provider,
                                "invocation_method": response.invocation_method,
                                "processing_time": processing_time,
                                "tokens": response.total_tokens,
                                "cost": total_cost,
                                "attempt": attempt + 1,
                                "fallback_used": attempt > 0
                            }
                        }
                    else:
                        print(f"❌ {model_name} failed: {response.error}")
                        # Try next model
                        continue
                        
                except Exception as e:
                    print(f"❌ Exception with {model_name}: {e}")
                    # Try next model
                    continue
            
            # All models failed
            await self.broadcaster.broadcast_error(
                task_id, self.agent_id, "ModelFailure", "All model attempts failed", ""
            )
            
            await self.broadcaster.broadcast_agent_status(
                task_id, self.agent_id, "processing", "idle"
            )
            
            return {
                "success": False,
                "error": "All model attempts failed",
                "models_tried": models_to_try
            }
    
    async def process_task_concurrent(self, task_id: str, user_input: str, 
                                    models: Optional[List[str]] = None) -> Dict:
        """Process task using multiple models concurrently and return the fastest successful response."""
        
        # Use default models if none specified
        if not models:
            models = self.preferred_models[:3]  # Top 3 models
        
        print(f"🚀 Processing with {len(models)} models concurrently: {models}")
        
        # Start MLflow run
        with self.mlflow_tracker.start_agent_run(
            agent_id=self.agent_id,
            agent_type="enhanced_demo_concurrent",
            task_id=task_id,
            parent_run_id=None
        ) as run_id:
            
            # Broadcast processing start
            await self.broadcaster.broadcast_agent_status(
                task_id, self.agent_id, "idle", "processing"
            )
            
            try:
                # Prepare concurrent requests
                self.call_model.task_id = task_id  # Update task_id for current task
                requests = []
                for model in models:
                    request_data = {
                        "system_prompt": self.system_prompt,
                        "conversation_history": self.messages,
                        "most_recent_message": user_input,
                        "max_tokens": 500,
                        "temperature": 0.7,
                        "timeout": 15.0,
                        "run_id": run_id
                    }
                    requests.append((model, request_data))
                
                # Execute concurrent calls with tracking
                start_time = time.time()
                responses = await self.call_model.call_multiple_models(requests, run_id=run_id)
                total_time = time.time() - start_time
                
                # Find first successful response
                successful_response = None
                fastest_time = float('inf')
                
                for i, response in enumerate(responses):
                    if isinstance(response, Exception):
                        print(f"❌ {models[i]} failed with exception: {response}")
                        continue
                    
                    if response.success and response.response_time < fastest_time:
                        successful_response = response
                        fastest_time = response.response_time
                        winning_model = models[i]
                
                if successful_response:
                    # Log successful response
                    self.mlflow_tracker.log_llm_call(
                        run_id,
                        model_provider=successful_response.provider or "unknown",
                        model_name=winning_model,
                        input_tokens=successful_response.input_tokens or 0,
                        output_tokens=successful_response.output_tokens or 0,
                        total_cost=successful_response.cost_usd or 0.0,
                        latency=fastest_time,
                        success=True
                    )
                    
                    # Broadcast successful response
                    output_message_id = str(uuid.uuid4())
                    await self.broadcaster.broadcast_dialogue_update(
                        task_id=task_id,
                        agent_id=self.agent_id,
                        message_id=output_message_id,
                        direction="output",
                        content={
                            "type": "text",
                            "data": successful_response.content,
                            "metadata": {
                                "timestamp": datetime.now().isoformat(),
                                "winning_model": winning_model,
                                "fastest_time": fastest_time,
                                "total_time": total_time,
                                "models_tried": len(models),
                                "strategy": "concurrent"
                            }
                        },
                        sender=self.agent_id
                    )
                    
                    await self.broadcaster.broadcast_agent_status(
                        task_id, self.agent_id, "processing", "active"
                    )
                    
                    return {
                        "success": True,
                        "response": successful_response.content,
                        "metadata": {
                            "winning_model": winning_model,
                            "fastest_time": fastest_time,
                            "total_time": total_time,
                            "models_tried": len(models),
                            "strategy": "concurrent"
                        }
                    }
                else:
                    # All models failed
                    await self.broadcaster.broadcast_error(
                        task_id, self.agent_id, "ConcurrentFailure", 
                        f"All {len(models)} concurrent models failed", ""
                    )
                    
                    return {
                        "success": False,
                        "error": f"All {len(models)} models failed",
                        "models_tried": models,
                        "total_time": total_time
                    }
                    
            finally:
                await self.broadcaster.broadcast_agent_status(
                    task_id, self.agent_id, "processing", "idle"
                )
    
    async def quick_response(self, message: str) -> str:
        """Quick response using the fastest available model."""
        try:
            return await quick_call(
                "llama-3.1-8b-instant",  # Fastest model
                message,
                system_prompt="You are a helpful AI assistant. Respond concisely."
            )
        except Exception as e:
            return f"Error: {e}"
    
    def cleanup(self):
        """Cleanup resources."""
        if self.call_model:
            self.call_model.cleanup()


async def demo_enhanced_agent():
    """Demonstrate the enhanced agent capabilities."""
    
    agent = EnhancedDemoAgent(agent_id="enhanced_research_agent", name="Enhanced Research Agent")
    task_id = f"enhanced_demo_{int(time.time())}"
    
    print(f"\n🤖 Enhanced Demo Agent with CallModel")
    print(f"Task ID: {task_id}")
    print(f"Agent: {agent.name} ({agent.agent_id})")
    print("-" * 60)
    
    try:
        # Test 1: Fallback strategy
        print("\n📝 Test 1: Fallback Strategy (Sequential Model Attempts)")
        result1 = await agent.process_task_with_fallbacks(
            task_id,
            "Explain the benefits of multi-agent systems and how ATLAS implements them."
        )
        if result1["success"]:
            print(f"✅ Success with {result1['metadata']['model']} (attempt {result1['metadata']['attempt']})")
            print(f"📝 Response: {result1['response'][:150]}...")
            print(f"⏱️  Time: {result1['metadata']['processing_time']:.2f}s")
        else:
            print(f"❌ Failed: {result1['error']}")
        
        await asyncio.sleep(2)
        
        # Test 2: Concurrent strategy
        print("\n📝 Test 2: Concurrent Strategy (Parallel Model Racing)")
        result2 = await agent.process_task_concurrent(
            task_id,
            "What are the key advantages of using multiple AI models simultaneously?"
        )
        if result2["success"]:
            print(f"✅ Success with {result2['metadata']['winning_model']}")
            print(f"📝 Response: {result2['response'][:150]}...")
            print(f"🏆 Fastest: {result2['metadata']['fastest_time']:.2f}s")
            print(f"📊 Total: {result2['metadata']['total_time']:.2f}s ({result2['metadata']['models_tried']} models)")
        else:
            print(f"❌ Failed: {result2['error']}")
        
        # Test 3: Quick response
        print("\n📝 Test 3: Quick Response")
        quick_result = await agent.quick_response("What is ATLAS in one sentence?")
        print(f"⚡ Quick response: {quick_result}")
        
        print("\n✅ Enhanced demo completed!")
        print(f"Total messages in conversation: {len(agent.messages)}")
        
        return task_id
        
    finally:
        agent.cleanup()


if __name__ == "__main__":
    # Run the enhanced demo
    asyncio.run(demo_enhanced_agent())