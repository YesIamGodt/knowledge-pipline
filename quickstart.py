#!/usr/bin/env python3
"""
Quick start script for LLM Wiki Agent.

This script helps you get started with the wiki agent in seconds.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.llm_config import LLMConfig


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           LLM Wiki Agent — Quick Start                       ║
║                                                               ║
║    Build a personal knowledge base with any LLM              ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")


def check_config():
    """Check if LLM is configured."""
    config = LLMConfig()

    if config.is_configured():
        print("✅ LLM is configured!")
        print(f"   {config}")
        print()
        return True
    else:
        print("⚠️  LLM is not configured yet.")
        print()
        print("Don't worry! When you run your first wiki command,")
        print("Claude will guide you through the setup process.")
        print()
        print("For manual setup, run:")
        print("  python tools/demo_config.py")
        print()
        return False


def show_next_steps():
    """Show next steps for the user."""
    print("📚 Next Steps:")
    print("-" * 50)
    print()
    print("1. Add your first document:")
    print("   ingest raw/my-document.md")
    print()
    print("2. Query your knowledge:")
    print("   query: what are the main themes?")
    print()
    print("3. Build a knowledge graph:")
    print("   build the knowledge graph")
    print()
    print("For more information, see:")
    print("  - SETUP_GUIDE.md        — Complete setup guide")
    print("  - INTERACTIVE_CONFIG_EXAMPLE.md  — Configuration examples")
    print("  - README.md             — Full documentation")
    print()


def check_wiki_structure():
    """Check if wiki directory structure exists."""
    wiki_dir = Path("wiki")
    raw_dir = Path("raw")

    print("📁 Checking directory structure...")

    if not wiki_dir.exists():
        print("   Creating wiki/ directory...")
        wiki_dir.mkdir(parents=True, exist_ok=True)
        (wiki_dir / "sources").mkdir(exist_ok=True)
        (wiki_dir / "entities").mkdir(exist_ok=True)
        (wiki_dir / "concepts").mkdir(exist_ok=True)
        (wiki_dir / "syntheses").mkdir(exist_ok=True)
        print("   ✅ Created wiki/ directory structure")

    if not raw_dir.exists():
        print("   Creating raw/ directory...")
        raw_dir.mkdir(parents=True, exist_ok=True)
        print("   ✅ Created raw/ directory")

    print()


def main():
    print_banner()

    # Check directory structure
    check_wiki_structure()

    # Check LLM configuration
    has_config = check_config()

    # Show next steps
    show_next_steps()

    if not has_config:
        print("💡 Tip: Run 'python tools/demo_config.py' to configure LLM now,")
        print("         or wait until you run your first wiki command.")
        print()

    print("🚀 You're ready to go! Open this repo in Claude Code and start using wiki commands.")
    print()


if __name__ == "__main__":
    main()
