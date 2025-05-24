import os
import platform
import subprocess
import logging
import sys

logger = logging.getLogger(__name__)

def get_current_bundle_id():
    """获取当前进程的bundle ID或标识符"""
    try:
        # 尝试获取当前Python可执行文件的路径
        python_path = sys.executable
        
        # 检查是否运行在打包后的macOS应用中
        if '.app/Contents/MacOS/' in python_path:
            # 从路径中提取应用名称并生成bundle ID
            app_path = python_path.split('.app/Contents/MacOS/')[0] + '.app'
            app_name = os.path.basename(app_path).replace('.app', '')
            if app_name.lower() == 'voicetyper':
                return 'com.bongcaca.voicetyper'  # 打包应用的bundle ID
            else:
                # 通用打包应用的bundle ID生成
                return f'com.pyinstaller.{app_name.lower()}'
        
        # 检查是否在不同的环境中运行
        if 'Cursor' in python_path or 'cursor' in python_path.lower():
            return 'com.todesktop.230313mzl4w4u92'  # Cursor的bundle ID
        elif 'Terminal' in os.environ.get('TERM_PROGRAM', ''):
            return 'com.apple.Terminal'
        elif 'iTerm' in os.environ.get('TERM_PROGRAM', ''):
            return 'com.googlecode.iterm2'
        elif 'Visual Studio Code' in os.environ.get('TERM_PROGRAM', ''):
            return 'com.microsoft.VSCode'
        else:
            # 使用Python的路径作为标识
            return python_path
    except Exception as e:
        logger.warning(f"无法获取bundle ID: {e}")
        return None

