#!/usr/bin/env python3
"""
LLM Configuration Manager for LLM Wiki Agent.

This module handles interactive configuration of LLM settings.
Only supports OpenAI-compatible API format.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


# Configuration file path
CONFIG_FILE = Path(__file__).parent.parent / ".llm_config.json"


class LLMConfig:
    """Manage LLM configuration storage and retrieval."""

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one configuration instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def save_config(self):
        """Save configuration to file."""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(self.config, indent=2), encoding="utf-8")

    def is_configured(self) -> bool:
        """Check if LLM is properly configured."""
        return all(k in self.config for k in ["base_url", "model", "api_key"])

    def get_config(self) -> Dict[str, str]:
        """Get configuration as environment variables dict."""
        return {
            "LLM_PROVIDER": "openai",
            "LLM_BASE_URL": self.config.get("base_url", ""),
            "LLM_MODEL": self.config.get("model", ""),
            "OPENAI_API_KEY": self.config.get("api_key", ""),
        }

    def update_config(self, base_url: str, model: str, api_key: str):
        """Update configuration with new values."""
        self.config = {
            "base_url": base_url.strip(),
            "model": model.strip(),
            "api_key": api_key.strip(),
        }
        self.save_config()
        self._update_environment()

    def reload_config(self) -> "LLMConfig":
        """Reload configuration from file."""
        self.config = self._load_config()
        self._update_environment()
        return self

    def _update_environment(self):
        """Update system environment variables with current config."""
        for key, value in self.get_config().items():
            os.environ[key] = value

    def get_env_commands(self, shell: str = "bash") -> str:
        """Export configuration as shell commands."""
        cfg = self.get_config()
        if shell == "bash":
            return f'export LLM_PROVIDER="openai" LLM_BASE_URL="{cfg["LLM_BASE_URL"]}" LLM_MODEL="{cfg["LLM_MODEL"]}" OPENAI_API_KEY="{cfg["OPENAI_API_KEY"]}"'
        elif shell == "cmd":
            return f'set LLM_PROVIDER=openai && set LLM_BASE_URL={cfg["LLM_BASE_URL"]} && set LLM_MODEL={cfg["LLM_MODEL"]} && set OPENAI_API_KEY={cfg["OPENAI_API_KEY"]}'
        elif shell == "powershell":
            return f'$env:LLM_PROVIDER="openai"; $env:LLM_BASE_URL="{cfg["LLM_BASE_URL"]}"; $env:LLM_MODEL="{cfg["LLM_MODEL"]}"; $env:OPENAI_API_KEY="{cfg["OPENAI_API_KEY"]}"'
        return ""

    def __repr__(self) -> str:
        """String representation (hides API key)."""
        if not self.config:
            return "LLMConfig(not configured)"
        api_key_hidden = self.config.get("api_key", "")[:8] + "..." if len(self.config.get("api_key", "")) > 8 else "***"
        return f"LLMConfig(base_url={self.config.get('base_url')}, model={self.config.get('model')}, api_key={api_key_hidden})"


def check_llm_config() -> Optional[LLMConfig]:
    """
    Check if LLM is configured. Returns config if configured, None otherwise.

    This is the main entry point for workflow scripts.
    """
    config = LLMConfig()
    return config if config.is_configured() else None


def reload_llm_config() -> LLMConfig:
    """Reload LLM configuration from file."""
    return LLMConfig().reload_config()


def setup_llm_config_interactive(base_url: str, model: str, api_key: str) -> LLMConfig:
    """
    Setup LLM configuration interactively.

    Args:
        base_url: API base URL (e.g., https://api.openai.com/v1)
        model: Model name (e.g., gpt-4o-mini)
        api_key: API key

    Returns:
        Configured LLMConfig instance
    """
    config = LLMConfig()
    config.update_config(base_url, model, api_key)
    return config


def print_config_summary(config: LLMConfig):
    """Print configuration summary (for debugging)"""
    print(f"Configuration status: {'configured' if config.is_configured() else 'not configured'}")
    if config.is_configured():
        print(f"Current config: {config}")
        print(f"\nEnvironment commands (bash):")
        print(config.get_env_commands("bash"))


if __name__ == "__main__":
    # Test configuration
    config = LLMConfig()
    print_config_summary(config)
