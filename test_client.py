"""Test the LangChain-based OpenRouter client"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from debatebench import OpenRouterClient

try:
    # Initialize client (should load from .env)
    client = OpenRouterClient()
    print("✓ Client initialized successfully")
    print(f"✓ API key loaded: {'Yes' if client.api_key else 'No'}")
    
    # Test that we can create an LLM instance (without actually calling it)
    try:
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        # Just verify imports work
        print("✓ LangChain imports successful")
        print("✓ python-dotenv import successful")
        print("\nClient is ready to use!")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Please run: pip install -r requirements.txt")
        
except ValueError as e:
    print(f"✗ Error: {e}")
    print("Make sure you have OPENROUTER_API_KEY in your .env file")

