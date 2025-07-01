#!/usr/bin/env python3
"""
ATLAS Demo Agent - Basic LLM Agent with AG-UI Broadcasting
Demonstrates real-time communication between agent and frontend
"""

import os
import sys
import asyncio
import time
from typing import Dict, Optional
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agui.handlers import AGUIEventBroadcaster
from src.mlflow.tracking import ATLASMLflowTracker
import groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DemoAgent:
    """Basic demonstration agent with LLM capabilities and AG-UI broadcasting"""
    
    def __init__(self, agent_id: str = "demo_agent", name: str = "Demo Agent"):
        self.agent_id = agent_id
        self.name = name
        self.broadcaster = AGUIEventBroadcaster()
        self.groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.mlflow_tracker = ATLASMLflowTracker()
        self.messages = []
        
    async def process_task(self, task_id: str, user_input: str) -> Dict:
        """Process a task with real-time broadcasting"""
        
        # Start MLflow run
        with self.mlflow_tracker.start_agent_run(
            agent_id=self.agent_id,
            agent_type="demo",
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
                        "tokens": len(user_input.split())  # Simple token estimate
                    }
                },
                sender="user"
            )
            
            # Log input to MLflow
            self.mlflow_tracker.log_dialogue_message_stats(
                run_id,
                direction="input",
                content_type="text",
                token_count=len(user_input.split()),
                processing_time=0.0
            )
            
            # Update status to processing
            await self.broadcaster.broadcast_agent_status(
                task_id, self.agent_id, "active", "processing"
            )
            
            try:
                # Make LLM call
                start_time = time.time()
                
                response = self.groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are {self.name}, a helpful AI assistant working as part of the ATLAS multi-agent system. Respond concisely and helpfully."
                        },
                        {
                            "role": "user",
                            "content": user_input
                        }
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                
                processing_time = time.time() - start_time
                response_text = response.choices[0].message.content
                token_count = response.usage.total_tokens if response.usage else 0
                
                # Calculate cost
                try:
                    from src.utils.cost_calculator import get_cost_and_pricing_details
                    total_cost, cost_details = get_cost_and_pricing_details(
                        "llama-3.1-8b-instant",
                        response.usage.prompt_tokens if response.usage else 0,
                        response.usage.completion_tokens if response.usage else 0
                    )
                    cost_info = {"total_cost": total_cost}
                except Exception as e:
                    print(f"Cost calculation error: {e}")
                    cost_info = {"total_cost": 0.0}
                
                # Log LLM metrics to MLflow
                self.mlflow_tracker.log_llm_call(
                    run_id,
                    model_provider="groq",
                    model_name="llama-3.1-8b-instant",
                    input_tokens=response.usage.prompt_tokens if response.usage else 0,
                    output_tokens=response.usage.completion_tokens if response.usage else 0,
                    total_cost=cost_info["total_cost"],
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
                        "data": response_text,
                        "metadata": {
                            "timestamp": datetime.now().isoformat(),
                            "model": "llama-3.1-8b-instant",
                            "tokens": token_count,
                            "processing_time": processing_time,
                            "cost": cost_info["total_cost"]
                        }
                    },
                    sender=self.agent_id
                )
                
                # Log output to MLflow
                self.mlflow_tracker.log_dialogue_message_stats(
                    run_id,
                    direction="output",
                    content_type="text",
                    token_count=token_count,
                    processing_time=processing_time
                )
                
                # Store message in memory
                self.messages.append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().isoformat()
                })
                self.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update status back to active
                await self.broadcaster.broadcast_agent_status(
                    task_id, self.agent_id, "processing", "active"
                )
                
                # Broadcast completion - use AGUIEventFactory directly
                from src.agui.events import AGUIEvent, AGUIEventType
                completion_event = AGUIEvent(
                    event_type=AGUIEventType.AGENT_COMPLETED,
                    task_id=task_id,
                    agent_id=self.agent_id,
                    data={
                        "success": True,
                        "processing_time": processing_time,
                        "cost": cost_info["total_cost"]
                    }
                )
                await self.broadcaster._broadcast_event(completion_event)
                
                return {
                    "success": True,
                    "response": response_text,
                    "metadata": {
                        "model": "llama-3.1-8b-instant",
                        "processing_time": processing_time,
                        "tokens": token_count,
                        "cost": cost_info["total_cost"]
                    }
                }
                
            except Exception as e:
                # Log error to MLflow
                self.mlflow_tracker.log_error(
                    run_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    error_context={"user_input": user_input}
                )
                
                # Broadcast error - use existing broadcast_error method
                await self.broadcaster.broadcast_error(
                    task_id, self.agent_id, type(e).__name__, str(e), ""
                )
                
                # Update status to idle
                await self.broadcaster.broadcast_agent_status(
                    task_id, self.agent_id, "processing", "idle"
                )
                
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
    
    async def ask_user_question(self, task_id: str, question: str) -> Optional[str]:
        """Ask the user a question and wait for response"""
        
        # Broadcast user approval required event - use existing method
        await self.broadcaster.broadcast_user_approval_required(
            task_id, self.agent_id, "question", question, ["Yes", "No", "Provide more details"]
        )
        
        # In a real implementation, this would wait for WebSocket response
        # For now, we'll simulate a delay
        await asyncio.sleep(2)
        
        # Return simulated response
        return "Yes, please proceed"
    
    async def generate_multimodal_content(self, task_id: str, content_type: str) -> Dict:
        """Generate different types of content for testing"""
        
        await self.broadcaster.broadcast_agent_status(
            task_id, self.agent_id, "active", "processing"
        )
        
        if content_type == "code":
            # Generate code example
            code_content = """def analyze_data(data: List[Dict]) -> Dict:
    \"\"\"Analyze dataset and return insights\"\"\"
    total_items = len(data)
    categories = set(item.get('category') for item in data)
    
    return {
        'total_items': total_items,
        'unique_categories': len(categories),
        'categories': list(categories)
    }"""
            
            await self.broadcaster.broadcast_dialogue_update(
                task_id=task_id,
                agent_id=self.agent_id,
                message_id=str(uuid.uuid4()),
                direction="output",
                content={
                    "type": "code",
                    "data": code_content,
                    "language": "python"
                },
                sender=self.agent_id
            )
            
            # Track in MLflow
            await self.broadcaster.broadcast_content_generated(
                task_id, self.agent_id, "code", len(code_content), 0.5
            )
            
        elif content_type == "json":
            # Generate JSON data
            json_content = {
                "analysis_results": {
                    "sentiment": "positive",
                    "confidence": 0.87,
                    "keywords": ["ATLAS", "multi-agent", "AI", "system"],
                    "summary": "Advanced multi-agent system showing promising results"
                }
            }
            
            await self.broadcaster.broadcast_dialogue_update(
                task_id=task_id,
                agent_id=self.agent_id,
                message_id=str(uuid.uuid4()),
                direction="output",
                content={
                    "type": "json",
                    "data": json_content
                },
                sender=self.agent_id
            )
            
        elif content_type == "chart":
            # Generate chart data
            chart_data = {
                "type": "line",
                "data": {
                    "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
                    "datasets": [{
                        "label": "Agent Performance",
                        "data": [65, 72, 78, 85, 92],
                        "borderColor": "rgb(75, 192, 192)",
                        "tension": 0.1
                    }]
                }
            }
            
            await self.broadcaster.broadcast_dialogue_update(
                task_id=task_id,
                agent_id=self.agent_id,
                message_id=str(uuid.uuid4()),
                direction="output",
                content={
                    "type": "chart",
                    "data": chart_data
                },
                sender=self.agent_id
            )
        
        await self.broadcaster.broadcast_agent_status(
            task_id, self.agent_id, "processing", "active"
        )
        
        return {"success": True, "content_type": content_type}


