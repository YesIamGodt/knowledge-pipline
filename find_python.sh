#!/bin/bash
# 通用的 Python 查找脚本

# 尝试 1: 使用 which 命令
PYTHON_CMD=$(which python3 2>/dev/null || which python 2>/dev/null)

# 尝试 2: 常见的 Python 路径
if [ -z "$PYTHON_CMD" ]; then
    # 常见的 Windows 安装路径
    possible_paths=(
        "/c/Users/$USER/AppData/Local/Programs/Python/Python312/python.exe"
        "/c/Users/$USER/AppData/Local/Programs/Python/Python311/python.exe"
        "/c/Users/$USER/AppData/Local/Programs/Python/Python310/python.exe"
        "/c/Program Files/Python312/python.exe"
        "/c/Program Files/Python311/python.exe"
        "/c/Program Files/Python310/python.exe"
        "/c/Program Files (x86)/Python312/python.exe"
        "/c/Program Files (x86)/Python311/python.exe"
        "/c/Program Files (x86)/Python310/python.exe"
        "/c/Python312/python.exe"
        "/c/Python311/python.exe"
        "/c/Python310/python.exe"
        "/usr/bin/python3"
        "/usr/bin/python"
    )

    for path in "${possible_paths[@]}"; do
        if [ -f "$path" ] && [ -x "$path" ]; then
            PYTHON_CMD="$path"
            break
        fi
    done
fi

# 尝试 3: 通过 cmd 查找
if [ -z "$PYTHON_CMD" ]; then
    if [ -x "/c/Windows/System32/cmd.exe" ]; then
        cmd_output=$(cmd //c where python 2>&1 || cmd //c where python3 2>&1)
        if [ $? -eq 0 ]; then
            # 转换 Windows 路径到 WSL 格式
            PYTHON_CMD=$(echo "$cmd_output" | head -1 | sed 's/\\/\//g' | sed 's/^C:/\/c/')
        fi
    fi
fi

# 输出找到的命令
if [ -n "$PYTHON_CMD" ]; then
    echo "$PYTHON_CMD"
else
    echo "python"
    exit 1
fi
