#!/usr/bin/env python3
"""
VoiceTyper 权限修复工具
帮助解决macOS命令行环境下的麦克风权限问题
"""

import os
import sys
import subprocess
import platform
import tempfile
import time

def print_banner():
    """显示工具banner"""
    print("="*60)
    print("🔧 VoiceTyper 权限修复工具")
    print("="*60)
    print("此工具将帮助您解决macOS命令行环境下的麦克风权限问题")
    print()

def check_system():
    """检查系统环境"""
    if platform.system() != "Darwin":
        print("❌ 此工具仅适用于macOS系统")
        return False
    
    print("✅ 检测到macOS系统")
    
    # 检查当前环境
    term_program = os.environ.get('TERM_PROGRAM', 'Unknown')
    print(f"📱 当前终端环境: {term_program}")
    
    # 检查Python路径
    python_path = sys.executable
    print(f"🐍 Python路径: {python_path}")
    
    return True

def check_current_permissions():
    """检查当前权限状态"""
    print("\n🔍 检查当前权限状态...")
    
    try:
        # 检查TCC数据库
        result = subprocess.run([
            'sqlite3', 
            os.path.expanduser('~/Library/Application Support/com.apple.TCC/TCC.db'),
            "SELECT client, allowed, last_modified FROM access WHERE service='kTCCServiceMicrophone' ORDER BY last_modified DESC;"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and result.stdout.strip():
            print("📊 当前麦克风权限状态:")
            lines = result.stdout.strip().split('\n')
            for line in lines[:5]:  # 只显示最近5条
                parts = line.split('|')
                if len(parts) >= 2:
                    client = parts[0]
                    allowed = "✅ 允许" if parts[1] == "1" else "❌ 拒绝"
                    print(f"   {client}: {allowed}")
        else:
            print("⚠️  无法读取TCC数据库或没有相关权限记录")
            
    except Exception as e:
        print(f"⚠️  检查权限状态失败: {e}")

def test_microphone_access():
    """测试麦克风访问"""
    print("\n🎤 测试麦克风访问...")
    
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            
            # 尝试读取数据
            test_data = stream.read(1024, exception_on_overflow=False)
            stream.close()
            pa.terminate()
            
            if test_data and len(test_data) > 0:
                print("✅ 麦克风访问成功！")
                return True
            else:
                print("❌ 麦克风访问失败 - 无音频数据")
                return False
                
        except Exception as e:
            print(f"❌ 麦克风访问失败: {e}")
            pa.terminate()
            return False
            
    except ImportError:
        print("❌ 无法导入pyaudio模块")
        return False

def reset_all_permissions():
    """重置所有麦克风权限"""
    print("\n🔄 重置所有麦克风权限...")
    
    try:
        result = subprocess.run(['tccutil', 'reset', 'Microphone'], 
                              capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("✅ 麦克风权限已重置")
            print("💡 请重新运行VoiceTyper以触发权限申请")
            return True
        else:
            print(f"❌ 重置权限失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 重置权限时出错: {e}")
        return False

def add_terminal_permission():
    """尝试为Terminal添加麦克风权限"""
    print("\n🔐 尝试为Terminal添加麦克风权限...")
    
    # 创建AppleScript来打开权限设置
    script_content = '''
tell application "System Preferences"
    activate
    set current pane to pane "com.apple.preference.security"
    delay 1
    tell application "System Events"
        tell process "System Preferences"
            try
                click tab "Privacy" of window 1
                delay 1
                click row 8 of table 1 of scroll area 1 of tab group 1 of window 1 -- 麦克风
                delay 1
            end try
        end tell
    end tell
end tell

display dialog "请在打开的系统偏好设置中：\\n1. 确保选择了'麦克风'选项\\n2. 勾选'Terminal'或'Python'\\n3. 关闭系统偏好设置\\n4. 重新运行VoiceTyper" buttons {"确定"} default button 1
'''
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scpt', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        result = subprocess.run(['osascript', script_path], 
                              capture_output=True, text=True, timeout=60)
        
        os.unlink(script_path)
        
        if result.returncode == 0:
            print("✅ 已打开系统偏好设置")
            return True
        else:
            print(f"⚠️  打开系统偏好设置失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 创建权限申请脚本失败: {e}")
        return False

def show_manual_instructions():
    """显示手动操作说明"""
    print("\n📖 手动设置权限说明:")
    print("="*50)
    print("1. 打开 系统偏好设置")
    print("2. 选择 安全性与隐私")
    print("3. 点击 隐私 标签")
    print("4. 在左侧列表中选择 麦克风")
    print("5. 点击左下角的锁图标并输入密码")
    print("6. 在右侧列表中勾选以下项目之一:")
    print("   • Terminal")
    print("   • Python")
    print("   • 您使用的终端应用")
    print("7. 关闭系统偏好设置")
    print("8. 重新运行 VoiceTyper")
    print("="*50)

def create_profile_method():
    """使用配置描述文件方法（需要进一步研究）"""
    print("\n📋 配置描述文件方法（实验性）...")
    print("⚠️  此方法需要企业管理权限，通常不适用于个人用户")
    
    # 这里可以添加配置描述文件的创建逻辑
    # 但通常需要企业管理员权限，对普通用户不适用
    
def main():
    """主函数"""
    print_banner()
    
    if not check_system():
        return
    
    check_current_permissions()
    
    # 测试当前麦克风访问状态
    if test_microphone_access():
        print("\n🎉 恭喜！麦克风权限正常，您可以直接使用VoiceTyper")
        return
    
    print("\n🚨 检测到麦克风权限问题，请选择解决方案:")
    print("1. 重置所有麦克风权限（推荐）")
    print("2. 打开系统偏好设置手动添加权限")
    print("3. 查看详细的手动操作说明")
    print("4. 退出")
    
    try:
        choice = input("\n请输入选择 [1/2/3/4]: ").strip()
        
        if choice == "1":
            if reset_all_permissions():
                print("\n✅ 权限重置完成！")
                print("💡 请现在运行以下命令来启动VoiceTyper:")
                print("   ./run.sh")
                print("系统将重新询问麦克风权限，请选择'允许'")
        elif choice == "2":
            add_terminal_permission()
        elif choice == "3":
            show_manual_instructions()
        elif choice == "4":
            print("👋 再见！")
        else:
            print("❌ 无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作")
    except Exception as e:
        print(f"\n❌ 操作失败: {e}")

if __name__ == "__main__":
    main() 