async def demo_conversation():
    """Run a demo conversation with the agent"""
    
    agent = DemoAgent(agent_id="research_web_researcher", name="Web Research Agent")
    task_id = f"demo_task_{int(time.time())}"
    
    print(f"\n🤖 Starting Demo Agent Conversation")
    print(f"Task ID: {task_id}")
    print(f"Agent: {agent.name} ({agent.agent_id})")
    print("-" * 50)
    
    # Test 1: Basic conversation
    print("\n📝 Test 1: Basic Conversation")
    result1 = await agent.process_task(
        task_id,
        "Hello! Can you explain what ATLAS is and how you fit into the system?"
    )
    print(f"Response: {result1.get('response', result1.get('error'))[:200]}...")
    
    # Wait a bit between messages
    await asyncio.sleep(2)
    
    # Test 2: Follow-up question
    print("\n📝 Test 2: Follow-up Question")
    result2 = await agent.process_task(
        task_id,
        "What are the main components of a multi-agent system like ATLAS?"
    )
    print(f"Response: {result2.get('response', result2.get('error'))[:200]}...")
    
    # Test 3: Generate multimodal content
    print("\n📝 Test 3: Multimodal Content Generation")
    
    # Generate code
    await agent.generate_multimodal_content(task_id, "code")
    print("Generated: Code example")
    
    await asyncio.sleep(1)
    
    # Generate JSON
    await agent.generate_multimodal_content(task_id, "json")
    print("Generated: JSON data")
    
    await asyncio.sleep(1)
    
    # Generate chart
    await agent.generate_multimodal_content(task_id, "chart")
    print("Generated: Chart visualization")
    
    # Test 4: User interaction
    print("\n📝 Test 4: User Interaction")
    user_response = await agent.ask_user_question(
        task_id,
        "Should I proceed with a detailed analysis of the ATLAS architecture?"
    )
    print(f"User response: {user_response}")
    
    print("\n✅ Demo conversation completed!")
    print(f"Total messages: {len(agent.messages)}")
    
    return task_id


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_conversation())