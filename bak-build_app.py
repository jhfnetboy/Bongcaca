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

# 初始化 Qt 应用程序
from PySide6.QtWidgets import QApplication
app = QApplication([])

# 设置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("build_app")

def check_requirements():
    """检查打包所需的依赖是否已安装"""
    try:
        import PyInstaller
        logger.info("PyInstaller 已安装")
    except ImportError:
        logger.error("缺少 PyInstaller 依赖，请先安装: pip install pyinstaller")
        return False
    
    # 检查平台特定依赖
    if sys.platform == "darwin":  # macOS
        # 检查 iconutil
        try:
            subprocess.run(["iconutil", "--help"], capture_output=True, check=False)
            logger.info("iconutil 可用")
        except FileNotFoundError:
            logger.warning("未找到 iconutil 命令，可能无法生成正确的应用图标")
        
        # 检查 create-dmg
        try:
            subprocess.run(["create-dmg", "--version"], capture_output=True, check=False)
            logger.info("create-dmg 可用")
        except FileNotFoundError:
            logger.warning("未找到 create-dmg，将不能创建 DMG 安装包。可以通过以下命令安装: brew install create-dmg")
    
    elif sys.platform == "win32":  # Windows
        # 检查 Inno Setup 是否存在
        inno_path = Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")
        if not inno_path.exists():
            inno_path = Path("C:/Program Files/Inno Setup 6/ISCC.exe")
            
        if not inno_path.exists():
            logger.warning("未找到 Inno Setup，将不能创建 Windows 安装程序。请从 https://jrsoftware.org/isdl.php 下载安装")
    
    return True

