# VoiceTyper

VoiceTyper是一个基于faster-whisper的语音转文字工具，支持实时录音转写和多语言翻译。
使用提示：

1. 首次运行时，macOS会要求授予麦克风和辅助功能权限，其他系统没测试过^_^，请谅解
2. 如果应用无法启动，请检查系统偏好设置 -> 安全性与隐私 -> 通用，允许运行该应用
3. 可以通过双击 .app 文件或从 Applications 文件夹启动应用

## 快速开始

```bash
# 激活环境并运行
conda activate voice_typer && python main.py
```

## 完整文档

所有详细文档请查看 [docs](docs/) 目录：

- [部署指南](docs/DEPLOY.md) - 环境设置和运行指南
- [更新日志](docs/CHANGES.md) - 版本更新记录
- [详细说明](docs/README.md) - 完整功能说明
- [发布记录](docs/RELEASE.md) - 版本发布历史

## 当前版本


v0.3.10 - 添加麦克风权限申请和性能优化 

