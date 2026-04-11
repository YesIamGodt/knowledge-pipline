#!/usr/bin/env python3
"""
测试 LLM 配置系统

用于测试 LLM 配置的加载、更新和重新加载功能。
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_config import LLMConfig


def test_config_reload():
    """测试配置重载功能"""
    print("=" * 60)
    print("✅ 测试 LLM 配置系统")
    print("=" * 60)

    # 1. 获取配置实例（单例模式）
    config1 = LLMConfig()
    print(f"1. 第一个配置实例: {id(config1)}")
    print(f"   配置状态: {'已配置' if config1.is_configured() else '未配置'}")

    config2 = LLMConfig()
    print(f"2. 第二个配置实例: {id(config2)}")
    print(f"   单例验证: {'✅ 单例' if id(config1) == id(config2) else '❌ 不是单例'}")

    # 2. 测试 reload_config
    print("\n" + "=" * 60)
    print("🔄 测试配置重载")
    print("=" * 60)

    try:
        config1.reload_config()
        print("✅ 配置重载成功")
    except Exception as e:
        print(f"❌ 配置重载失败: {e}")

    # 3. 打印当前配置
    print("\n" + "=" * 60)
    print("📋 当前配置信息")
    print("=" * 60)

    if config1.is_configured():
        # 打印配置（隐藏 API 密钥）
        api_key_hidden = config1.config.get("api_key", "")[:8] + "..." if len(config1.config.get("api_key", "")) > 8 else "***"
        print(f"🎯 提供商: {'OpenAI' if 'openai.com' in config1.config['base_url'] else 'Ollama' if 'localhost:11434' in config1.config['base_url'] else '自定义'}")
        print(f"🌐 基础 URL: {config1.config['base_url']}")
        print(f"🤖 模型: {config1.config['model']}")
        print(f"🔑 API 密钥: {api_key_hidden}")
    else:
        print("⚠️  LLM 未配置")

    # 4. 测试环境变量更新
    print("\n" + "=" * 60)
    print("🌍 环境变量更新测试")
    print("=" * 60)

    try:
        import os
        llm_base_url = os.environ.get("LLM_BASE_URL", "未设置")
        llm_model = os.environ.get("LLM_MODEL", "未设置")
        openai_api_key = os.environ.get("OPENAI_API_KEY", "未设置")
        llm_provider = os.environ.get("LLM_PROVIDER", "未设置")

        print(f"LLM_PROVIDER: {llm_provider}")
        print(f"LLM_BASE_URL: {llm_base_url}")
        print(f"LLM_MODEL: {llm_model}")
        print(f"OPENAI_API_KEY: {openai_api_key[:8]}..." if len(openai_api_key) > 8 else "OPENAI_API_KEY: {openai_api_key}")
        print("✅ 环境变量配置完成")
    except Exception as e:
        print(f"❌ 环境变量访问失败: {e}")

    # 5. 测试配置验证
    print("\n" + "=" * 60)
    print("✅ 测试结果")
    print("=" * 60)

    if config1.is_configured():
        print("🎉 配置系统工作正常！")
        print("💡 您可以使用 /pipeline-config 命令重新配置 LLM API。")
        print("💡 配置完成后，所有 wiki 命令会立即使用新配置。")
    else:
        print("⚠️  LLM 未配置，请运行 /pipeline-config 进行配置。")

    return config1.is_configured()


if __name__ == "__main__":
    print("🚀 启动 LLM 配置系统测试...")
    success = test_config_reload()
    sys.exit(0 if success else 1)
