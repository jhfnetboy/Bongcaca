# VoiceTyper 构建指南

## 多架构构建说明

VoiceTyper 支持在不同架构的 Mac 上构建对应的 DMG 包，以确保最佳的兼容性和性能。

### 支持的架构

- **Apple Silicon (M1/M2/M3)**: arm64 架构
- **Intel Mac**: x86_64 架构

### 为什么需要分架构构建？

1. **最佳性能**: 原生架构的应用程序运行效率最高
2. **兼容性**: 避免通过 Rosetta 2 转换运行可能出现的问题
3. **文件大小**: 避免构建包含多架构的通用二进制文件（Universal Binary）导致的体积增大

## 构建准备

### 环境要求

1. **macOS 系统**: macOS 10.15 或更高版本
2. **Homebrew**: 用于安装依赖工具
3. **Python**: 3.11 版本
4. **Conda**: 用于环境管理

### 依赖安装

```bash
# 安装 Homebrew (如果未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 create-dmg 工具
brew install create-dmg

# 创建 conda 环境
conda create -n voice_typer python=3.11
conda activate voice_typer

# 安装 Python 依赖
pip install -r requirements.txt
```

## 快速构建

### 使用自动化脚本（推荐）

```bash
# 运行多架构构建脚本
./build_multi_arch.sh
```

这个脚本会：
- 自动检测当前架构
- 检查并安装必要依赖
- 构建对应架构的 DMG 包
- 显示构建结果和发布指导

### 手动构建

```bash
# 激活环境
conda activate voice_typer

# 运行构建脚本
python build_app.py --platform macos
```

## 构建输出

### 文件命名规则

构建完成后会生成如下格式的 DMG 文件：

```
VoiceTyper-[版本号]-[架构].dmg
```

例如：
- `VoiceTyper-0.23.43-arm64.dmg` (Apple Silicon 版本)
- `VoiceTyper-0.23.43-x86_64.dmg` (Intel 版本)

### 构建产物

- **应用包**: `dist/VoiceTyper.app`
- **DMG 镜像**: `VoiceTyper-[版本]-[架构].dmg`
- **构建日志**: 控制台输出

## 发布流程

### 1. 在两个架构的 Mac 上分别构建

**Apple Silicon Mac:**
```bash
./build_multi_arch.sh
# 生成: VoiceTyper-0.23.43-arm64.dmg
```

**Intel Mac:**
```bash
./build_multi_arch.sh
# 生成: VoiceTyper-0.23.43-x86_64.dmg
```

### 2. 上传到 GitHub Releases

1. 创建新的 Release
2. 上传两个 DMG 文件
3. 在 Release 说明中明确标注架构要求

### 3. Release 说明模板

```markdown
## VoiceTyper v0.23.43

### 下载说明

请根据您的 Mac 架构选择对应的版本：

- **Apple Silicon Mac (M1/M2/M3)**: 下载 `VoiceTyper-0.23.43-arm64.dmg`
- **Intel Mac**: 下载 `VoiceTyper-0.23.43-x86_64.dmg`

### 如何检测您的架构？

在终端中运行：
```bash
uname -m
```

- 输出 `arm64`: 使用 Apple Silicon 版本
- 输出 `x86_64`: 使用 Intel 版本

或者运行我们提供的检测脚本：
```bash
curl -s https://raw.githubusercontent.com/[用户名]/VoiceTyper/main/check_architecture.sh | bash
```

### 更新内容

- 新功能 1
- 新功能 2
- Bug 修复
```

## 用户架构检测

为了帮助用户选择正确的版本，我们提供了架构检测脚本：

### 本地检测脚本

```bash
./check_architecture.sh
```

### 在线检测脚本

用户可以直接运行：

```bash
curl -s https://raw.githubusercontent.com/[用户名]/VoiceTyper/main/check_architecture.sh | bash
```

## 故障排除

### 常见问题

1. **构建失败 - 依赖缺失**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt
   ```

2. **DMG 创建失败**
   ```bash
   # 确保 create-dmg 已安装
   brew install create-dmg
   ```

3. **权限问题**
   ```bash
   # 给脚本添加执行权限
   chmod +x build_multi_arch.sh
   chmod +x check_architecture.sh
   ```

4. **Conda 环境问题**
   ```bash
   # 重新创建环境
   conda env remove -n voice_typer
   conda create -n voice_typer python=3.11
   conda activate voice_typer
   pip install -r requirements.txt
   ```

### 构建日志分析

如果构建失败，请检查：

1. Python 依赖是否完整安装
2. macOS 权限设置是否正确
3. 磁盘空间是否充足
4. 网络连接是否正常（下载依赖时）

## 开发者注意事项

### 版本号管理

修改 `build_app.py` 中的版本号：

```python
VERSION = "0.23.43"  # 更新这里
```

### 构建优化

- 使用 `--skip-deps-check` 跳过依赖检查（仅在确认环境正确时使用）
- 构建前清理旧文件以避免冲突

### 代码签名

目前使用 adhoc 签名，如需分发建议使用开发者证书：

```bash
# 在 build_app.py 中修改签名设置
--sign "Developer ID Application: Your Name"
``` 