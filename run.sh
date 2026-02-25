#!/bin/bash
# run.sh - 启动 Commodity Lab 应用

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

# Check if venv exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please create it first: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source "$VENV_PATH/bin/activate"

# 检查依赖
echo "✓ 虚拟环境已激活"

# 启动Streamlit应用
echo "🚀 启动 Commodity Lab..."
echo ""
echo "应用已启动，请在浏览器打开:"
echo "  📍 Local: http://localhost:8501"
echo ""
echo "按 Ctrl+C 停止应用"
echo ""

streamlit run "$PROJECT_ROOT/app/main.py"
