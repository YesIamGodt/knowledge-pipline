#!/usr/bin/env python3
"""
多格式文件处理演示脚本

演示如何从不同文件格式提取内容并摄入到 wiki 中：
- PDF、Word、Excel、PowerPoint
- 图片（OCR）
- HTML 网页
- 纯文本文件
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.processors import FileProcessor


def demo_file_processing(file_path: str):
    """演示文件处理"""
    print(f"\\n{'='*60}")
    print(f"处理文件: {file_path}")
    print(f"{'='*60}")

    # 创建文件处理器
    processor = FileProcessor()

    # 处理文件
    result = processor.process(file_path)

    # 显示结果
    print(f"\\n✅ 处理完成！")
    print(f"\\n📄 元数据:")
    for key, value in result.metadata.items():
        print(f"  - {key}: {value}")

    print(f"\\n📝 提取的文本预览 (前 500 字符):")
    preview = result.content[:500]
    if len(result.content) > 500:
        preview += "..."
    print(preview)

    if result.tables:
        print(f"\\n📊 提取的表格数量: {len(result.tables)}")
        for i, table in enumerate(result.tables[:2], 1):
            print(f"\\n表格 {i} 预览:")
            print(table[:300] + "..." if len(table) > 300 else table)

    if result.images:
        print(f"\\n🖼️  提取的图片数量: {len(result.images)}")

    if result.errors:
        print(f"\\n⚠️  警告/错误:")
        for error in result.errors:
            print(f"  - {error}")

    # 统计信息
    char_count = len(result.content)
    word_count = len(result.content.split())
    print(f"\\n📊 统计:")
    print(f"  - 字符数: {char_count}")
    print(f"  - 估计字数: {word_count}")

    return result


def main():
    """主函数"""
    print("="*60)
    print("LLM Wiki Agent - 多格式文件处理演示")
    print("="*60)

    # 支持的格式示例
    supported_formats = [
        ".pdf - PDF 文档",
        ".docx - Word 文档",
        ".xlsx - Excel 表格",
        ".jpg/.png/.webp - 图片（OCR）",
        ".pptx - PowerPoint 演示文稿",
        ".html - HTML 网页",
        ".md/.txt - 纯文本",
    ]

    print("\\n支持的文件格式:")
    for fmt in supported_formats:
        print(f"  {fmt}")

    print("\\n" + "="*60)
    print("使用方法:")
    print("="*60)
    print("""
1. 命令行使用:
   python demo_multi_format.py <file_path>

2. 在代码中使用:
   from backend.processors import FileProcessor

   processor = FileProcessor()
   result = processor.process("path/to/your/file.pdf")
   content = result.content

3. 在 wiki-ingest 工作流中使用:
   文件会被自动处理，提取的文本用于生成 wiki 页面
    """)

    # 如果提供了命令行参数，处理指定的文件
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if Path(file_path).exists():
            demo_file_processing(file_path)
        else:
            print(f"\\n❌ 错误: 文件不存在: {file_path}")
    else:
        print("\\n💡 提示: 运行 'python demo_multi_format.py <文件路径>' 来处理特定文件")


if __name__ == "__main__":
    main()
