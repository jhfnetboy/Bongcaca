#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Voice Typer 应用打包脚本
支持 macOS 和 Windows 平台
"""

import os
import sys
import subprocess
import shutil
import logging
from pathlib import Path
import argparse
import time
from datetime import datetime

# 初始化 Qt 应用程序
from PySide6.QtWidgets import QApplication
app = QApplication([])

# 设置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("build_app")

# 版本信息
VERSION = "0.23.43"
BUILD_DATE = datetime.now().strftime("%Y-%m-%d")

def get_version_info():
    """获取版本信息"""
    return {
        "version": VERSION,
        "build_date": BUILD_DATE,
        "file_version": tuple(map(int, VERSION.split("."))) + (0,),
        "product_version": tuple(map(int, VERSION.split("."))) + (0,)
    }

def check_requirements():
    """检查打包所需的依赖是否已安装"""
    required_tools = {
        "PyInstaller": "pip install pyinstaller",
        "PIL": "pip install pillow"
    }
    
    if sys.platform == "darwin":
        required_tools.update({
            "iconutil": "系统自带",
            "create-dmg": "brew install create-dmg"
        })
    elif sys.platform == "win32":
        required_tools.update({
            "Inno Setup": "https://jrsoftware.org/isdl.php"
        })
    
    missing_tools = []
    for tool, install_cmd in required_tools.items():
        try:
            if tool == "PyInstaller":
                import PyInstaller
            elif tool == "PIL":
                from PIL import Image
            elif tool == "iconutil" and sys.platform == "darwin":
                subprocess.run(["iconutil", "--help"], capture_output=True, check=False)
            elif tool == "create-dmg" and sys.platform == "darwin":
                subprocess.run(["create-dmg", "--version"], capture_output=True, check=False)
            elif tool == "Inno Setup" and sys.platform == "win32":
                inno_path = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
                if not inno_path.exists():
                    inno_path = Path("C:/Program Files/Inno Setup 6/ISCC.exe")
                if not inno_path.exists():
                    raise FileNotFoundError
            logger.info(f"{tool} 已安装")
        except (ImportError, FileNotFoundError):
            missing_tools.append((tool, install_cmd))
    
    if missing_tools:
        logger.error("缺少以下依赖:")
        for tool, install_cmd in missing_tools:
            logger.error(f"- {tool}: {install_cmd}")
        return False
    return True

def create_icon_files(icons_dir):
    """创建应用图标文件"""
    try:
        from ui.logo import create_logo_pixmap
        
        if sys.platform == "win32":
            from PIL import Image
            import io
            
            images = []
            for size in [16, 32, 48, 64, 128, 256]:
                pixmap = create_logo_pixmap(size)
                byte_array = io.BytesIO()
                pixmap.save(byte_array, format='PNG')
                byte_array.seek(0)
                img = Image.open(byte_array)
                images.append(img)
            
            icon_file = icons_dir / "app_icon.ico"
            images[0].save(str(icon_file), format='ICO', 
                          sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
                          append_images=images[1:])
            logger.info(f"Windows 图标已生成: {icon_file}")
        
        elif sys.platform == "darwin":
            png_file = icons_dir / "app_icon.png"
            pixmap = create_logo_pixmap(1024)
            pixmap.save(str(png_file))
            logger.info(f"macOS 图标已生成: {png_file}")
            
            try:
                from ui.macos_app_icon import create_macos_app_icon
                icns_path = create_macos_app_icon()
                if icns_path and os.path.exists(icns_path):
                    icns_file = icons_dir / "app_icon.icns"
                    shutil.copy(icns_path, str(icns_file))
                    logger.info(f"macOS .icns 图标已复制到资源目录: {icns_file}")
            except Exception as e:
                logger.error(f"生成 .icns 文件失败: {e}")
                logger.info("将使用 PNG 图标替代")
                
    except Exception as e:
        logger.error(f"准备图标资源失败: {e}")
        return False
    return True

def create_info_plist(resources_dir):
    """创建 macOS Info.plist 文件"""
    version_info = get_version_info()
    plist_file = resources_dir / "Info.plist"
    with open(plist_file, 'w', encoding='utf-8') as f:
        f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>Voice Typer</string>
    <key>CFBundleName</key>
    <string>VoiceTyper</string>
    <key>CFBundleIdentifier</key>
    <string>com.bongcaca.voicetyper</string>
    <key>CFBundleVersion</key>
    <string>{version_info['version']}</string>
    <key>CFBundleShortVersionString</key>
    <string>{version_info['version']}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>需要麦克风权限进行语音输入</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>需要控制其他应用以插入文本</string>
</dict>
</plist>''')
    logger.info(f"macOS Info.plist 模板已生成: {plist_file}")
    return True

def create_version_info(resources_dir):
    """创建 Windows 版本信息文件"""
    version_info = get_version_info()
    version_file = resources_dir / "version_info.txt"
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(f'''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_info['file_version']},
    prodvers={version_info['product_version']},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'BongCaCa'),
        StringStruct(u'FileDescription', u'Voice Typer'),
        StringStruct(u'FileVersion', u'{version_info['version']}'),
        StringStruct(u'InternalName', u'VoiceTyper'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024 BongCaCa'),
        StringStruct(u'OriginalFilename', u'VoiceTyper.exe'),
        StringStruct(u'ProductName', u'Voice Typer'),
        StringStruct(u'ProductVersion', u'{version_info['version']}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x0409, 1200])])
  ]
)''')
    logger.info(f"Windows 版本信息文件已生成: {version_file}")
    return True

def create_inno_script(resources_dir):
    """创建 Inno Setup 脚本"""
    version_info = get_version_info()
    inno_script = resources_dir / "installer.iss"
    with open(inno_script, 'w', encoding='utf-8') as f:
        f.write(f'''#define MyAppName "Voice Typer"
#define MyAppVersion "{version_info['version']}"
#define MyAppPublisher "BongCaCa"
#define MyAppURL "https://github.com/yourusername/voicetyper"
#define MyAppExeName "VoiceTyper.exe"

[Setup]
AppId={{B673DE85-CAA9-4B24-A2F9-C8A68F8C2C7D}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
OutputDir=installer
OutputBaseFilename=VoiceTyper_Setup
SetupIconFile=resources\\icons\\app_icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"
Name: "startupicon"; Description: "开机自动启动"; GroupDescription: "启动选项"

[Files]
Source: "dist\\VoiceTyper\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon
Name: "{{userstartup}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: startupicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent
''')
    logger.info(f"Windows 安装程序脚本已生成: {inno_script}")
    return True

def prepare_resources():
    """准备资源文件"""
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    icons_dir = resources_dir / "icons"
    icons_dir.mkdir(exist_ok=True)
    
    if not create_icon_files(icons_dir):
        return False
    
    if sys.platform == "darwin":
        if not create_info_plist(resources_dir):
            return False
    elif sys.platform == "win32":
        if not create_version_info(resources_dir):
            return False
        if not create_inno_script(resources_dir):
            return False
    
    return True

def build_macos():
    """构建 macOS 应用程序"""
    logger.info("开始构建 macOS 应用...")
    
    resources_dir = Path("resources")
    icon_file = resources_dir / "icons" / "app_icon.icns"
    if not icon_file.exists():
        icon_file = resources_dir / "icons" / "app_icon.png"
        if not icon_file.exists():
            logger.warning("未找到应用图标，将使用默认图标")
            icon_param = []
        else:
            icon_param = ["--icon", str(icon_file)]
    else:
        icon_param = ["--icon", str(icon_file)]
    
    # 优化构建命令
    cmd = [
        "pyinstaller",
        "--name=VoiceTyper",
        "--windowed",
        "--onefile",
        "--noconfirm",
        "--clean",
        *icon_param,
        "--osx-bundle-identifier=com.bongcaca.voicetyper",
        # 添加优化参数
        "--noupx",  # 禁用 UPX 压缩，因为它可能导致一些问题
        "--strip",  # 移除调试符号
        # 排除不需要的模块
        "--exclude-module=matplotlib",
        "--exclude-module=notebook",
        "--exclude-module=PIL.ImageQt",
        "--exclude-module=PyQt5",
        "--exclude-module=PyQt6",
        "--exclude-module=tkinter",
        # 只包含必要的数据文件
        "--add-data=resources/icons:resources/icons",
        # 优化 Python 字节码
        "--python-option=O",
        "main.py"
    ]
    
    logger.info(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"构建失败: {result.stderr}")
        return False
    
    logger.info("应用构建成功")
    
    # 修复 Info.plist
    app_path = Path("dist/VoiceTyper.app")
    plist_path = app_path / "Contents" / "Info.plist"
    if plist_path.exists():
        try:
            from plistlib import load, dump
            
            with open(plist_path, 'rb') as f:
                plist_data = load(f)
            
            plist_data['NSMicrophoneUsageDescription'] = '需要麦克风权限进行语音输入'
            plist_data['NSAppleEventsUsageDescription'] = '需要控制其他应用以插入文本'
            
            with open(plist_path, 'wb') as f:
                dump(plist_data, f)
            
            logger.info("已更新应用的Info.plist并添加必要的权限声明")
            
            import stat
            os.chmod(str(plist_path), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            logger.info("已设置Info.plist权限: 644")
        
        except Exception as e:
            logger.error(f"修改Info.plist时出错: {e}")
            return False
    
    # 创建 DMG 前清理不必要的文件
    try:
        # 删除 __pycache__ 目录
        for pycache in app_path.rglob("__pycache__"):
            shutil.rmtree(pycache)
        # 删除 .pyc 文件
        for pyc in app_path.rglob("*.pyc"):
            pyc.unlink()
        # 删除测试文件
        for test in app_path.rglob("test_*.py"):
            test.unlink()
        logger.info("已清理不必要的文件")
    except Exception as e:
        logger.warning(f"清理文件时出错: {e}")

    # 创建 DMG
    try:
        logger.info("创建 DMG 安装镜像...")
        dmg_cmd = [
            "create-dmg",
            "--volname", "VoiceTyper",
            "--window-pos", "200", "120",
            "--window-size", "800", "450",
            "--icon-size", "100",
            "--icon", "VoiceTyper.app", "200", "190",
            "--app-drop-link", "600", "185",
            "--format", "UDZO",  # 使用 UDZO 格式进行压缩
            "--no-internet-enable",  # 禁用网络链接
            "VoiceTyper.dmg",
            "dist/VoiceTyper.app"
        ]
        
        dmg_result = subprocess.run(dmg_cmd, capture_output=True, text=True)
        if dmg_result.returncode != 0:
            logger.error(f"创建 DMG 失败: {dmg_result.stderr}")
            logger.info("请检查 create-dmg 是否已安装: brew install create-dmg")
        else:
            logger.info("DMG 安装镜像已创建: VoiceTyper.dmg")
    except Exception as e:
        logger.error(f"创建 DMG 时出错: {e}")
    
    logger.info(f"macOS 应用已构建完成: {app_path}")
    return True

def build_windows():
    """构建 Windows 应用程序"""
    logger.info("开始构建 Windows 应用...")
    
    resources_dir = Path("resources")
    icon_file = resources_dir / "icons" / "app_icon.ico"
    if not icon_file.exists():
        logger.warning("未找到应用图标，将使用默认图标")
        icon_param = []
    else:
        icon_param = ["--icon", str(icon_file)]
    
    version_file = resources_dir / "version_info.txt"
    if version_file.exists():
        version_param = ["--version-file", str(version_file)]
    else:
        version_param = []
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--name=VoiceTyper",
        "--windowed",
        "--onefile",
        "--noconfirm",
        "--clean",
        *icon_param,
        *version_param,
        "--add-data=resources;resources",
        "main.py"
    ]
    
    logger.info(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"构建失败: {result.stderr}")
        return False
    
    logger.info("应用构建成功")
    
    # 创建安装程序
    try:
        installer_dir = Path("installer")
        installer_dir.mkdir(exist_ok=True)
        
        iscc_path = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
        if not iscc_path.exists():
            iscc_path = Path("C:/Program Files/Inno Setup 6/ISCC.exe")
        
        if not iscc_path.exists():
            logger.error("未找到 Inno Setup 编译器，跳过创建安装程序")
            logger.info("请从 https://jrsoftware.org/isdl.php 下载安装 Inno Setup")
            return True
        
        inno_script = resources_dir / "installer.iss"
        logger.info("创建 Windows 安装程序...")
        
        cmd = [str(iscc_path), str(inno_script)]
        inno_result = subprocess.run(cmd, capture_output=True, text=True)
        
        if inno_result.returncode != 0:
            logger.error(f"创建安装程序失败: {inno_result.stderr}")
        else:
            logger.info("Windows 安装程序已创建: installer/VoiceTyper_Setup.exe")
    except Exception as e:
        logger.error(f"创建安装程序时出错: {e}")
    
    logger.info("Windows 应用已构建完成: dist/VoiceTyper.exe")
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Voice Typer 应用打包工具")
    parser.add_argument("--platform", choices=["auto", "macos", "windows"], default="auto",
                        help="目标平台，默认为当前系统")
    parser.add_argument("--skip-deps-check", action="store_true", 
                        help="跳过依赖检查")
    args = parser.parse_args()
    
    # 确定目标平台
    platform = args.platform
    if platform == "auto":
        if sys.platform == "darwin":
            platform = "macos"
        elif sys.platform == "win32":
            platform = "windows"
        else:
            logger.error(f"不支持的平台: {sys.platform}")
            return 1
    
    logger.info(f"开始构建 Voice Typer 应用，目标平台: {platform}")
    logger.info(f"版本: {VERSION}，构建日期: {BUILD_DATE}")
    
    # 检查依赖
    if not args.skip_deps_check and not check_requirements():
        return 1
    
    # 准备资源
    if not prepare_resources():
        logger.error("准备资源失败，终止构建")
        return 1
    
    # 根据平台执行构建
    if platform == "macos":
        if sys.platform != "darwin":
            logger.error("只能在 macOS 系统上构建 macOS 应用")
            return 1
        if not build_macos():
            return 1
    elif platform == "windows":
        if sys.platform != "win32":
            logger.error("只能在 Windows 系统上构建 Windows 应用")
            return 1
        if not build_windows():
            return 1
    
    logger.info("应用构建完成")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 