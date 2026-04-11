#!/usr/bin/env python3
"""
Export LLM configuration as environment variables for shell scripts.

Usage:
    # Bash
    eval $(python tools/export_config.py)

    # Or directly in Python
    from tools.export_config import get_llm_env
    import os
    os.environ.update(get_llm_env())
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_config import LLMConfig


def get_llm_env() -> dict:
    """Get LLM configuration as environment variables dict."""
    config = LLMConfig()
    if not config.is_configured():
        return {}
    return config.get_config()


def print_shell_exports(shell: str = "bash"):
    """Print shell export commands."""
    config = LLMConfig()
    if not config.is_configured():
        print("# LLM not configured. Run a wiki command to configure.", file=sys.stderr)
        sys.exit(1)

    print(config.get_env_commands(shell))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export LLM configuration as environment variables")
    parser.add_argument("--shell", default="bash", choices=["bash", "cmd", "powershell"], help="Shell type")
    args = parser.parse_args()

    print_shell_exports(args.shell)
