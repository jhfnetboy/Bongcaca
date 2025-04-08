# 更新日志

## 2024-03-21
- 添加了录音控制按钮（绿色开始/红色停止）
- 添加了空格键控制录音功能
- 添加了识别结果显示区域
- 移除了自动下载模型功能，改为提示用户手动下载
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