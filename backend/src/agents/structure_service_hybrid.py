"""
Module: structure_service_hybrid
Purpose: Convert unstructured agent outputs to structured tool inputs using local inference
Dependencies: transformers, torch, pydantic
Used By: All agents for tool call formatting
"""

import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pydantic import BaseModel, Field, create_model
from typing import Dict, Any, List, Optional, Type, Union
import logging
import json
import asyncio
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class StructureServiceHybrid:
    """
    Converts agent outputs to structured tool inputs using local model inference.
    Falls back to simpler extraction if model is unavailable.
    """
    
    def __init__(self, use_model: bool = True):
        """Initialize the structure service"""
        self.use_model = use_model
        self.model = None
        self.tokenizer = None
        
        if self.use_model:
            try:
                self._load_model()
            except Exception as e:
                logger.warning(f"Failed to load model, using fallback mode: {e}")
                self.use_model = False
    
    def _load_model(self):
        """Load the Osmosis-Structure model"""
        model_name = "osmosis-ai/Osmosis-Structure-0.6B"
        logger.info(f"Loading {model_name} for structured output generation...")
        
        # Get HuggingFace token
        hf_token = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            token=hf_token
        )
        
        # Determine device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True,
            token=hf_token,
            low_cpu_mem_usage=True  # Optimize memory usage
        )
        
        if not torch.cuda.is_available():
            self.model = self.model.to(self.device)
        
        self.model.eval()
        logger.info("Model loaded successfully")
    
    async def structure_agent_output(
        self,
        agent_output: str,
        target_schema: Dict[str, Any],
        tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transform unstructured agent output to tool-ready structure.
        """
        if self.use_model and self.model is not None:
            # Use model-based extraction
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._model_based_extraction,
                agent_output,
                target_schema,
                tool_name
            )
        else:
            # Use rule-based extraction
            return self._rule_based_extraction(agent_output, target_schema, tool_name)
    
    def _model_based_extraction(
        self,
        agent_output: str,
        target_schema: Dict[str, Any],
        tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structure using the model"""
        try:
            prompt = self._build_extraction_prompt(agent_output, target_schema, tool_name)
            
            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract JSON
            return self._extract_json_from_text(generated_text, target_schema)
            
        except Exception as e:
            logger.error(f"Model extraction failed: {e}")
            return self._rule_based_extraction(agent_output, target_schema, tool_name)
    
    def _rule_based_extraction(
        self,
        agent_output: str,
        target_schema: Dict[str, Any],
        tool_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structure using rules and heuristics"""
        result = {}
        
        # Convert agent_output to dict if it's a JSON string
        if isinstance(agent_output, str):
            # Check if this is a TOOL_CALL format from the LLM
            if "TOOL_CALL:" in agent_output and "ARGUMENTS:" in agent_output:
                try:
                    # Extract the JSON from ARGUMENTS section
                    args_start = agent_output.find("ARGUMENTS:") + len("ARGUMENTS:")
                    args_end = agent_output.find("}", args_start) + 1
                    if args_end > args_start:
                        json_str = agent_output[args_start:args_end].strip()
                        agent_data = json.loads(json_str)
                    else:
                        agent_data = {"content": agent_output}
                except (json.JSONDecodeError, ValueError):
                    agent_data = {"content": agent_output}
            else:
                try:
                    # Try to parse as JSON first
                    agent_data = json.loads(agent_output)
                except json.JSONDecodeError:
                    # If not JSON, create a simple dict
                    agent_data = {"content": agent_output}
        else:
            agent_data = agent_output
        
        # Map fields based on schema and tool name
        for field_name, field_type in target_schema.items():
            # Try to find matching data in agent output
            value = None
            
            # Direct mapping
            if field_name in agent_data:
                value = agent_data[field_name]
            # Tool-specific mappings
            elif tool_name == "call_research_team":
                if field_name == "task_description":
                    value = agent_data.get("research_type", agent_data.get("task", 
                            agent_data.get("description", agent_data.get("content", agent_data.get("raw", "")))))
                elif field_name == "priority":
                    value = agent_data.get("priority", "medium")
            elif tool_name == "call_rating_team":
                if field_name == "task_description":
                    value = agent_data.get("content_to_rate", agent_data.get("task", 
                            agent_data.get("description", agent_data.get("content", agent_data.get("raw", "")))))
                elif field_name == "evaluation_criteria":
                    value = agent_data.get("rating_criteria", agent_data.get("criteria", []))
                elif field_name == "content_to_review":
                    value = agent_data.get("content_to_review", agent_data.get("content", ""))
            # Common aliases for all tools
            elif field_name == "task_description":
                value = agent_data.get("task", agent_data.get("description", 
                        agent_data.get("content", agent_data.get("raw", ""))))
            elif field_name == "message":
                value = agent_data.get("message", agent_data.get("content", 
                        agent_data.get("raw", "")))
            elif field_name == "message_type":
                value = agent_data.get("type", agent_data.get("message_type", "update"))
            elif field_name == "analysis_type":
                value = agent_data.get("analysis_type", agent_data.get("type", "general"))
            elif field_name == "content_type":
                value = agent_data.get("content_type", agent_data.get("type", "report"))
            elif field_name == "tone":
                value = agent_data.get("tone", "formal")
            elif field_name == "priority":
                value = agent_data.get("priority", "medium")
            elif field_name == "data_sources":
                value = agent_data.get("data_sources", agent_data.get("sources", []))
            elif field_name == "evaluation_criteria":
                value = agent_data.get("evaluation_criteria", agent_data.get("criteria", []))
            elif field_name == "content_to_review":
                value = agent_data.get("content_to_review", agent_data.get("content", ""))
            elif field_name == "context":
                value = agent_data.get("context", {})
            
            # Apply type conversion
            if value is not None:
                result[field_name] = self._convert_to_type(value, field_type)
            else:
                result[field_name] = self._get_default_value(field_type)
        
        return result
    
    def _convert_to_type(self, value: Any, field_type: Union[str, type]) -> Any:
        """Convert value to the expected type"""
        if field_type == "string" or field_type == str:
            return str(value)
        elif field_type == "boolean" or field_type == bool:
            return bool(value)
        elif field_type == "integer" or field_type == int:
            return int(value) if isinstance(value, (int, float, str)) else 0
        elif field_type == "list" or field_type == list:
            return value if isinstance(value, list) else []
        elif field_type == "dict" or field_type == dict:
            return value if isinstance(value, dict) else {}
        return value
    
    def _get_default_value(self, field_type: Union[str, type]) -> Any:
        """Get default value for a field type"""
        if field_type == "string" or field_type == str:
            return ""
        elif field_type == "boolean" or field_type == bool:
            return False
        elif field_type == "integer" or field_type == int:
            return 0
        elif field_type == "list" or field_type == list:
            return []
        elif field_type == "dict" or field_type == dict:
            return {}
        return None
    
    def _build_extraction_prompt(
        self,
        agent_output: str,
        target_schema: Dict[str, Any],
        tool_name: Optional[str] = None
    ) -> str:
        """Build prompt for extraction"""
        schema_str = json.dumps(target_schema, indent=2)
        
        prompt = f"""Extract information into JSON format.

Schema:
{schema_str}

Text:
{agent_output}

JSON:"""
        
        return prompt
    
    def _extract_json_from_text(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract JSON from generated text"""
        try:
            # Find JSON in text
            start_idx = text.find("{")
            if start_idx != -1:
                end_idx = text.rfind("}") + 1
                if end_idx > start_idx:
                    json_str = text[start_idx:end_idx]
                    return json.loads(json_str)
        except:
            pass
        
        # Fallback to rule-based
        return self._rule_based_extraction(text, schema)


# Global instance
_structure_service: Optional[StructureServiceHybrid] = None


def get_structure_service() -> StructureServiceHybrid:
    """Get or create the global structure service instance"""
    global _structure_service
    if _structure_service is None:
        # Start with rule-based extraction to avoid blocking on model load
        _structure_service = StructureServiceHybrid(use_model=False)
    return _structure_service


# Tool schemas - Updated to match actual function signatures
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