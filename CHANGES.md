# 更新日志

## 2024-03-21
- 改进了模型下载逻辑，使用 huggingface-cli 命令行工具
- 添加了模型缓存目录检查
- 优化了模型路径处理
- 添加了录音控制按钮（绿色开始/红色停止）
- 添加了空格键控制录音功能
- 添加了识别结果显示区域
- 改进了模型路径处理，优先使用已下载的模型
- 添加了默认模型路径检查
- 优化了模型加载逻辑
- 添加了主窗口界面，支持图形化操作
- 改进了模型下载路径处理，支持从缓存目录加载模型
- 添加了模型检查和下载状态显示
- 添加了录音和识别状态显示
- 改进了程序退出处理，支持窗口关闭和 Ctrl+C 退出
- 更新了模型下载方式，使用 huggingface-cli 进行下载
- 改进了程序退出处理，确保 Ctrl+C 可以正常退出
- 优化了模型下载错误处理
- 更新了模型下载路径（从 guillaumekln 更改为 Systran）
- 添加了程序退出处理，支持 Ctrl+C 正常退出
- 添加了模型下载错误处理
- 优化了模型加载的错误提示
- 更新了安装步骤，添加了环境激活说明
- Upgraded faster-whisper to version 1.1.1
- Added word-level timestamp support
- Improved model download and management features
- Added logging configuration
- Optimized model loading and recognition processes
- Added system resource detection and model recommendation features
- Fixed model download path issues
- Added model version compatibility checks
- Renamed platform directory to platform_specific to avoid conflicts with standard library
- Configured conda environment to resolve dependency installation issues

## 2024-03-22
- Added model detection feature to automatically detect and use downloaded models
- Added audio visualization with real-time waveform display
- Improved UI with better button states and visual feedback
- Added automatic input device selection
- Added text input functionality to current focus position
- Added pyautogui dependency for text input
- Removed custom window controls in favor of system window controls
- Added real-time audio level visualization
- Improved error handling and user feedback
- Added model detection logging

## 2024-04-08
- 修复了录音无法启动的严重问题:
  - 重构了录音控制流程
  - 分离UI状态和录音逻辑
  - 使用信号机制代替直接函数调用
  - 确保状态变更顺序正确
- 改进了信号处理机制:
  - 添加了录音控制专用信号
  - 优化了按钮和键盘事件处理
  - 增强了状态同步逻辑
- 版本号更新至 0.23.37

## 初始化安装步骤

1. 安装 Homebrew（如果没有）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. 安装 Miniconda（如果没有）
```bash
brew install --cask miniconda
```

3. 初始化 conda
```bash
conda init zsh  # 如果使用 bash，则运行 conda init bash
```

4. 关闭并重新打开终端

5. 创建并激活 conda 环境
```bash
conda create -n voice_typer python=3.11
conda activate voice_typer
```

6. 安装依赖
```bash
conda install -c conda-forge ctranslate2
conda install -c conda-forge pyside6
pip install -U huggingface_hub
pip install -r requirements.txt
```

7. 运行程序
```bash
conda activate voice_typer  # 确保环境已激活
python main.py
```

注意：如果遇到 PyQt6 相关错误，请使用 conda 安装 pyside6：
```bash
conda install -c conda-forge pyside6
```

注意：
1. 如果遇到 Qt 相关错误，请完全卸载并重新安装：
   ```bash
   pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip PySide6
   pip install --no-cache-dir PySide6
   ```

2. 如果仍然遇到 Qt 平台插件错误，请尝试：
   ```bash
   conda install -c conda-forge pyside6
   ``` 


     