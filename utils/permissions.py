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
        # 使用系统命令检查麦克风权限
        result = subprocess.run([
            "sqlite3", 
            f"{os.path.expanduser('~')}/Library/Application Support/com.apple.TCC/TCC.db",
            "SELECT allowed FROM access WHERE service='kTCCServiceMicrophone' AND client LIKE '%python%' ORDER BY last_modified DESC LIMIT 1;"
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout.strip() == "1":
            return True
        else:
            return False
            
    except Exception as e:
        logger.warning(f"无法检查麦克风权限状态: {e}")
        # 如果检查失败，假设需要权限申请
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
    """显示权限申请对话框"""
    try:
        from PySide6.QtWidgets import QMessageBox
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("麦克风权限")
        msg.setText("VoiceTyper需要访问您的麦克风来进行语音识别。")
        msg.setInformativeText(
            "请在系统弹出的权限对话框中点击'允许'，\n"
            "或者在系统偏好设置 > 安全性与隐私 > 隐私 > 麦克风\n"
            "中手动开启VoiceTyper的麦克风权限。"
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
        
    except Exception as e:
        logger.error(f"显示权限对话框时出错: {e}") 