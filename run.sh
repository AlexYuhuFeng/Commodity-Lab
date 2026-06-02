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

# Start the Tauri-friendly Python backend for local development
echo "🚀 Starting Commodity Lab backend (FastAPI)..."
echo ""
echo "Developer notes:"
echo " - Start the Python backend: python tauri/backend/main.py"
echo " - Start the frontend dev server: cd tauri/tauri-frontend && npm install && npm run dev"
echo " - Or run the full Tauri dev workflow from the tauri/ directory: npm run tauri:dev"
echo ""
python tauri/backend/main.py
