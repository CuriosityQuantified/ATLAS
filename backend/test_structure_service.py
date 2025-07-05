#!/usr/bin/env python3
"""
Test the Osmosis-Structure service integration
"""

import asyncio
import logging
from src.agents.structure_service import StructureService, TOOL_SCHEMAS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_structure_service():
    """Test the structure service with various inputs"""
    print("\n🧪 Testing Osmosis-Structure Service")
    print("=" * 60)
    
    # Initialize service
    print("\n1. Initializing Osmosis-Structure-0.6B...")
    service = StructureService()
    print("✅ Model loaded successfully")
    
    # Test cases
    test_cases = [
        {
            "name": "respond_to_user with raw parameter",
            "input": {
                "raw": "I'll help you research renewable energy. Let me gather the latest information for you.",
                "message": "Starting research on renewable energy",
                "type": "update"
            },
            "tool": "respond_to_user",
            "expected_keys": ["message", "message_type"]
        },
        {
            "name": "call_research_team with extra parameters",
            "input": {
                "raw": "Research renewable energy technologies",
                "topic": "renewable energy",
                "focus": "latest developments"
            },
            "tool": "call_research_team",
            "expected_keys": ["task_description"]
        },
        {
            "name": "Complex nested input",
            "input": {
                "raw": "Analyze the market data",
                "data_source": "market reports",
                "analysis_method": "SWOT",
                "extra_field": "should be filtered out"
            },
            "tool": "call_analysis_team",
            "expected_keys": ["task_description", "analysis_type"]
        }
    ]
    
    # Run tests
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test['name']}")
        print(f"   Input: {test['input']}")
        
        schema = TOOL_SCHEMAS.get(test['tool'], {})
        result = await service.structure_agent_output(
            str(test['input']),
            schema,
            test['tool']
        )
        
        print(f"   Output: {result}")
        
        # Verify expected keys
        for key in test['expected_keys']:
            if key in result:
                print(f"   ✅ Found expected key: {key}")
            else:
                print(f"   ❌ Missing expected key: {key}")
    
    # Test tool call structuring
    print("\n\n🔧 Testing Tool Call Structuring")
    print("=" * 60)
    
    raw_response = {
        "tool_calls": [
            {
                "name": "respond_to_user",
                "arguments": {
                    "raw": "I'll start researching now",
                    "extra": "should be removed"
                },
                "id": "call_1"
            },
            {
                "name": "call_research_team",
                "arguments": {
                    "raw": "Research renewable energy",
                    "topic": "renewable energy"
                },
                "id": "call_2"
            }
        ]
    }
    
    available_tools = [
        {
            "type": "function",
            "function": {
                "name": "respond_to_user",
                "parameters": TOOL_SCHEMAS["respond_to_user"]
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "call_research_team",
                "parameters": TOOL_SCHEMAS["call_research_team"]
            }
        }
    ]
    
    structured_calls = await service.structure_tool_calls(raw_response, available_tools)
    
    print("\nStructured tool calls:")
    for call in structured_calls:
        print(f"\n- Tool: {call['name']}")
        print(f"  Arguments: {call['arguments']}")
        print(f"  ID: {call['id']}")
    
    print("\n\n✅ Structure service test completed!")


if __name__ == "__main__":
    asyncio.run(test_structure_service())