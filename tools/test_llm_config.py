#!/usr/bin/env python3
"""Test script to verify LLM provider configuration."""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

def test_claude():
    """Test Claude API."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'Claude works!' in JSON format"}]
        )
        print(f"✅ Claude: {response.content[0].text.strip()}")
        return True
    except Exception as e:
        print(f"❌ Claude failed: {e}")
        return False

def test_openai():
    """Test OpenAI API."""
    try:
        import openai
        client = openai.OpenAI(
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("OPENAI_API_KEY")
        )
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'OpenAI works!' in JSON format"}],
            max_tokens=50
        )
        print(f"✅ OpenAI ({model}): {response.choices[0].message.content.strip()}")
        return True
    except Exception as e:
        print(f"❌ OpenAI failed: {e}")
        return False

def test_ollama():
    """Test Ollama API."""
    try:
        import requests
        base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
        model = os.getenv("LLM_MODEL", "llama3.2")
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": "Say 'Ollama works!'", "stream": False},
            timeout=30
        )
        response.raise_for_status()
        print(f"✅ Ollama ({model}): {response.json().get('response', '')[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Ollama failed: {e}")
        return False

def main():
    provider = os.getenv("LLM_PROVIDER", "claude")
    print(f"Testing LLM Provider: {provider}\n")

    if provider == "claude":
        success = test_claude()
    elif provider == "openai":
        success = test_openai()
    elif provider == "ollama":
        success = test_ollama()
    else:
        print(f"❌ Unknown provider: {provider}")
        sys.exit(1)

    if success:
        print(f"\n✅ {provider.upper()} is configured correctly!")
        sys.exit(0)
    else:
        print(f"\n❌ {provider.upper()} configuration failed. Check your API keys and settings.")
        sys.exit(1)

if __name__ == "__main__":
    main()
