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
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """Call a model via OpenRouter using LangChain

        Args:
            model: Model identifier (e.g., "openai/gpt-4", "anthropic/claude-3-opus")
            messages: List of message dicts with "role" and "content" keys
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            max_retries: Maximum number of retries for empty responses
            **kwargs: Additional parameters (ignored for now)

        Returns:
            Generated text response
        """
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

        # Retry logic for handling transient empty responses
        last_error = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"[CLIENT] Retry attempt {attempt + 1}/{max_retries}")
                    import time
                    time.sleep(1)  # Brief delay between retries

                # Create a FRESH LLM instance for each attempt
                # This prevents state/connection reuse issues in LangChain
                llm = self._create_llm(model, temperature, max_tokens)

                return self._invoke_model(llm, langchain_messages, model)

            except ValueError as ve:
                # Empty response error - retry
                last_error = ve
                if attempt < max_retries - 1:
                    print(f"[CLIENT] Empty response on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    raise
            except Exception as e:
                # Other errors - don't retry
                raise

        # If we exhausted all retries
        raise last_error if last_error else RuntimeError(f"Failed to get response from {model} after {max_retries} attempts")

    def _invoke_model(
        self,
        llm: ChatOpenAI,
        langchain_messages: List[BaseMessage],
        model: str
    ) -> str:
        """Internal method to invoke the model and extract content"""
        try:
            print(f"\n[CLIENT] Calling OpenRouter API for model: {model}")
            print(f"[CLIENT] Messages count: {len(langchain_messages)}")
            print(f"[CLIENT] Temperature: {llm.temperature}")
            print(f"[CLIENT] Max tokens: {getattr(llm, 'max_tokens', 'default')}")

            response = llm.invoke(langchain_messages)

            print(f"[CLIENT] Response received")
            print(f"[CLIENT] Response type: {type(response)}")
            print(f"[CLIENT] Response has content attr: {hasattr(response, 'content')}")

            # Check additional_kwargs for error messages
            if hasattr(response, 'additional_kwargs'):
                print(f"[CLIENT] Additional kwargs: {response.additional_kwargs}")

            # Check response_metadata for error info
            if hasattr(response, 'response_metadata'):
                print(f"[CLIENT] Response metadata: {response.response_metadata}")

            # Check for content_blocks (some models use this)
            if hasattr(response, 'content_blocks'):
                print(f"[CLIENT] Has content_blocks: {response.content_blocks}")

            # Extract text from response - handle multiple possible formats
            content = None
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            elif hasattr(response, 'content_blocks') and response.content_blocks:
                # Some models return content in blocks
                content = ' '.join([block.get('text', '') for block in response.content_blocks if isinstance(block, dict)])
            else:
                content = str(response)

            print(f"[CLIENT] Extracted content type: {type(content)}")
            print(f"[CLIENT] Content repr: {repr(content)}")
            print(f"[CLIENT] Content length: {len(content) if content else 0}")
            print(f"[CLIENT] Content is None: {content is None}")
            print(f"[CLIENT] Content is empty string: {content == ''}")
            print(f"[CLIENT] Content equals empty list: {content == []}")

            # Handle case where content might be a list or other type
            if isinstance(content, list):
                print(f"[CLIENT] Content is a list with {len(content)} items")
                if content:
                    content = ' '.join([str(item) for item in content])
                else:
                    content = ""

            if content:
                print(f"[CLIENT] Content stripped length: {len(content.strip())}")
                print(f"[CLIENT] First 100 chars: '{content[:100]}'")

            if not content or (isinstance(content, str) and len(content.strip()) == 0):
                print(f"[CLIENT] ERROR: Empty content detected!")
                print(f"[CLIENT] Full response object type: {type(response)}")
                print(f"[CLIENT] Full response object dir: {dir(response)}")
                print(f"[CLIENT] Full response object: {response}")
                raise ValueError(f"Model {model} returned an empty response. The model may not exist or may have failed.")

            print(f"[CLIENT] Success! Returning {len(content)} chars")
            return str(content)  # Ensure we always return a string
        except ValueError as ve:
            # Don't wrap ValueError, let it propagate
            raise
        except Exception as e:
            # Re-raise with more context
            print(f"[CLIENT] Exception during API call: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Error calling model {model}: {str(e)}") from e

