#!/bin/bash
# build.sh - 本地构建脚本 (Linux/Mac)
# 使用方式: bash build.sh 或 ./build.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数
CLEAN=${1:-"--clean"}
OUTPUT_DIR="dist"
APP_NAME="Commodity-Lab.exe"

echo -e "${BLUE}🔨 Commodity Lab 构建脚本${NC}"
echo "========================================"
echo ""

# 检查Python
echo -e "${YELLOW}🐍 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到Python！请确保Python 3已安装${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
echo ""

# 检查虚拟环境
echo -e "${YELLOW}📦 检查虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境不存在，正在创建...${NC}"
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
echo ""

# 安装依赖
echo -e "${YELLOW}📚 安装依赖...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
pip install pyinstaller > /dev/null 2>&1
echo -e "${GREEN}✅ 依赖安装完成${NC}"
echo ""

# 清理旧构建
if [[ "$CLEAN" == "--clean" ]]; then
    echo -e "${YELLOW}🧹 清理旧的构建文件...${NC}"
    rm -rf build 2>/dev/null || true
    rm -rf "$OUTPUT_DIR" 2>/dev/null || true
    rm -f *.spec 2>/dev/null || true
    echo -e "${GREEN}✅ 清理完成${NC}"
    echo ""
fi

# 构建参数
BUILD_ARGS=(
    "--onefile"
    "--windowed"
    "--name" "$APP_NAME"
    "--distpath" "$OUTPUT_DIR"
    "--workpath" "build"
    "--specpath" "."
    "-y"
)

# 添加数据文件
BUILD_ARGS+=(
    "--add-data" "app:app"
    "--add-data" "core:core"
    "--add-data" "data:data"
)

# 添加隐藏导入
HIDDEN_IMPORTS=(
    "streamlit"
    "streamlit.web"
    "duckdb"
    "pandas"
    "plotly"
    "yfinance"
)

for module in "${HIDDEN_IMPORTS[@]}"; do
    BUILD_ARGS+=("--hidden-import=$module")
done

# 设置图标
if [ -f "app/assets/icon.ico" ]; then
    BUILD_ARGS+=("--icon" "app/assets/icon.ico")
fi

# 执行构建
echo -e "${BLUE}🏗️ 开始构建...${NC}"
python3 -m PyInstaller "${BUILD_ARGS[@]}" app/desktop_launcher.py

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo -e "${GREEN}✅ 构建成功！${NC}"
    echo "========================================"
    echo ""
    
    # 列出输出文件
    EXE_PATH="$OUTPUT_DIR/$APP_NAME"
    if [ -f "$EXE_PATH" ]; then
        FILE_SIZE=$(du -h "$EXE_PATH" | cut -f1)
        echo -e "${BLUE}📦 可执行文件:${NC}"
        echo -e "   路径: $EXE_PATH"
        echo -e "   大小: $FILE_SIZE"
        echo ""
        echo -e "${BLUE}🚀 运行应用:${NC}"
        echo -e "   ./$EXE_PATH"
        echo ""
    fi
    
    # 显示文件列表
    echo -e "${BLUE}📂 输出目录内容:${NC}"
    find "$OUTPUT_DIR" -type f -exec ls -lh {} \; | awk '{print "   " $9 " (" $5 ")"}'
    echo ""
    echo -e "${GREEN}构建完成！${NC}"
else
    echo -e "${RED}❌ 构建失败！请检查错误信息${NC}"
    exit 1
fi
