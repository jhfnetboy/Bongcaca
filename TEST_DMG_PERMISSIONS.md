# VoiceTyper DMG 权限测试指南

## 测试目标

验证打包后的VoiceTyper.dmg应用能够正确弹出"VoiceTyper would like to access the microphone"权限申请对话框，而不是显示"Terminal would like to access the microphone"。

## 修复内容 (v0.3.15)

### 1. 新增独立启动器 (`launcher.py`)
- 确保应用以独立进程身份运行
- 设置正确的进程标题和进程组
- 在GUI初始化前完成权限申请

### 2. 代码签名和权限声明
- 添加 `VoiceTyper.entitlements` 权限声明文件
- 使用adhoc代码签名，确保bundle ID正确识别
- 明确声明麦克风和辅助功能权限

### 3. 增强的Info.plist配置
```xml
<key>CFBundleIdentifier</key>
<string>com.bongcaca.voicetyper</string>
<key>NSMicrophoneUsageDescription</key>
<string>VoiceTyper需要访问您的麦克风来进行语音识别和转写</string>
```

### 4. 改进的权限检查逻辑
- 正确识别打包应用环境 (`.app/Contents/MacOS/`)
- 增强TCC数据库查询，支持VoiceTyper bundle ID
- 区分打包应用和开发环境的处理策略

## 测试步骤

### 准备工作

1. **重置权限状态**（确保干净的测试环境）：
   ```bash
   # 重置VoiceTyper权限
   tccutil reset Microphone com.bongcaca.voicetyper
   
   # 重置Terminal权限（如果需要）
   tccutil reset Microphone com.apple.Terminal
   ```

2. **构建新的应用**：
   ```bash
   # 清理旧构建
   rm -rf dist build VoiceTyper.dmg
   
   # 重新构建
   python build_app.py --platform macos
   ```

### 测试用例1：DMG安装和首次运行

1. **安装DMG**：
   - 双击 `VoiceTyper.dmg`
   - 将VoiceTyper拖拽到Applications文件夹

2. **首次运行**：
   - 从Applications文件夹启动VoiceTyper
   - **期望结果**：弹出权限对话框显示"VoiceTyper" would like to access the microphone
   - **不应出现**：显示"Terminal" would like to access the microphone

3. **权限申请后**：
   - 点击"Allow"授予权限
   - 应用应该正常启动并显示主界面

### 测试用例2：直接运行.app文件

1. **直接启动**：
   ```bash
   open dist/VoiceTyper.app
   ```

2. **验证权限对话框**：
   - 确认显示的是"VoiceTyper"而不是"Terminal"
   - 确认权限描述文本正确

### 测试用例3：权限验证

1. **检查权限状态**：
   ```bash
   # 运行权限测试脚本
   python test_packaged_permissions.py
   ```

2. **验证TCC数据库**：
   ```bash
   # 查看权限记录
   sqlite3 ~/Library/Application\ Support/com.apple.TCC/TCC.db \
   "SELECT client, allowed FROM access WHERE service='kTCCServiceMicrophone';"
   ```

3. **期望结果**：
   - 应该看到 `com.bongcaca.voicetyper` 的权限记录
   - 权限状态为允许 (allowed=1)

## 故障排除

### 如果仍然显示"Terminal"权限申请

1. **检查代码签名**：
   ```bash
   codesign -dv dist/VoiceTyper.app
   ```
   应该显示：`Identifier=com.bongcaca.voicetyper`

2. **验证Info.plist**：
   ```bash
   cat dist/VoiceTyper.app/Contents/Info.plist | grep -A1 CFBundleIdentifier
   ```

3. **清除权限缓存**：
   ```bash
   # 重启权限服务
   sudo killall tccd
   
   # 重新启动应用
   ```

### 如果应用无法启动

1. **检查Gatekeeper设置**：
   - 系统偏好设置 > 安全性与隐私 > 通用
   - 如果显示"VoiceTyper已被阻止"，点击"仍要打开"

2. **查看控制台日志**：
   ```bash
   # 查看应用启动日志
   log show --last 5m --predicate 'subsystem contains "VoiceTyper"'
   ```

## 验证成功标准

✅ **成功的权限申请应该显示**：
- 应用名称：VoiceTyper（带有蓝色手掌图标）
- 权限描述：完整的中文描述
- 对话框标题：包含VoiceTyper而不是Terminal

✅ **权限授予后应该**：
- 应用正常启动
- 录音功能正常工作
- 音频电平显示正常

## 技术细节

### Bundle ID设置
- **开发环境**：各种终端应用的bundle ID
- **打包应用**：`com.bongcaca.voicetyper`

### 代码签名
- **类型**：adhoc签名（本地开发）
- **Entitlements**：包含麦克风和辅助功能权限
- **验证**：`codesign -dv` 显示正确的identifier

### 启动流程
1. `launcher.py` 设置独立进程环境
2. 检查打包应用状态
3. 提前申请权限（在GUI初始化前）
4. 设置环境变量标识
5. 启动 `main.py` 主应用

## 相关文件

- `launcher.py` - 独立启动器
- `VoiceTyper.entitlements` - 权限声明
- `build_app.py` - 构建脚本（包含代码签名）
- `utils/permissions.py` - 权限检查逻辑
- `main.py` - 主应用（包含权限处理）

---

如果测试成功，您应该看到正确的VoiceTyper权限申请对话框，而不是Terminal的权限申请。 