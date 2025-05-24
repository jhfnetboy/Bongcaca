#!/bin/bash

# Voice Typer 多架构构建脚本
# 用于在 Apple Silicon 和 Intel Mac 上分别构建对应的 DMG 包

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检测当前架构
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    ARCH_NAME="Apple Silicon"
    ARCH_SHORT="arm64"
elif [[ "$ARCH" == "x86_64" ]]; then
    ARCH_NAME="Intel"
    ARCH_SHORT="x86_64"
else
    echo -e "${RED}❌ 不支持的架构: $ARCH${NC}"
    exit 1
fi

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}🔨 Voice Typer 多架构构建工具${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}当前架构: $ARCH_NAME ($ARCH_SHORT)${NC}"
echo ""

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python 未找到，请确保已安装 Python${NC}"
    exit 1
fi

# 检查依赖
echo -e "${YELLOW}📋 检查构建依赖...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew 未安装，请先安装 Homebrew${NC}"
    exit 1
fi

if ! command -v create-dmg &> /dev/null; then
    echo -e "${YELLOW}⚠️  create-dmg 未安装，正在安装...${NC}"
    brew install create-dmg
fi

# 检查 voice_typer 环境
if ! conda env list | grep -q voice_typer; then
    echo -e "${RED}❌ voice_typer conda环境未找到，请先创建环境${NC}"
    echo "运行: conda create -n voice_typer python=3.11"
    exit 1
fi

# 激活环境
echo -e "${YELLOW}🔄 激活 voice_typer 环境...${NC}"
eval "$(conda shell.bash hook)"
conda activate voice_typer

# 检查关键依赖
echo -e "${YELLOW}🔍 检查Python依赖...${NC}"
python -c "import PyInstaller" 2>/dev/null || {
    echo -e "${RED}❌ PyInstaller 未安装，正在安装...${NC}"
    pip install pyinstaller
}

python -c "from PySide6.QtWidgets import QApplication" 2>/dev/null || {
    echo -e "${RED}❌ PySide6 未安装，请安装依赖${NC}"
    echo "运行: pip install -r requirements.txt"
    exit 1
}

# 清理之前的构建
echo -e "${YELLOW}🧹 清理之前的构建文件...${NC}"
rm -rf dist/ build/ *.dmg 2>/dev/null || true

# 开始构建
echo -e "${GREEN}🚀 开始构建 $ARCH_NAME 版本...${NC}"
python build_app.py --platform macos

# 检查构建结果
if [[ ! -d "dist/VoiceTyper.app" ]]; then
    echo -e "${RED}❌ 应用构建失败${NC}"
    exit 1
fi

# 查找生成的DMG文件
DMG_FILE=$(ls VoiceTyper-*-${ARCH_SHORT}.dmg 2>/dev/null | head -n 1)
if [[ -z "$DMG_FILE" ]]; then
    echo -e "${RED}❌ DMG文件未找到${NC}"
    exit 1
fi

# 获取文件大小
DMG_SIZE=$(du -h "$DMG_FILE" | cut -f1)

echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}✅ 构建成功！${NC}"
echo -e "${GREEN}架构: $ARCH_NAME ($ARCH_SHORT)${NC}"
echo -e "${GREEN}文件: $DMG_FILE${NC}"
echo -e "${GREEN}大小: $DMG_SIZE${NC}"
echo -e "${GREEN}=================================${NC}"

# 提供下一步指导
echo ""
echo -e "${BLUE}📦 发布指导:${NC}"
echo "1. 将 $DMG_FILE 上传到 GitHub Releases"
echo "2. 在另一个架构的Mac上运行此脚本构建对应版本"
echo "3. 用户可根据自己的Mac架构选择相应的DMG下载"
echo ""
echo -e "${BLUE}🔍 检测用户架构的方法:${NC}"
echo "用户可以运行: uname -m"
echo "- arm64: 下载 Apple Silicon 版本"
echo "- x86_64: 下载 Intel 版本"
echo "" 