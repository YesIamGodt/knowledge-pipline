#!/usr/bin/env python3
"""
LLM Wiki Agent - Demo Launcher

Quick launch script for the demo application.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required = ['flask', 'flask_cors']
    missing = []

    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)

    if missing:
        print("❌ Missing dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n📦 Install with: pip install -r requirements.txt")
        return False

    return True

def check_llm_config():
    """Check if LLM is configured."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.llm_config import LLMConfig

    config = LLMConfig()
    if not config.is_configured():
        print("⚠️  LLM not configured yet.")
        print("   You can configure it through the web interface.")
        print("   Visit: http://localhost:5000")
        return False

    print(f"✅ LLM configured: {config.config.get('model', 'unknown')}")
    return True

def main():
    print("🚀 LLM Wiki Agent - Demo Launcher")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check LLM config
    check_llm_config()

    print("\n🌐 Starting Flask server...")
    print("   URL: http://localhost:5000")
    print("   Press Ctrl+C to stop\n")

    # Launch the app
    demo_dir = Path(__file__).parent
    app_path = demo_dir / "app.py"

    try:
        subprocess.run([sys.executable, str(app_path)], cwd=str(demo_dir))
    except KeyboardInterrupt:
        print("\n\n👋 Demo stopped. Thanks for using LLM Wiki Agent!")
    except Exception as e:
        print(f"\n❌ Error starting demo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
