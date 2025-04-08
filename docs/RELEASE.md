# 如何将应用发布到GitHub

本文档介绍如何将打包好的Voice Typer应用（.dmg或.exe）发布到GitHub，使用户可以轻松下载和安装。

## 准备工作

1. 确保你已经有了一个GitHub仓库
2. 确保你已经使用
```
pip install pyinstaller
brew install create-dmg

python build_app.py
```
脚本成功打包了应用程序
3. 安装[GitHub CLI](https://cli.github.com/)（可选，但推荐）

## 步骤1：创建新的发布版本

### 使用GitHub Web界面

1. 打开浏览器，访问你的GitHub仓库页面
2. 点击右侧的"Releases"
3. 点击"Create a new release"（创建新发布）
4. 填写版本号（例如v0.23.29）
5. A. 添加标题（例如"Voice Typer 0.23.29"）
   B. 添加版本说明，可以从CHANGES.md复制最新版本的更新内容

### 使用GitHub CLI

```bash
# 登录GitHub（如果尚未登录）
gh auth login

# 创建新版本
gh release create v0.23.29 --title "Voice Typer 0.23.29" --notes "在此处添加版本说明"
```

## 步骤2：上传打包文件

### 使用GitHub Web界面

1. 在创建发布页面上，找到"Attach binaries by dropping them here or selecting them"部分
2. 点击"选择文件"，上传以下文件：
   - macOS用户: `VoiceTyper.dmg`
   - Windows用户: `installer/VoiceTyper_Setup.exe`

### 使用GitHub CLI

```bash
# 上传macOS应用
gh release upload v0.23.29 VoiceTyper.dmg

# 上传Windows应用
gh release upload v0.23.29 installer/VoiceTyper_Setup.exe
```

## 步骤3：发布版本

### 使用GitHub Web界面

1. 确认所有信息都已填写，所有文件都已上传
2. 选择"发布版本"按钮

### 使用GitHub CLI

发布已经在创建时完成，无需额外步骤。

## 步骤4：验证发布

1. 访问你的GitHub仓库
2. 点击"Releases"查看所有发布
3. 确认最新的发布包含正确的版本号、说明和附件文件
4. 尝试下载附件文件并安装，确保它们可以正常工作

## 发布说明的最佳实践

在发布说明中，建议包含以下内容：

1. 版本亮点：简要介绍此版本的主要新功能或改进
2. 详细更新列表：列出所有更改（功能、修复、改进等）
3. 已知问题：列出任何已知但尚未解决的问题
4. 安装说明：简要说明如何安装应用
5. 系统要求：列出运行应用所需的最低系统配置

## 自动化发布流程（进阶）

对于经常发布的项目，可以考虑使用GitHub Actions自动化发布流程：

1. 在仓库中创建`.github/workflows/release.yml`文件
2. 配置工作流，在打标签时自动创建发布并上传文件
3. 推送代码和标签，触发自动发布流程

示例工作流文件（仅供参考）：

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
          brew install create-dmg
      - name: Build app
        run: python build_app.py
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: macos-app
          path: VoiceTyper.dmg

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller pywin32
          # Install Inno Setup (would need additional scripting)
      - name: Build app
        run: python build_app.py
      - name: Upload artifact
        uses: actions/upload-artifact@v2
        with:
          name: windows-app
          path: dist/VoiceTyper.exe

  create-release:
    needs: [build-macos, build-windows]
    runs-on: ubuntu-latest
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v2
      - name: Create Release
        id: create_release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Voice Typer ${{ github.ref }}
          draft: false
          prerelease: false
      - name: Upload macOS App
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: ./macos-app/VoiceTyper.dmg
          asset_name: VoiceTyper.dmg
          asset_content_type: application/octet-stream
      - name: Upload Windows App
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: ./windows-app/VoiceTyper.exe
          asset_name: VoiceTyper.exe
          asset_content_type: application/octet-stream
```

## 常见问题解答

### Q: 文件大小超过GitHub上传限制怎么办？
A: GitHub单个文件上传限制为100MB。如果你的应用包超过此限制，可以考虑：
- 使用[Git LFS](https://git-lfs.github.com/)
- 分割文件后上传
- 使用外部存储服务（如AWS S3、Google Drive等）

### Q: 如何在发布页面添加下载次数统计？
A: GitHub自动跟踪发布资产的下载统计，无需额外设置。

### Q: 如何撤回有问题的发布？
A: 在GitHub的Releases页面，找到有问题的发布，点击"Edit"，然后标记为"pre-release"或"draft"，或者完全删除该发布。 