def check_tcc_permission(service='kTCCServiceMicrophone'):
    """使用系统API检查TCC权限状态"""
    if platform.system() != "Darwin":
        return True
    
    try:
        bundle_id = get_current_bundle_id()
        if not bundle_id:
            return False
            
        # 使用tccutil检查权限（不需要sudo）
        # 构建查询条件，包含当前bundle ID和常见的相关应用
        query_conditions = [
            f"client='{bundle_id}'",
            "client LIKE '%python%'",
            "client LIKE '%Terminal%'", 
            "client LIKE '%cursor%'",
            "client LIKE '%voicetyper%'",
            "client='com.bongcaca.voicetyper'",
            "client LIKE '%bongcaca%'"
        ]
        query = f"SELECT allowed FROM access WHERE service='{service}' AND ({' OR '.join(query_conditions)}) ORDER BY last_modified DESC LIMIT 1;"
        
        result = subprocess.run([
            'sqlite3', 
            os.path.expanduser('~/Library/Application Support/com.apple.TCC/TCC.db'),
            query
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout.strip() == "1":
            logger.info(f"TCC数据库显示 {service} 权限已授予")
            return True
        else:
            logger.warning(f"TCC数据库显示 {service} 权限未授予")
            return False
            
    except Exception as e:
        logger.warning(f"检查TCC权限失败: {e}")
        return False

def check_microphone_permission():
    """检查麦克风权限状态 - 增强版本"""
    if platform.system() != "Darwin":
        return True
    
    # 首先检查TCC数据库
    tcc_status = check_tcc_permission()
    
    # 然后尝试实际访问麦克风
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        
        try:
            # 尝试打开默认输入设备
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            # 尝试读取一小段数据
            test_data = stream.read(1024, exception_on_overflow=False)
            stream.close()
            pa.terminate()
            
            if test_data and len(test_data) > 0:
                logger.info("麦克风权限检查通过 - 能够访问音频数据")
                return True
            else:
                logger.warning("麦克风权限检查失败 - 无法获取音频数据")
                return False
            
        except Exception as e:
            logger.warning(f"麦克风访问测试失败: {e}")
            pa.terminate()
            return False
            
    except Exception as e:
        logger.error(f"检查麦克风权限时出错: {e}")
        return False

def request_microphone_permission():
    """请求麦克风权限 - 增强版本"""
    if platform.system() != "Darwin":
        return True
    
    try:
        # 尝试访问麦克风以触发权限对话框
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
            # 尝试读取数据以确保真正触发权限检查
            test_data = stream.read(1024, exception_on_overflow=False)
            stream.close()
            pa.terminate()
            
            if test_data and len(test_data) > 0:
                logger.info("麦克风权限已获得")
                return True
            else:
                logger.warning("麦克风权限被拒绝或无音频数据")
                return False
            
        except Exception as e:
            logger.warning(f"麦克风权限申请失败: {e}")
            pa.terminate()
            return False
            
    except Exception as e:
        logger.error(f"请求麦克风权限时出错: {e}")
        return False

def reset_microphone_permission():
    """重置麦克风权限"""
    if platform.system() != "Darwin":
        return True
    
    try:
        logger.info("正在重置麦克风权限...")
        result = subprocess.run(['tccutil', 'reset', 'Microphone'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            logger.info("麦克风权限已重置，请重新运行程序")
            return True
        else:
            logger.error(f"重置权限失败: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"重置权限时出错: {e}")
        return False

def add_manual_permission_instructions():
    """提供手动添加权限的详细说明"""
    bundle_id = get_current_bundle_id()
    
    print("\n" + "="*80)
    print("🔧 手动权限设置指南")
    print("="*80)
    print("如果自动权限申请失败，请按以下步骤手动设置：")
    print()
    print("方法1：使用系统偏好设置")
    print("1. 打开 系统偏好设置 > 安全性与隐私 > 隐私")
    print("2. 选择左侧的 '麦克风'")
    print("3. 如果看到锁图标，点击解锁并输入密码")
    print("4. 在右侧列表中找到并勾选：")
    print("   - Terminal (如果通过终端运行)")
    print("   - Python (如果显示)")
    print("   - 或者你当前使用的应用")
    print()
    print("方法2：重置所有麦克风权限")
    print("在终端中运行以下命令：")
    print("   tccutil reset Microphone")
    print("然后重新运行本程序")
    print()
    if bundle_id:
        print(f"当前进程标识符: {bundle_id}")
    print("="*80)

def show_permission_dialog():
    """显示权限申请提示（命令行版本）- 增强版本"""
    print("\n" + "="*60)
    print("🎤 VoiceTyper 需要麦克风权限")
    print("="*60)
    print("VoiceTyper需要访问您的麦克风来进行语音识别。")
    print()
    print("检测到您可能在命令行环境中运行本程序。")
    print("macOS对命令行应用的权限管理比较严格。")
    print()
    
    # 检查当前运行环境
    term_program = os.environ.get('TERM_PROGRAM', 'Unknown')
    print(f"当前终端环境: {term_program}")
    
    print()
    print("请选择以下选项：")
    print("1. 按 Enter 键尝试触发权限申请")
    print("2. 输入 'reset' 重置麦克风权限")
    print("3. 输入 'manual' 查看手动设置说明")
    print("4. 输入 'quit' 退出程序")
    print("="*60)
    
    try:
        choice = input("请输入选择 [1/reset/manual/quit]: ").strip().lower()
        
        if choice == 'reset':
            return reset_microphone_permission()
        elif choice == 'manual':
            add_manual_permission_instructions()
            return False
        elif choice == 'quit':
            print("程序已退出")
            exit(0)
        else:
            return True  # 默认尝试申请权限
            
    except KeyboardInterrupt:
        print("\n程序已取消")
        exit(1)

def create_app_specific_permission_request():
    """为当前应用创建特定的权限申请"""
    if platform.system() != "Darwin":
        return True
    
    try:
        # 创建一个临时的权限申请脚本
        script_content = '''
tell application "System Events"
    try
        set micPermission to do shell script "tccutil reset Microphone"
        display dialog "已重置麦克风权限，请重新运行VoiceTyper" buttons {"确定"} default button 1
    on error
        display dialog "需要手动设置麦克风权限：\\n1. 打开系统偏好设置\\n2. 选择安全性与隐私\\n3. 选择隐私标签\\n4. 选择麦克风\\n5. 勾选Terminal或Python" buttons {"确定"} default button 1
    end try
end tell
'''
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.scpt', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        # 执行AppleScript
        result = subprocess.run(['osascript', script_path], 
                              capture_output=True, text=True, timeout=30)
        
        # 清理临时文件
        os.unlink(script_path)
        
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"创建权限申请脚本失败: {e}")
        return False 