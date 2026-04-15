"""
PlannerAgent Usage Examples

This file demonstrates various ways to use PlannerAgent in different scenarios.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ppt.agents import PlannerAgent
from backend.ppt.models import OutlineItem
from core.llm_config import LLMConfig


# ═══════════════════════════════════════════════════════════════
# Example 1: Basic Usage
# ═══════════════════════════════════════════════════════════════

def example_1_basic():
    """Basic usage: generate outline from knowledge text."""
    print("=" * 70)
    print("Example 1: Basic Usage")
    print("=" * 70)

    # Initialize
    planner = PlannerAgent()

    # Prepare inputs
    knowledge = """
# 机器学习基础

机器学习是人工智能的一个分支，它使计算机能够从数据中学习。

主要类型：
1. 监督学习：有标签数据
2. 无监督学习：无标签数据
3. 强化学习：通过奖励学习

常见算法：
- 线性回归
- 决策树
- 神经网络
- 支持向量机
"""

    instruction = "制作一个机器学习入门的演示文稿"

    # Generate outline
    outline = planner.plan(knowledge, instruction)

    # Display results
    print(f"\nGenerated {len(outline)} slides:\n")
    for item in outline:
        print(f"  [{item.idx:2d}] {item.type:12s} - {item.topic}")

    print("\n" + "=" * 70 + "\n")
    return outline


# ═══════════════════════════════════════════════════════════════
# Example 2: Empty Knowledge (LLM's Own Knowledge)
# ═══════════════════════════════════════════════════════════════

def example_2_no_knowledge():
    """Generate outline without knowledge base (relies on LLM's knowledge)."""
    print("=" * 70)
    print("Example 2: Empty Knowledge (LLM's Own Knowledge)")
    print("=" * 70)

    planner = PlannerAgent()

    # Empty knowledge - LLM will use its internal knowledge
    knowledge = ""
    instruction = "做一个关于 Python 编程语言历史的演示文稿"

    outline = planner.plan(knowledge, instruction)

    print(f"\nGenerated {len(outline)} slides:\n")
    for item in outline:
        print(f"  [{item.idx:2d}] {item.type:12s} - {item.topic}")

    print("\n" + "=" * 70 + "\n")
    return outline


# ═══════════════════════════════════════════════════════════════
# Example 3: Technical Deep Dive
# ═══════════════════════════════════════════════════════════════

def example_3_technical():
    """Generate outline for technical content with specific instruction."""
    print("=" * 70)
    print("Example 3: Technical Deep Dive")
    print("=" * 70)

    planner = PlannerAgent()

    knowledge = """
# Docker 容器技术

Docker 是一个开源的容器化平台。

核心概念：
- 镜像 (Image): 只读模板
- 容器 (Container): 运行实例
- 仓库 (Registry): 镜像存储

技术架构：
- Namespaces: 资源隔离
- Cgroups: 资源限制
- UnionFS: 分层存储

优势：
- 快速部署
- 环境一致性
- 资源效率高
- 微服务架构
"""

    # More specific instruction
    instruction = "面向 DevOps 工程师，重点讲 Docker 的技术架构和最佳实践"

    outline = planner.plan(knowledge, instruction)

    print(f"\nGenerated {len(outline)} slides:\n")
    for item in outline:
        print(f"  [{item.idx:2d}] {item.type:12s} - {item.topic}")

    print("\n" + "=" * 70 + "\n")
    return outline


# ═══════════════════════════════════════════════════════════════
# Example 4: Export to JSON
# ═══════════════════════════════════════════════════════════════

def example_4_export_json():
    """Export outline to JSON format."""
    print("=" * 70)
    print("Example 4: Export to JSON")
    print("=" * 70)

    planner = PlannerAgent()

    knowledge = "# React 组件化开发\nReact 是一个用于构建用户界面的 JavaScript 库。\n\n核心特性：\n- 组件化\n- 虚拟DOM\n- 单向数据流"

    instruction = "React 组件化开发教程"

    outline = planner.plan(knowledge, instruction)

    # Export to JSON
    import json
    json_output = [item.to_dict() for item in outline]

    print("\nJSON Output:\n")
    print(json.dumps(json_output, ensure_ascii=False, indent=2))

    print("\n" + "=" * 70 + "\n")
    return json_output


# ═══════════════════════════════════════════════════════════════
# Example 5: Error Handling
# ═══════════════════════════════════════════════════════════════

def example_5_error_handling():
    """Demonstrate proper error handling."""
    print("=" * 70)
    print("Example 5: Error Handling")
    print("=" * 70)

    planner = PlannerAgent()

    knowledge = "简短的知识"
    instruction = "演示文稿"

    try:
        outline = planner.plan(knowledge, instruction)
        print(f"✓ Success: Generated {len(outline)} slides")

    except RuntimeError as e:
        if "LLM 未配置" in str(e):
            print("❌ Error: LLM not configured")
            print("   Solution: Run /pipeline-config")
        else:
            print(f"❌ Error: {e}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════
# Example 6: Validation
# ═══════════════════════════════════════════════════════════════

def example_6_validation():
    """Validate generated outline."""
    print("=" * 70)
    print("Example 6: Outline Validation")
    print("=" * 70)

    planner = PlannerAgent()

    knowledge = "# 软件测试\n软件测试是保证软件质量的重要环节。\n\n测试类型：\n- 单元测试\n- 集成测试\n- 系统测试\n- 验收测试"

    instruction = "软件测试方法介绍"

    outline = planner.plan(knowledge, instruction)

    # Validate
    issues = validate_outline(outline)

    print(f"\nGenerated {len(outline)} slides\n")
    for item in outline:
        print(f"  [{item.idx:2d}] {item.type:12s} - {item.topic}")

    print(f"\nValidation result:")
    if issues:
        print("  ⚠️  Issues found:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✓ No issues found!")

    print("\n" + "=" * 70 + "\n")


# ═══════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════

def validate_outline(outline: list[OutlineItem]) -> list[str]:
    """Validate outline structure."""
    issues = []

    if len(outline) < 5:
        issues.append(f"Too few slides: {len(outline)} (minimum 5)")
    if len(outline) > 15:
        issues.append(f"Too many slides: {len(outline)} (maximum 15)")

    if outline[0].type != "title":
        issues.append(f"First slide must be 'title', got '{outline[0].type}'")
    if outline[-1].type != "title":
        issues.append(f"Last slide must be 'title', got '{outline[-1].type}'")

    valid_types = {"title", "bullets", "comparison", "metric", "quote", "timeline", "flowchart"}
    for i, item in enumerate(outline):
        if item.type not in valid_types:
            issues.append(f"Slide {i} has invalid type '{item.type}'")
        if not item.topic.strip():
            issues.append(f"Slide {i} has empty topic")

    return issues


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    """Run all examples."""
    print("\n" + "🚀" * 35)
    print("PlannerAgent Usage Examples")
    print("🚀" * 35 + "\n")

    # Check configuration first
    config = LLMConfig()
    if not config.is_configured():
        print("⚠️  LLM not configured!")
        print("   Please run: /pipeline-config")
        print("\nSkipping examples that require LLM calls.\n")
        return

    try:
        # Run examples
        example_1_basic()
        example_2_no_knowledge()
        example_3_technical()
        example_4_export_json()
        example_5_error_handling()
        example_6_validation()

        print("✅ All examples completed successfully!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
