import os
import platform
import subprocess
import logging

logger = logging.getLogger(__name__)

def check_microphone_permission():
    """检查麦克风权限状态"""
    if platform.system() != "Darwin":
        # 非macOS系统，直接返回True
        return True
    
    try:
        # 直接尝试访问麦克风来检查权限，这比查询数据库更准确
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
            # 如果能成功打开，说明有权限
            stream.close()
            pa.terminate()
            logger.info("麦克风权限检查通过")
            return True
            
        except Exception as e:
            logger.warning(f"麦克风权限检查失败: {e}")
            pa.terminate()
            return False
            
    except Exception as e:
        logger.error(f"检查麦克风权限时出错: {e}")
        return False

def request_microphone_permission():
    """请求麦克风权限"""
    if platform.system() != "Darwin":
        return True
    
    try:
        # 尝试访问麦克风以触发权限对话框
        import pyaudio
        pa = pyaudio.PyAudio()
        
        # 尝试打开默认输入设备
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            # 如果能成功打开，说明有权限
            stream.close()
            pa.terminate()
            logger.info("麦克风权限已获得")
            return True
            
        except Exception as e:
            logger.warning(f"麦克风权限被拒绝: {e}")
            pa.terminate()
            return False
            
    except Exception as e:
        logger.error(f"请求麦克风权限时出错: {e}")
        return False

def show_permission_dialog():
    """显示权限申请提示（命令行版本）"""
    print("\n" + "="*60)
    print("🎤 VoiceTyper 需要麦克风权限")
    print("="*60)
    print("VoiceTyper需要访问您的麦克风来进行语音识别。")
    print()
    print("请按以下步骤操作：")
    print("1. 按 Enter 键触发权限申请")
    print("2. 如果系统弹出权限对话框，请点击'允许'")
    print("3. 如果没有弹出对话框，请手动设置权限：")
    print("   - 打开 系统偏好设置 > 安全性与隐私 > 隐私")
    print("   - 选择 麦克风")
    print("   - 确保 Python 或终端已勾选")
    print("="*60)
    
    # 等待用户确认
    try:
        input("按 Enter 键继续...")
    except KeyboardInterrupt:
        print("\n程序已取消")
        exit(1) 