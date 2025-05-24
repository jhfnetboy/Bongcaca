# VoiceTyper - 智能语音转写工具

一款基于 Whisper 的实时语音转写应用，支持多语言识别和翻译。

## 🎯 主要功能

- **实时语音转写**: 支持批量和实时两种转写模式
- **多语言支持**: 支持中文、英文、日文等多种语言识别
- **语言翻译**: 可将语音直接翻译成目标语言
- **全局快捷键**: 支持 fn 双击快捷键在任意应用中录音
- **模型选择**: 支持多种 Whisper 模型，可根据精度和速度需求选择
- **设备选择**: 支持选择不同的音频输入设备

## 📥 下载安装

### 🔍 检测您的Mac架构

在下载前，请先确定您的Mac架构：

**方法1：运行检测脚本**
```bash
curl -s https://raw.githubusercontent.com/nicolasshimokuryuu/VoiceTyper/main/check_architecture.sh | bash
```

**方法2：手动检测**
```bash
uname -m
```
- 输出 `arm64`: Apple Silicon Mac (M1/M2/M3/M4)
- 输出 `x86_64`: Intel Mac

### 📦 下载对应版本

前往 [Releases 页面](https://github.com/nicolasshimokuryuu/VoiceTyper/releases) 下载：

- **Apple Silicon Mac**: `VoiceTyper-[版本号]-arm64.dmg`
- **Intel Mac**: `VoiceTyper-[版本号]-x86_64.dmg`

### 🛠 安装步骤

1. 下载对应架构的 DMG 文件
2. 双击打开 DMG 文件
3. 将 VoiceTyper.app 拖拽到 Applications 文件夹
4. 首次运行时，系统会要求授予麦克风和辅助功能权限

## 🚀 快速开始

### 权限设置

首次运行需要授予以下权限：

1. **麦克风权限**: 用于录音识别
2. **辅助功能权限**: 用于自动输入转写文本
3. **文件访问权限**: 用于保存录音文件

### 基本使用

1. 启动 VoiceTyper
2. 选择合适的模型（推荐 small 或 medium）
3. 选择源语言和目标语言（如需翻译）
4. 点击录音按钮或使用 fn 双击快捷键开始录音
5. 转写结果会自动复制到剪贴板，可使用 Command+V 粘贴

## 🔧 开发构建

### 环境准备

```bash
# 创建 conda 环境
conda create -n voice_typer python=3.11
conda activate voice_typer

# 安装依赖
pip install -r requirements.txt

# 安装构建工具
brew install create-dmg
```

### 运行开发版本

```bash
# 激活环境
conda activate voice_typer

# 运行应用
python main.py
```

### 构建 DMG 包

#### 快速构建（推荐）

```bash
# 使用自动化脚本
./build_multi_arch.sh
```

#### 手动构建

```bash
# 激活环境
conda activate voice_typer

# 构建应用
python build_app.py --platform macos
```

构建完成后会生成：
- `VoiceTyper-[版本号]-[架构].dmg`

### 多架构发布流程

1. **在 Apple Silicon Mac 上构建**：
   ```bash
   ./build_multi_arch.sh
   # 生成: VoiceTyper-0.3.18-arm64.dmg
   ```

2. **在 Intel Mac 上构建**：
   ```bash
   ./build_multi_arch.sh
   # 生成: VoiceTyper-0.3.18-x86_64.dmg
   ```

3. **上传到 GitHub Releases**：
   - 创建新的 Release
   - 上传两个 DMG 文件
   - 在说明中标注架构要求

详细构建指南请参考 [BUILD_GUIDE.md](docs/BUILD_GUIDE.md)

## 📖 文档

- [构建指南](docs/BUILD_GUIDE.md) - 详细的构建和发布流程
- [更新日志](docs/CHANGES.md) - 版本更新记录
- [部署指南](docs/DEPLOY.md) - 环境设置和运行指南

## 🔍 故障排除

### 常见问题

1. **权限问题**: 确保授予了麦克风和辅助功能权限
2. **模型下载缓慢**: 可选择较小的模型如 small 或 base
3. **转写精度不佳**: 尝试使用 medium 或 large-v3 模型
4. **快捷键不工作**: 检查辅助功能权限是否正确授予

### 获取帮助

- [GitHub Issues](https://github.com/nicolasshimokuryuu/VoiceTyper/issues)
- [讨论区](https://github.com/nicolasshimokuryuu/VoiceTyper/discussions)

## 📄 许可证

MIT License

## 🙏 致谢

- [Faster Whisper](https://github.com/SYSTRAN/faster-whisper) - 高效的 Whisper 实现
- [OpenAI Whisper](https://github.com/openai/whisper) - 强大的语音识别模型
- [PySide6](https://wiki.qt.io/Qt_for_Python) - 跨平台 GUI 框架

