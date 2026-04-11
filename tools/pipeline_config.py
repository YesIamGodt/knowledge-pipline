#!/usr/bin/env python3
"""
LLM 配置管理工具

用于交互式配置 LLM API 信息，支持 OpenAI、自定义 OpenAI 兼容端点、Ollama 本地模型。
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_config import LLMConfig, setup_llm_config_interactive


def print_current_config(config: LLMConfig):
    """打印当前配置（隐藏 API 密钥）"""
    print("=" * 60)
    print("📋 当前 LLM 配置")
    print("=" * 60)
    if config.is_configured():
        api_key_hidden = config.config.get("api_key", "")[:8] + "..." if len(config.config.get("api_key", "")) > 8 else "***"
        print(f"🎯 提供商: {'OpenAI' if 'openai.com' in config.config['base_url'] else 'Ollama' if 'localhost:11434' in config.config['base_url'] else '自定义'}")
        print(f"🌐 基础 URL: {config.config['base_url']}")
        print(f"🤖 模型: {config.config['model']}")
        print(f"🔑 API 密钥: {api_key_hidden}")
    else:
        print("⚠️ LLM 未配置")
    print()


def configure_llm_interactive():
    """交互式配置 LLM API"""
    print("=" * 60)
    print("🚀 LLM API 配置向导")
    print("=" * 60)
    print()

    config = LLMConfig()

    # 显示当前配置（如果有）
    if config.is_configured():
        print_current_config(config)
        print("=" * 60)
        response = input("🔄 是否要重新配置 LLM API？(y/N): ").strip().lower()
        if response not in ["y", "yes"]:
            print("✅ 保持当前配置")
            return False

    print("\n" + "=" * 60)
    print("🏪 选择 LLM 提供商")
    print("=" * 60)
    print("1. OpenAI (https://api.openai.com/v1)")
    print("2. 自定义 OpenAI 兼容端点")
    print("3. Ollama (本地模型服务)")
    print()

    while True:
        choice = input("请输入选择 (1-3): ").strip()

        if choice == "1":  # OpenAI
            base_url = "https://api.openai.com/v1"
            print("\n✅ 已选择 OpenAI")
            print(f"🌐 基础 URL: {base_url}")
            break

        elif choice == "2":  # 自定义 OpenAI 兼容
            base_url = input("\n🌐 输入 API 基础 URL (例如: https://api.deepseek.com/v1): ").strip()
            if not base_url.startswith("http"):
                print("⚠️  无效的 URL，必须以 http:// 或 https:// 开头")
                continue
            print("✅ 自定义端点已设置")
            break

        elif choice == "3":  # Ollama 本地
            base_url = "http://localhost:11434/v1"
            print("\n✅ 已选择 Ollama (本地模型)")
            print(f"🌐 基础 URL: {base_url}")
            break

        else:
            print("⚠️  无效选择，请输入 1-3")

    print()
    print("=" * 60)
    print("🤖 模型配置")
    print("=" * 60)

    if base_url == "https://api.openai.com/v1":  # OpenAI
        model = input("📝 输入模型名称 (默认: gpt-4o-mini): ").strip()
        model = model or "gpt-4o-mini"
        examples = ["gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]

    elif base_url == "http://localhost:11434/v1":  # Ollama
        model = input("📝 输入模型名称 (默认: llama3.2): ").strip()
        model = model or "llama3.2"
        examples = ["llama3.2", "qwen2", "mixtral"]

    else:  # 自定义
        model = input("📝 输入模型名称 (例如: deepseek-chat): ").strip()
        if not model:
            print("⚠️  模型名称不能为空")
            continue
        examples = ["deepseek-chat", "meta-llama/Llama-3-8b-chat-hf", "anthropic/claude-3-opus"]

    print()
    print("=" * 60)
    print("🔑 API 密钥配置")
    print("=" * 60)

    if base_url == "http://localhost:11434/v1":  # Ollama 不需要 API 密钥
        api_key = ""
        print("ℹ️  Ollama 本地模型服务不需要 API 密钥")
    else:
        api_key = input("🔑 输入 API 密钥: ").strip()
        if not api_key:
            print("⚠️  API 密钥不能为空")
            continue

    print()
    print("=" * 60)
    print("📋 配置预览")
    print("=" * 60)
    print(f"🏪 提供商: {'OpenAI' if base_url == 'https://api.openai.com/v1' else 'Ollama' if base_url == 'http://localhost:11434/v1' else '自定义'}")
    print(f"🌐 基础 URL: {base_url}")
    print(f"🤖 模型: {model}")
    print(f"🔑 API 密钥: {'***' if api_key else '未设置'}")
    print()

    # 确认配置
    confirm = input("✅ 确认配置？(Y/n): ").strip().lower()
    if confirm and confirm not in ["y", "yes"]:
        print("\n❌ 配置已取消")
        return False

    # 保存配置
    try:
        setup_llm_config_interactive(base_url, model, api_key)
        print("\n✅ 配置已成功保存到 .llm_config.json")

        # 验证配置
        new_config = LLMConfig()
        if new_config.is_configured():
            print("✅ 配置验证通过")
            print_current_config(new_config)
        else:
            print("❌ 配置验证失败")
            return False

        return True

    except Exception as e:
        print(f"\n❌ 配置失败: {e}")
        return False


def main():
    """主函数"""
    print("LLM 配置管理工具")
    print("=" * 60)

    try:
        success = configure_llm_interactive()

        if success:
            print("\n🎉 配置完成！")
            print("💡 所有 wiki 命令现在将使用新配置。")
            print("💡 您可以运行 /pipeline-query 来测试新配置是否工作正常。")
        else:
            print("\nℹ️  配置过程已结束")
            return 1

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  操作被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
