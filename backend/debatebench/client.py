"""OpenRouter API client for model interactions using LangChain"""

import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage


# Load environment variables from .env file
load_dotenv()


class OpenRouterClient:
    """Client for interacting with models via OpenRouter API using LangChain"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenRouter client
        
        Args:
            api_key: OpenRouter API key. If not provided, reads from OPENROUTER_API_KEY env var
                     or .env file.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY in .env file "
                "or pass api_key parameter."
            )
        self.base_url = "https://openrouter.ai/api/v1"
    
    def _create_llm(
        self,
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> ChatOpenAI:
        """Create a LangChain ChatOpenAI instance configured for OpenRouter"""
        kwargs = {
            "model": model,
            "temperature": temperature,
            "openai_api_key": self.api_key,
            "openai_api_base": self.base_url,
            "default_headers": {
                "HTTP-Referer": "https://github.com/debatebench"
            }
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        
        return ChatOpenAI(**kwargs)
    
    def call_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Call a model via OpenRouter using LangChain
        
        Args:
            model: Model identifier (e.g., "openai/gpt-4", "anthropic/claude-3-opus")
            messages: List of message dicts with "role" and "content" keys
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters (ignored for now)
            
        Returns:
            Generated text response
        """
        # Create LLM instance
        llm = self._create_llm(model, temperature, max_tokens)
        
        # Convert messages to LangChain format
        langchain_messages: List[BaseMessage] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
        
        # Invoke the model
        response = llm.invoke(langchain_messages)
        
        # Extract text from response
        return response.content

