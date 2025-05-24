#!/bin/bash

# Voice Typer 架构检测脚本
# 帮助用户检测Mac架构并选择正确的DMG版本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}🔍 VoiceTyper 架构检测工具${NC}"
echo -e "${BLUE}=================================${NC}"

# 检测架构
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    ARCH_NAME="Apple Silicon"
    DOWNLOAD_VERSION="arm64"
    EMOJI="🍎"
elif [[ "$ARCH" == "x86_64" ]]; then
    ARCH_NAME="Intel"
    DOWNLOAD_VERSION="x86_64"
    EMOJI="💻"
else
    echo -e "${YELLOW}⚠️  未知架构: $ARCH${NC}"
    echo "请联系开发者获取支持"
    exit 1
fi

echo -e "${GREEN}$EMOJI 您的Mac架构: $ARCH_NAME ($ARCH)${NC}"
echo ""
echo -e "${BLUE}📥 请下载以下版本:${NC}"
echo -e "${GREEN}VoiceTyper-[版本号]-${DOWNLOAD_VERSION}.dmg${NC}"
echo ""
echo -e "${BLUE}💡 下载说明:${NC}"
echo "1. 前往 GitHub Releases 页面"
echo "2. 找到最新版本"
echo "3. 下载文件名包含 '${DOWNLOAD_VERSION}' 的 DMG 文件"
echo ""
echo -e "${BLUE}🔗 GitHub 地址:${NC}"
echo "https://github.com/[用户名]/VoiceTyper/releases"
echo ""

# 显示系统信息
echo -e "${BLUE}📊 系统信息:${NC}"
echo "操作系统: $(sw_vers -productName) $(sw_vers -productVersion)"
echo "架构: $ARCH"
echo "芯片: $ARCH_NAME"
echo ""

echo -e "${BLUE}=================================${NC}" 