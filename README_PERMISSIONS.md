# VoiceTyper 权限问题解决指南

## 问题描述

如果您遇到以下问题：
- **打包后的dmg应用启动时没有弹出麦克风权限申请窗口**
- 在Cursor中运行VoiceTyper正常，但在命令行中运行没有权限
- 录音时没有音频电平显示
- 转写结果总是为空
- 系统没有弹出权限申请对话框

这通常是macOS对不同应用的权限管理造成的。

## 快速解决方案

### 针对打包后的dmg应用（v0.3.15+修复）

**v0.3.15版本已修复打包应用权限问题**，现在打包后的应用会：
- 正确识别自己的bundle ID (`com.bongcaca.voicetyper`)
- 在首次运行时自动触发系统权限对话框
- 使用更清晰的权限申请描述

如果仍然没有弹出权限对话框，请：

1. **手动设置权限**：
   - 打开 **系统偏好设置** > **安全性与隐私** > **隐私**
   - 选择 **麦克风**
   - 勾选 **VoiceTyper** 应用

2. **重置应用权限**：
   ```bash
   tccutil reset Microphone com.bongcaca.voicetyper
   ```

### 针对开发环境

#### 方法1：使用权限修复工具（推荐）

运行我们提供的权限修复工具：

```bash
python fix_permissions.py
```

该工具会：
- 自动检测您的系统环境
- 分析当前权限状态
- 提供多种解决方案选择
- 指导您完成权限设置

#### 方法2：手动重置权限

如果您熟悉命令行操作，可以直接重置麦克风权限：

```bash
tccutil reset Microphone
```

然后重新运行程序：

```bash
./run.sh
```

系统会重新询问麦克风权限，请选择"允许"。

#### 方法3：手动设置权限

1. 打开 **系统偏好设置**
2. 选择 **安全性与隐私**
3. 点击 **隐私** 标签
4. 在左侧列表中选择 **麦克风**
5. 点击左下角的🔒并输入密码
6. 在右侧列表中勾选：
   - **Terminal** (如果通过终端运行)
   - **Python** (如果显示)
   - 或者您当前使用的终端应用
7. 关闭系统偏好设置
8. 重新运行VoiceTyper

## 技术说明

### v0.3.15版本权限修复

**修复的核心问题**：
- Bundle ID识别：正确检测打包应用环境 (`.app/Contents/MacOS/`)
- TCC数据库查询：增加对VoiceTyper应用bundle ID的支持
- 权限申请策略：区分打包应用和开发环境的不同处理方式

**修复内容**：
1. **增强的Bundle ID检测**：
   ```python
   # 检测打包应用环境
   if '.app/Contents/MacOS/' in python_path:
       return 'com.bongcaca.voicetyper'
   ```

2. **完善的TCC查询**：
   ```python
   # 支持多种应用标识符查询
   query_conditions = [
       "client='com.bongcaca.voicetyper'",
       "client LIKE '%voicetyper%'",
       # ... 其他条件
   ]
   ```

3. **Info.plist权限配置**：
   ```xml
   <key>NSMicrophoneUsageDescription</key>
   <string>VoiceTyper需要访问您的麦克风来进行语音识别和转写</string>
   ```

### 为什么会有权限问题？

macOS的TCC（透明度、同意和控制）系统对不同的应用有不同的权限管理：

1. **打包应用**：有独立的bundle ID和权限上下文
2. **命令行运行**：作为Terminal的子进程，需要Terminal的权限  
3. **Cursor运行**：作为GUI应用，有自己的bundle ID和权限上下文
4. **不同Python环境**：conda环境和系统Python可能有不同的权限

### 权限检查机制

VoiceTyper v0.3.15使用增强的权限检查系统：

1. **环境检测**：识别当前运行环境（打包应用/开发环境）
2. **TCC数据库检查**：查询系统权限记录
3. **实际访问测试**：尝试真实的麦克风访问
4. **多重验证**：确保权限真正有效

### 常见环境对应

| 运行环境 | Bundle ID | 权限要求 |
|---------|-----------|----------|
| 打包应用 | com.bongcaca.voicetyper | VoiceTyper需要麦克风权限 |
| Terminal | com.apple.Terminal | Terminal需要麦克风权限 |
| iTerm2 | com.googlecode.iterm2 | iTerm2需要麦克风权限 |
| VS Code Terminal | com.microsoft.VSCode | VS Code需要麦克风权限 |
| Cursor | com.todesktop.230313mzl4w4u92 | Cursor需要麦克风权限 |

## 故障排除

### 如果打包应用仍然没有权限对话框

1. **检查应用签名**：确保应用没有被系统阻止
2. **重置所有权限**：
   ```bash
   tccutil reset All com.bongcaca.voicetyper
   ```
3. **清除应用缓存**：删除应用并重新安装
4. **检查Gatekeeper设置**：系统偏好设置 > 安全性与隐私 > 通用

### 如果权限修复工具无法解决问题

1. **检查系统版本**：确保使用macOS 10.14+
2. **重启应用**：完全退出Terminal/iTerm2并重新打开
3. **清除应用权限**：
   ```bash
   tccutil reset All
   ```
4. **检查SIP状态**：某些操作可能需要禁用SIP（不推荐）

### 如果仍然无法解决

请在GitHub Issue中提供以下信息：
- macOS版本
- 使用的应用类型（打包应用/开发环境）
- VoiceTyper版本
- 权限修复工具的输出
- 完整的错误日志

## 更新日志

- **v0.3.15**: 修复打包应用权限检查问题，增强bundle ID识别
- **v0.3.14**: 新增权限修复工具和增强权限检查
- **v0.3.13**: 修复命令行权限检查问题
- **v0.3.11**: 添加基础权限申请功能

---

如果本指南帮助您解决了问题，请考虑给项目一个⭐！ 