def prepare_resources():
    """准备资源文件"""
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)
    
    # 确保图标目录存在
    icons_dir = resources_dir / "icons"
    icons_dir.mkdir(exist_ok=True)
    
    # 生成应用图标
    try:
        from ui.logo import create_logo_pixmap
        
        # 为 Windows 生成 .ico 文件
        if sys.platform == "win32":
            from PIL import Image
            import io
            
            # 创建不同尺寸的图像
            images = []
            for size in [16, 32, 48, 64, 128, 256]:
                pixmap = create_logo_pixmap(size)
                byte_array = io.BytesIO()
                pixmap.save(byte_array, format='PNG')
                byte_array.seek(0)
                img = Image.open(byte_array)
                images.append(img)
                
            # 保存为 ICO 文件
            icon_file = icons_dir / "app_icon.ico"
            images[0].save(str(icon_file), format='ICO', 
                          sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
                          append_images=images[1:])
            logger.info(f"Windows 图标已生成: {icon_file}")
        
        # 为 macOS 生成 PNG 文件
        elif sys.platform == "darwin":
            png_file = icons_dir / "app_icon.png"
            pixmap = create_logo_pixmap(1024)  # 大尺寸图标
            pixmap.save(str(png_file))
            logger.info(f"macOS 图标已生成: {png_file}")
            
            # 尝试生成 .icns 文件
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
    
    # 创建 Info.plist 模板 (macOS)
    if sys.platform == "darwin":
        plist_file = resources_dir / "Info.plist"
        with open(plist_file, 'w', encoding='utf-8') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
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
    <string>1.0.0</string>
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
    
    # 创建 Windows 版本信息文件
    if sys.platform == "win32":
        version_file = resources_dir / "version_info.txt"
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write('''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
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
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'VoiceTyper'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024 BongCaCa'),
        StringStruct(u'OriginalFilename', u'VoiceTyper.exe'),
        StringStruct(u'ProductName', u'Voice Typer'),
        StringStruct(u'ProductVersion', u'1.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x0409, 1200])])
  ]
)''')
        logger.info(f"Windows 版本信息文件已生成: {version_file}")
        
        # 创建 Inno Setup 脚本
        inno_script = resources_dir / "installer.iss"
        with open(inno_script, 'w', encoding='utf-8') as f:
            f.write('''#define MyAppName "Voice Typer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "BongCaCa"
#define MyAppURL "https://github.com/yourusername/voicetyper"
#define MyAppExeName "VoiceTyper.exe"

[Setup]
AppId={{B673DE85-CAA9-4B24-A2F9-C8A68F8C2C7D}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=installer
OutputBaseFilename=VoiceTyper_Setup
SetupIconFile=resources\\icons\\app_icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "开机自动启动"; GroupDescription: "启动选项"

[Files]
Source: "dist\\VoiceTyper\\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: startupicon

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
''')
        logger.info(f"Windows 安装程序脚本已生成: {inno_script}")
    
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
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--name=VoiceTyper",
        "--windowed",
        "--onefile",
        "--noconfirm",
        "--clean",
        *icon_param,
        "--osx-bundle-identifier=com.bongcaca.voicetyper",
        "--debug=all",
        "--add-data=resources:resources",
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
            # 备份原始文件
            shutil.copy(plist_path, str(plist_path) + ".bak")
            logger.info(f"成功备份原始Info.plist到 {plist_path}.bak")
            
            # 直接修改最终的 Info.plist 文件，确保包含所有必要权限
            from plistlib import load, dump
            
            # 读取当前plist
            with open(plist_path, 'rb') as f:
                plist_data = load(f)
            
            # 添加必要的权限说明
            plist_data['NSMicrophoneUsageDescription'] = '需要麦克风权限进行语音输入'
            plist_data['NSAppleEventsUsageDescription'] = '需要控制其他应用以插入文本'
            
            # 写回修改后的plist
            with open(plist_path, 'wb') as f:
                dump(plist_data, f)
            
            logger.info(f"已更新应用的Info.plist并添加必要的权限声明")
            
            # 设置文件权限
            import stat
            os.chmod(str(plist_path), stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            logger.info(f"已设置Info.plist权限: 644")
            
            # 验证最终的Info.plist内容
            with open(plist_path, 'rb') as f:
                final_plist = load(f)
                logger.info(f"最终的Info.plist包含以下权限声明:")
                if 'NSMicrophoneUsageDescription' in final_plist:
                    logger.info(f"✓ 麦克风权限: {final_plist['NSMicrophoneUsageDescription']}")
                else:
                    logger.error(f"✗ 缺少麦克风权限声明")
                
                if 'NSAppleEventsUsageDescription' in final_plist:
                    logger.info(f"✓ AppleEvents权限: {final_plist['NSAppleEventsUsageDescription']}")
                else:
                    logger.error(f"✗ 缺少AppleEvents权限声明")
        
        except Exception as e:
            logger.error(f"修改Info.plist时出错: {e}")
            logger.warning("将尝试使用备份方法更新Info.plist")
            
            # 备份方法：直接覆盖Info.plist文件
            custom_plist = resources_dir / "Info.plist"
            if custom_plist.exists():
                # 确保模板文件包含正确的权限声明
                with open(custom_plist, 'r', encoding='utf-8') as f:
                    plist_content = f.read()
                
                # 检查并添加必要的权限声明
                if "<key>NSMicrophoneUsageDescription</key>" not in plist_content:
                    logger.warning("添加缺失的麦克风权限声明到Info.plist模板")
                    plist_content = plist_content.replace('</dict>', '''    <key>NSMicrophoneUsageDescription</key>
    <string>需要麦克风权限进行语音输入</string>
</dict>''')
                
                if "<key>NSAppleEventsUsageDescription</key>" not in plist_content:
                    logger.warning("添加缺失的AppleEvents权限声明到Info.plist模板")
                    plist_content = plist_content.replace('</dict>', '''    <key>NSAppleEventsUsageDescription</key>
    <string>需要控制其他应用以插入文本</string>
</dict>''')
                
                # 写入更新后的模板
                with open(custom_plist, 'w', encoding='utf-8') as f:
                    f.write(plist_content)
                
                # 复制到应用目录
                shutil.copy(custom_plist, plist_path)
                logger.info(f"使用自定义模板覆盖Info.plist文件")
        
        # 检查应用结构
        logger.info("检查打包应用的结构:")
        app_contents = app_path / "Contents"
        logger.info(f"应用目录: {app_path}")
        
        # 检查主要文件和目录
        for path in ["MacOS/VoiceTyper", "Info.plist", "Resources"]:
            full_path = app_contents / path
            if os.path.exists(full_path):
                logger.info(f"✓ 存在: {path}")
            else:
                logger.error(f"✗ 缺失: {path}")
        
        # 检查库和框架
        frameworks_path = app_contents / "Frameworks"
        if os.path.exists(frameworks_path):
            logger.info(f"包含 {len(os.listdir(frameworks_path))} 个框架文件")
        else:
            logger.warning("缺少Frameworks目录")
    
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
    logger.info("注意: 如果应用运行后无法访问麦克风，请检查系统偏好设置中的权限。")
    logger.info("提示: 首次启动应用时，macOS会询问是否允许访问麦克风，请点击\"允许\"。")
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
        # 确保输出目录存在
        installer_dir = Path("installer")
        installer_dir.mkdir(exist_ok=True)
        
        # 找到 Inno Setup 编译器
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