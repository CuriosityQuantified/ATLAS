"""
Module: structure_service_ollama_v2
Purpose: Convert unstructured agent outputs to structured tool inputs using Ollama with Osmosis-Structure
Dependencies: ollama, pydantic
Used By: All agents for tool call formatting
"""

from ollama import chat
from pydantic import BaseModel, Field, create_model
from typing import Dict, Any, List, Optional, Type
import logging
import json
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class StructureServiceOllama:
    """
    Converts agent outputs to structured tool inputs using Ollama with Osmosis-Structure model.
    This ensures consistent and correct tool parameter formatting.
    """
    
    def __init__(self, model_name: str = "Osmosis/Osmosis-Structure-0.6B"):
        """Initialize the Ollama structure service"""
        self.model_name = model_name
        logger.info(f"Initialized Ollama structure service with model: {self.model_name}")
        
    def _create_pydantic_model(self, schema: Dict[str, Any], model_name: str = "DynamicModel") -> Type[BaseModel]:
        """Create a Pydantic model from a schema dictionary"""
        fields = {}
        
        for field_name, field_type in schema.items():
            # Determine the Python type
            if field_type == "string":
                py_type = str
                default = ""
            elif field_type == "boolean":
                py_type = bool
                default = False
            elif field_type == "integer":
                py_type = int
                default = 0
            elif isinstance(field_type, list):
                py_type = List[str]
                default = []
            elif isinstance(field_type, dict):
                py_type = Dict[str, Any]
                default = {}
            else:
                py_type = Any
                default = None
            
            # Create field with default
            fields[field_name] = (py_type, Field(default=default))
        
        # Create dynamic model
        return create_model(model_name, **fields)
    
    async def structure_agent_output(
        self,
        agent_output: str,
        target_schema: Dict[str, Any],
        tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform unstructured agent output to tool-ready structure.
        
        Args:
            agent_output: Raw output from the agent
            target_schema: Expected schema for the tool
            tool_name: Optional name of the tool being called
            
        Returns:
            Structured dictionary matching the target schema
        """
        try:
            # Create Pydantic model from schema
            model_class = self._create_pydantic_model(target_schema, tool_name or "ToolInput")
            
            # Build system prompt
            system_prompt = f"""You are a helpful assistant that understands and translates text to JSON format according to the following schema.

Schema: {model_class.model_json_schema()}

Important rules:
1. Extract relevant information from the user's text
2. Map it to the appropriate fields in the schema
3. Use only the fields defined in the schema
4. Fill missing fields with appropriate defaults
5. Return valid JSON that matches the schema exactly"""

            # Build user prompt
            user_prompt = f"""Convert the following text into JSON format:

Text: {agent_output}

Remember to extract the key information and map it to the schema fields."""

            if tool_name:
                user_prompt = f"Tool function being called: {tool_name}\n\n{user_prompt}"
            
            # Call Ollama with structured output
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chat(
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    model=self.model_name,
                    format=model_class.model_json_schema()
                )
            )
            
            # Parse and validate the response
            result = model_class.model_validate_json(response.message.content)
            structured_output = result.model_dump()
            
            logger.debug(f"Structured output for {tool_name}: {structured_output}")
            return structured_output
            
        except Exception as e:
            logger.error(f"Structure generation failed: {e}")
            logger.error(f"Agent output was: {agent_output}")
            # Return safe defaults based on schema
            return self._create_default_structure(target_schema)
    
    def _create_default_structure(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create default structure based on schema"""
        result = {}
        
        for key, value in schema.items():
            if isinstance(value, dict):
                result[key] = self._create_default_structure(value)
            elif isinstance(value, list):
                result[key] = []
            elif value == "string":
                result[key] = ""
            elif value == "boolean":
                result[key] = False
            elif value == "integer":
                result[key] = 0
            else:
                result[key] = None
        
        return result
    
    async def structure_tool_calls(
        self,
        agent_response: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Structure multiple tool calls from agent response.
        
        Args:
            agent_response: Raw response from agent containing tool calls
            available_tools: List of available tool definitions
            
        Returns:
            List of structured tool calls
        """
        tool_calls = []
        
        # Extract tool calls from response
        raw_tool_calls = agent_response.get("tool_calls", [])
        
        for raw_call in raw_tool_calls:
            tool_name = raw_call.get("name", "")
            
            # Find tool definition
            tool_def = next(
                (t for t in available_tools if t["function"]["name"] == tool_name),
                None
            )
            
            if tool_def:
                # Get expected parameters
                params = tool_def["function"].get("parameters", {})
                properties = params.get("properties", {})
                
                # Structure the arguments
                structured_args = await self.structure_agent_output(
                    json.dumps(raw_call.get("arguments", {})),
                    properties,
                    tool_name
                )
                
                tool_calls.append({
                    "name": tool_name,
                    "arguments": structured_args,
                    "id": raw_call.get("id", f"call_{len(tool_calls)}")
                })
            else:
                logger.warning(f"Unknown tool: {tool_name}")
        
        return tool_calls


# Global instance for reuse
_structure_service: Optional[StructureServiceOllama] = None


def get_structure_service() -> StructureServiceOllama:
    """Get or create the global structure service instance"""
    global _structure_service
    if _structure_service is None:
        _structure_service = StructureServiceOllama()
    return _structure_service


# Tool-specific schemas - Updated to match actual function signatures
TOOL_SCHEMAS = {
    "respond_to_user": {
        "message": "string",
        "message_type": "string",
        "include_status": "boolean",
        "request_input": "boolean",
        "options": "list",
        "context": "dict"
    },
    "call_research_team": {
        "task_description": "string",
        "priority": "string",
        "context": "dict"
    },
    "call_analysis_team": {
        "task_description": "string",
        "analysis_type": "string",
        "data_sources": "list",
        "context": "dict"
    },
    "call_writing_team": {
        "task_description": "string",
        "content_type": "string",
        "tone": "string",
        "context": "dict"
    },
    "call_rating_team": {
        "task_description": "string",
        "evaluation_criteria": "list",
        "content_to_review": "string",
        "context": "dict"
    }
}