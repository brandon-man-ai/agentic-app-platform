"""LLM client factory for different providers."""

import os
import json
from typing import Any, Generator
import openai
import anthropic
from schemas import LLMModel, LLMModelConfig, FragmentSchema


class LLMClient:
    """Unified LLM client that supports multiple providers."""
    
    def __init__(self, model: LLMModel, config: LLMModelConfig):
        self.model = model
        self.config = config
        self.provider_id = model.providerId
        self.model_id = model.id
        
    def _get_openai_client(self, api_key: str | None = None, base_url: str | None = None) -> openai.OpenAI:
        """Create an OpenAI-compatible client."""
        return openai.OpenAI(
            api_key=api_key or self.config.apiKey,
            base_url=base_url or self.config.baseURL,
        )
    
    def _get_anthropic_client(self) -> anthropic.Anthropic:
        """Create an Anthropic client."""
        return anthropic.Anthropic(
            api_key=self.config.apiKey or os.getenv("ANTHROPIC_API_KEY"),
            base_url=self.config.baseURL,
        )
    
    def _get_generation_params(self) -> dict[str, Any]:
        """Get common generation parameters."""
        params = {}
        if self.config.temperature is not None:
            params["temperature"] = self.config.temperature
        if self.config.maxTokens is not None:
            params["max_tokens"] = self.config.maxTokens
        if self.config.topP is not None:
            params["top_p"] = self.config.topP
        return params
    
    def generate_structured(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        schema: dict[str, Any],
    ) -> Generator[str, None, None]:
        """Generate structured output with streaming."""
        
        # Convert messages to the format expected by the provider
        formatted_messages = self._format_messages(messages)
        
        if self.provider_id == "anthropic":
            yield from self._generate_anthropic(system_prompt, formatted_messages, schema)
        elif self.provider_id == "openai":
            yield from self._generate_openai(
                system_prompt, formatted_messages, schema,
                api_key=self.config.apiKey or os.getenv("OPENAI_API_KEY"),
            )
        elif self.provider_id == "groq":
            yield from self._generate_openai(
                system_prompt, formatted_messages, schema,
                api_key=self.config.apiKey or os.getenv("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1",
            )
        elif self.provider_id == "togetherai":
            yield from self._generate_openai(
                system_prompt, formatted_messages, schema,
                api_key=self.config.apiKey or os.getenv("TOGETHER_API_KEY"),
                base_url="https://api.together.xyz/v1",
            )
        elif self.provider_id == "fireworks":
            yield from self._generate_openai(
                system_prompt, formatted_messages, schema,
                api_key=self.config.apiKey or os.getenv("FIREWORKS_API_KEY"),
                base_url="https://api.fireworks.ai/inference/v1",
            )
        elif self.provider_id == "xai":
            yield from self._generate_openai(
                system_prompt, formatted_messages, schema,
                api_key=self.config.apiKey or os.getenv("XAI_API_KEY"),
                base_url="https://api.x.ai/v1",
            )
        elif self.provider_id == "deepseek":
            yield from self._generate_openai(
                system_prompt, formatted_messages, schema,
                api_key=self.config.apiKey or os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com/v1",
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider_id}")
    
    def _format_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format messages for the LLM provider."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Handle different content types
            if isinstance(content, list):
                # Extract text from content list
                text_parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = "\n".join(text_parts)
            
            formatted.append({"role": role, "content": content})
        
        return formatted
    
    def _generate_anthropic(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        schema: dict[str, Any],
    ) -> Generator[str, None, None]:
        """Generate using Anthropic API."""
        client = self._get_anthropic_client()
        params = self._get_generation_params()
        
        # Add JSON mode instruction to system prompt
        json_system = f"""{system_prompt}

You must respond with a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with the JSON object, no additional text."""

        with client.messages.stream(
            model=self.model_id,
            system=json_system,
            messages=messages,
            max_tokens=params.get("max_tokens", 8192),
            **{k: v for k, v in params.items() if k != "max_tokens"},
        ) as stream:
            for text in stream.text_stream:
                yield text
    
    def _generate_openai(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        schema: dict[str, Any],
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> Generator[str, None, None]:
        """Generate using OpenAI-compatible API."""
        client = self._get_openai_client(api_key, base_url)
        params = self._get_generation_params()
        
        # Add JSON mode instruction
        json_system = f"""{system_prompt}

You must respond with a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with the JSON object, no additional text."""

        all_messages = [{"role": "system", "content": json_system}] + messages
        
        stream = client.chat.completions.create(
            model=self.model_id,
            messages=all_messages,
            stream=True,
            response_format={"type": "json_object"},
            **params,
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def get_fragment_schema() -> dict[str, Any]:
    """Get the JSON schema for FragmentSchema."""
    return {
        "type": "object",
        "properties": {
            "commentary": {
                "type": "string",
                "description": "Describe what you're about to do and the steps you want to take for generating the fragment in great detail."
            },
            "template": {
                "type": "string",
                "description": "Name of the template used to generate the fragment."
            },
            "title": {
                "type": "string",
                "description": "Short title of the fragment. Max 3 words."
            },
            "description": {
                "type": "string",
                "description": "Short description of the fragment. Max 1 sentence."
            },
            "additional_dependencies": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Additional dependencies required by the fragment."
            },
            "has_additional_dependencies": {
                "type": "boolean",
                "description": "Detect if additional dependencies are required."
            },
            "install_dependencies_command": {
                "type": "string",
                "description": "Command to install additional dependencies."
            },
            "port": {
                "type": ["integer", "null"],
                "description": "Port number used by the resulted fragment."
            },
            "file_path": {
                "type": "string",
                "description": "Relative path to the file, including the file name."
            },
            "code": {
                "type": "string",
                "description": "Code generated by the fragment. Only runnable code is allowed."
            }
        },
        "required": ["commentary", "template", "title", "description", "additional_dependencies", 
                     "has_additional_dependencies", "install_dependencies_command", "port", 
                     "file_path", "code"]
    }


def get_morph_edit_schema() -> dict[str, Any]:
    """Get the JSON schema for MorphEditSchema."""
    return {
        "type": "object",
        "properties": {
            "commentary": {
                "type": "string",
                "description": "Explain what changes you are making and why"
            },
            "instruction": {
                "type": "string",
                "description": "One line instruction on what the change is"
            },
            "edit": {
                "type": "string",
                "description": "The code changes with // ... existing code ... for unchanged parts"
            },
            "file_path": {
                "type": "string",
                "description": "Path to the file being edited"
            }
        },
        "required": ["commentary", "instruction", "edit", "file_path"]
    }

