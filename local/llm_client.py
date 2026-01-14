#!/usr/bin/env python3
"""
LLM Client Abstraction Layer
Supports both Azure OpenAI and Anthropic Claude for local testing.
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Optional


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str, 
             temperature: float = 0.3, json_mode: bool = False,
             max_tokens: int = 4000) -> str:
        """Send a chat message and get a response."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the LLM provider."""
        pass


class ClaudeClient(LLMClient):
    """Anthropic Claude client."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        try:
            import anthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
        
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
    
    @property
    def name(self) -> str:
        return f"Claude ({self.model})"
    
    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.3, json_mode: bool = False,
             max_tokens: int = 4000) -> str:
        """Send a chat message to Claude."""
        
        # If JSON mode, add instruction to system prompt
        if json_mode:
            system_prompt = f"{system_prompt}\n\nIMPORTANT: You must respond with valid JSON only. No markdown code blocks, no explanations - just the raw JSON object."
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.content[0].text
        
        # Clean up JSON response if needed
        if json_mode:
            content = content.strip()
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        
        return content


class AzureOpenAIClient(LLMClient):
    """Azure OpenAI client."""
    
    def __init__(self, api_key: Optional[str] = None, 
                 endpoint: Optional[str] = None,
                 deployment: Optional[str] = None):
        try:
            from openai import AzureOpenAI
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        
        self.api_key = api_key or os.environ.get('AZURE_OPENAI_KEY')
        self.endpoint = endpoint or os.environ.get('AZURE_OPENAI_ENDPOINT')
        self.deployment = deployment or os.environ.get('AZURE_OPENAI_DEPLOYMENT')
        
        if not all([self.api_key, self.endpoint, self.deployment]):
            raise ValueError("Azure OpenAI requires AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT")
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version="2024-02-01",
            azure_endpoint=self.endpoint
        )
    
    @property
    def name(self) -> str:
        return f"Azure OpenAI ({self.deployment})"
    
    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.3, json_mode: bool = False,
             max_tokens: int = 4000) -> str:
        """Send a chat message to Azure OpenAI."""
        
        kwargs = {
            "model": self.deployment,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


def create_client(provider: str = "claude") -> LLMClient:
    """Factory function to create the appropriate LLM client.
    
    Args:
        provider: Either "claude" or "azure"
    
    Returns:
        An LLMClient instance
    """
    if provider.lower() == "claude":
        return ClaudeClient()
    elif provider.lower() == "azure":
        return AzureOpenAIClient()
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'claude' or 'azure'")
