#!/usr/bin/env python3
"""
Demo script showing how to use the LLM configuration system.

This simulates what Claude Code does when a user runs /wiki-ingest without configuration.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_config import LLMConfig, setup_llm_config_interactive


def check_and_configure():
    """Check if LLM is configured, and if not, guide through setup."""
    config = LLMConfig()

    if config.is_configured():
        print("✅ LLM already configured!")
        print(f"   {config}")
        return True

    # Interactive configuration
    print("\n" + "="*60)
    print("⚠️  LLM Configuration Required")
    print("="*60)
    print("\nTo use wiki commands, you need to configure your LLM API.\n")

    # Step 1: Provider selection
    print("Step 1: Choose your LLM provider")
    print("-" * 40)
    print("  [1] OpenAI (https://api.openai.com/v1)")
    print("  [2] DeepSeek (https://api.deepseek.com/v1)")
    print("  [3] Ollama (local, http://localhost:11434/v1)")
    print("  [4] Custom OpenAI-compatible endpoint")

    choice = input("\nEnter choice (1-4): ").strip()

    providers = {
        "1": ("OpenAI", "https://api.openai.com/v1"),
        "2": ("DeepSeek", "https://api.deepseek.com/v1"),
        "3": ("Ollama", "http://localhost:11434/v1"),
    }

    if choice in providers:
        provider_name, base_url = providers[choice]
        print(f"\n✓ Selected: {provider_name}")
        print(f"  Base URL: {base_url}")
    elif choice == "4":
        base_url = input("\nEnter your API base URL (e.g., https://api.example.com/v1): ").strip()
        provider_name = "Custom"
    else:
        print("Invalid choice. Exiting.")
        return False

    # Step 2: Model name
    print("\nStep 2: Enter your model name")
    print("-" * 40)

    if choice == "1":
        default = "gpt-4o-mini"
    elif choice == "2":
        default = "deepseek-chat"
    elif choice == "3":
        default = "llama3.2"
    else:
        default = "model-name"

    model = input(f"Model name [{default}]: ").strip() or default
    print(f"✓ Model: {model}")

    # Step 3: API key
    print("\nStep 3: Enter your API key")
    print("-" * 40)

    if choice == "3":
        print("Note: Ollama typically doesn't require an API key.")
        api_key = input("API key (press Enter to skip): ").strip() or "dummy-key"
    else:
        api_key = input("API key (will be saved locally): ").strip()
        if not api_key:
            print("API key is required. Exiting.")
            return False

    # Save configuration
    print("\nSaving configuration...")
    setup_llm_config_interactive(base_url, model, api_key)

    print("\n" + "="*60)
    print("✅ Configuration saved successfully!")
    print("="*60)
    print(f"\nProvider: {provider_name}")
    print(f"Model: {model}")
    print(f"Base URL: {base_url}")

    # Show how to use in shell scripts
    print("\n" + "-"*60)
    print("To use in shell scripts, export environment variables:")
    print("-"*60)
    config = LLMConfig()
    print(f"\n{config.get_env_commands('bash')}\n")

    return True


if __name__ == "__main__":
    success = check_and_configure()
    sys.exit(0 if success else 1)
