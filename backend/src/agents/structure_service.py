"""
Module: structure_service
Purpose: Convert unstructured agent outputs to structured tool inputs using Osmosis-Structure-0.6B
Dependencies: transformers, torch
Used By: All agents for tool call formatting
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Dict, Any, List, Optional
import logging
import json
import asyncio
from functools import lru_cache
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class StructureService:
    """
    Converts agent outputs to structured tool inputs using Osmosis-Structure-0.6B.
    This ensures consistent and correct tool parameter formatting.
    """
    
    def __init__(self):
        """Initialize the Osmosis-Structure model for local inference"""
        self.model_name = "osmosis-ai/Osmosis-Structure-0.6B"
        
        logger.info(f"Loading {self.model_name} for structured output generation...")
        
        # Get HuggingFace token from environment
        hf_token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
        if not hf_token:
            logger.warning("No HuggingFace token found in environment. Trying without authentication...")
        
        # Load model and tokenizer with authentication
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_auth_token=hf_token  # Use token from environment
            )
        except Exception as e:
            logger.error(f"Failed to load tokenizer. Make sure HUGGINGFACE_API_KEY is set in .env")
            logger.error(f"Error: {e}")
            raise
        
        # Determine device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load model with appropriate settings
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True,
                use_auth_token=hf_token  # Use token from environment
            )
        except Exception as e:
            logger.error(f"Failed to load model. Make sure HUGGINGFACE_API_KEY is set in .env")
            logger.error(f"Error: {e}")
            raise
        
        if not torch.cuda.is_available():
            self.model = self.model.to(self.device)
        
        self.model.eval()
        logger.info("Osmosis-Structure model loaded successfully")
    
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
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._generate_structure,
            agent_output,
            target_schema,
            tool_name
        )
    
    def _generate_structure(
        self,
        agent_output: str,
        target_schema: Dict[str, Any],
        tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured output using the model"""
        try:
            # Build prompt for structure generation
            prompt = self._build_structure_prompt(agent_output, target_schema, tool_name)
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate structured output
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.1,  # Low temperature for consistent structure
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode and parse
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract JSON from generated text
            structured_output = self._extract_json(generated_text, target_schema)
            
            logger.debug(f"Structured output: {structured_output}")
            return structured_output
            
        except Exception as e:
            logger.error(f"Structure generation failed: {e}")
            # Return safe defaults based on schema
            return self._create_default_structure(target_schema)
    
    def _build_structure_prompt(
        self,
        agent_output: str,
        target_schema: Dict[str, Any],
        tool_name: Optional[str] = None
    ) -> str:
        """Build prompt for the structure model"""
        schema_str = json.dumps(target_schema, indent=2)
        
        prompt = f"""Convert the following text into a structured JSON format.

Target Schema:
{schema_str}

Text to Convert:
{agent_output}

Instructions:
1. Extract relevant information from the text
2. Map it to the schema fields
3. Use only the fields defined in the schema
4. Return valid JSON

JSON Output:"""
        
        if tool_name:
            prompt = f"Tool: {tool_name}\n\n{prompt}"
        
        return prompt
    
    def _extract_json(self, generated_text: str, target_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract JSON from generated text"""
        try:
            # Find JSON in the generated text
            start_idx = generated_text.find("{")
            if start_idx == -1:
                # Try to find after "JSON Output:"
                marker = "JSON Output:"
                marker_idx = generated_text.find(marker)
                if marker_idx != -1:
                    start_idx = generated_text.find("{", marker_idx)
            
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


# Global instance for reuse
_structure_service: Optional[StructureService] = None


def get_structure_service() -> StructureService:
    """Get or create the global structure service instance"""
    global _structure_service
    if _structure_service is None:
        _structure_service = StructureService()
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