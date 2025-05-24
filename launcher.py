#!/usr/bin/env python3
"""
VoiceTyper 独立启动器
确保应用以独立进程身份运行，正确触发权限申请
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def set_process_title():
    """设置进程标题为VoiceTyper"""
    try:
        import setproctitle
        setproctitle.setproctitle("VoiceTyper")
    except ImportError:
        # 如果没有setproctitle，使用其他方法
        pass

def ensure_independent_process():
    """确保以独立进程身份运行"""
    # 设置进程组
    try:
        os.setpgrp()
    except OSError:
        pass
    
    # 分离控制终端
    try:
        if os.isatty(sys.stdin.fileno()):
            # 如果还连接着终端，尝试分离
            pass
    except:
        pass

def check_app_environment():
    """检查应用运行环境"""
    executable_path = sys.executable
    
    # 检查是否在打包应用中运行
    is_packaged = '.app/Contents/MacOS/' in executable_path
    
    if is_packaged:
        print(f"✅ 运行在打包应用中: {executable_path}")
        app_path = executable_path.split('.app/Contents/MacOS/')[0] + '.app'
        print(f"📱 应用路径: {app_path}")
        
        # 检查Info.plist
        info_plist = Path(app_path) / "Contents" / "Info.plist"
        if info_plist.exists():
            print(f"✅ Info.plist 存在: {info_plist}")
        else:
            print(f"❌ Info.plist 不存在: {info_plist}")
    else:
        print(f"ℹ️  运行在开发环境中: {executable_path}")
    
    return is_packaged

def request_permissions_early():
    """尽早请求权限，确保在GUI初始化前完成"""
    try:
        # 导入权限检查模块
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from utils.permissions import (
            check_microphone_permission,
            request_microphone_permission,
            get_current_bundle_id
        )
        
        bundle_id = get_current_bundle_id()
        print(f"🔑 当前Bundle ID: {bundle_id}")
        
        # 立即检查和申请权限
        if not check_microphone_permission():
            print("🎤 正在申请麦克风权限...")
            success = request_microphone_permission()
            if success:
                print("✅ 麦克风权限获取成功")
            else:
                print("❌ 麦克风权限获取失败")
                return False
        else:
            print("✅ 麦克风权限已存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 权限检查失败: {e}")
        return False

def main():
    """主启动函数"""
    print("🚀 VoiceTyper 启动器")
    print("=" * 50)
    
    # 设置进程属性
    set_process_title()
    ensure_independent_process()
    
    # 检查运行环境
    is_packaged = check_app_environment()
    
    # 如果是打包应用，尽早申请权限
    if is_packaged:
        print("\n🔐 正在检查权限...")
        if not request_permissions_early():
            print("⚠️  权限检查失败，应用可能无法正常工作")
    
    print("\n🎯 启动主应用...")
    
    # 设置环境变量，标识通过launcher启动
    os.environ['VOICETYPER_LAUNCHED_BY_LAUNCHER'] = 'true'
    
    # 导入并运行主应用
    try:
        # 确保能找到主模块
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # 导入主应用模块
        import main
        
        # 运行主应用
        main.main()
        
    except KeyboardInterrupt:
        print("\n👋 用户取消，应用退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 