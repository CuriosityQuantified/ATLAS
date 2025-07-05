"""
Module: structure_service_ollama
Purpose: Convert unstructured agent outputs to structured tool inputs using Ollama
Dependencies: ollama, httpx
Used By: All agents for tool call formatting
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)


class StructureServiceOllama:
    """
    Converts agent outputs to structured tool inputs using Ollama with Osmosis-Structure model.
    This ensures consistent and correct tool parameter formatting.
    """
    
    def __init__(self, model_name: str = "qwen3:14b"):
        """Initialize the Ollama structure service"""
        self.model_name = model_name
        self.base_url = "http://localhost:11434"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"Initialized Ollama structure service with model: {self.model_name}")
        
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
            prompt = self._build_structure_prompt(agent_output, target_schema, tool_name)
            
            # Call Ollama API
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,  # Low temperature for consistent structure
                    "format": "json"  # Request JSON output
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return self._create_default_structure(target_schema)
            
            result = response.json()
            generated_text = result.get("response", "")
            
            # Extract and parse JSON
            structured_output = self._extract_json(generated_text, target_schema)
            
            logger.debug(f"Structured output: {structured_output}")
            return structured_output
            
        except Exception as e:
            logger.error(f"Structure generation failed: {e}")
            return self._create_default_structure(target_schema)
    
    def _build_structure_prompt(
        self,
        agent_output: str,
        target_schema: Dict[str, Any],
        tool_name: Optional[str] = None
    ) -> str:
        """Build prompt for the structure model"""
        schema_str = json.dumps(target_schema, indent=2)
        
        prompt = f"""You are a JSON structure converter. Convert the given text into a valid JSON object that matches the target schema.

Target Schema:
```json
{schema_str}
```

Text to Convert:
"{agent_output}"

Rules:
1. Extract relevant information from the text
2. Map it to the schema fields
3. Use ONLY the fields defined in the schema
4. Fill missing fields with appropriate defaults (empty strings for text, empty arrays for lists, etc.)
5. Return ONLY valid JSON, no explanations

JSON Output:
```json"""
        
        if tool_name:
            prompt = f"Tool Function: {tool_name}\n\n{prompt}"
        
        return prompt
    
    def _extract_json(self, generated_text: str, target_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract JSON from generated text"""
        try:
            # First try to parse the whole response as JSON
            return json.loads(generated_text)
        except json.JSONDecodeError:
            pass
        
        try:
            # Look for JSON between ```json and ``` markers
            start_marker = "```json"
            end_marker = "```"
            
            start_idx = generated_text.find(start_marker)
            if start_idx != -1:
                start_idx += len(start_marker)
                end_idx = generated_text.find(end_marker, start_idx)
                if end_idx != -1:
                    json_str = generated_text[start_idx:end_idx].strip()
                    return json.loads(json_str)
            
            # Try to find JSON starting with {
            start_idx = generated_text.find("{")
            if start_idx != -1:
                # Find matching closing brace
                brace_count = 0
                end_idx = start_idx
                
                for i in range(start_idx, len(generated_text)):
                    if generated_text[i] == "{":
                        brace_count += 1
                    elif generated_text[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                json_str = generated_text[start_idx:end_idx]
                return json.loads(json_str)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON: {e}")
        
        # Return defaults if parsing fails
        return self._create_default_structure(target_schema)
    
    def _create_default_structure(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Create default structure based on schema"""
        result = {}
        
        for key, value in schema.items():
            if isinstance(value, dict):
                result[key] = self._create_default_structure(value)
            elif isinstance(value, list):
                result[key] = []
            elif isinstance(value, str):
                result[key] = ""
            elif isinstance(value, (int, float)):
                result[key] = 0
            elif isinstance(value, bool):
                result[key] = False
            else:
                result[key] = None
        
        return result
    
    async def structure_tool_calls(
        self,
        agent_response: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Structure tool calls from agent response.
        
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
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global instance for reuse
_structure_service: Optional[StructureServiceOllama] = None


def get_structure_service() -> StructureServiceOllama:
    """Get or create the global structure service instance"""
    global _structure_service
    if _structure_service is None:
        _structure_service = StructureServiceOllama()
    return _structure_service


# Tool-specific schemas
TOOL_SCHEMAS = {
    "respond_to_user": {
        "message": "string",
        "message_type": "string",
        "include_status": "boolean",
        "request_input": "boolean",
        "options": ["string"],
        "context": {}
    },
    "call_research_team": {
        "task_description": "string",
        "research_type": "string",
        "sources": ["string"],
        "context": {}
    },
    "call_analysis_team": {
        "task_description": "string",
        "analysis_type": "string",
        "data_sources": ["string"],
        "context": {}
    },
    "call_writing_team": {
        "task_description": "string",
        "content_type": "string",
        "tone": "string",
        "context": {}
    },
    "call_rating_team": {
        "content_to_rate": "string",
        "rating_criteria": ["string"],
        "context": {}
    }
}