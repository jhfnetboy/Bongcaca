import platform
import pyautogui
import time

class TextInput:
    def __init__(self):
        self.system = platform.system()
        
    def input_text(self, text):
        """输入文本到当前焦点位置"""
        try:
            # 模拟键盘输入
            pyautogui.write(text)
            # 添加一个空格
            pyautogui.press('space')
        except Exception as e:
            print(f"Error inputting text: {e}")
            
    def get_focused_window(self):
        """获取当前焦点窗口信息"""
        try:
            if self.system == "Darwin":  # macOS
                import subprocess
                result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of first process whose frontmost is true'], 
                                     capture_output=True, text=True)
                return result.stdout.strip()
            elif self.system == "Windows":
                import win32gui
                return win32gui.GetWindowText(win32gui.GetForegroundWindow())
            else:
                return "Unknown"
        except Exception as e:
            print(f"Error getting focused window: {e}")
            return "Unknown" 