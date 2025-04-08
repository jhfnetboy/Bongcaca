import logging
import platform
import pyautogui
import time

class TextInput:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        self.logger.debug(f"Initializing TextInput for platform: {self.system}")
        
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

    def insert_text(self, text):
        """将文本插入到当前光标位置"""
        self.logger.debug(f"Inserting text: {text}")
        
        try:
            if self.system == "Darwin":  # macOS
                self._insert_text_macos(text)
            elif self.system == "Windows":
                self._insert_text_windows(text)
            elif self.system == "Linux":
                self._insert_text_linux(text)
            else:
                self.logger.error(f"Unsupported platform: {self.system}")
        except Exception as e:
            self.logger.error(f"Failed to insert text: {e}")
            
    def _insert_text_macos(self, text):
        """在macOS上插入文本"""
        try:
            pyautogui.write(text)
            self.logger.debug("Text inserted using pyautogui on macOS")
        except ImportError:
            self.logger.error("pyautogui not installed, cannot insert text")
        except Exception as e:
            self.logger.error(f"Error inserting text on macOS: {e}")
            
    def _insert_text_windows(self, text):
        """在Windows上插入文本"""
        try:
            pyautogui.write(text)
            self.logger.debug("Text inserted using pyautogui on Windows")
        except ImportError:
            self.logger.error("pyautogui not installed, cannot insert text")
        except Exception as e:
            self.logger.error(f"Error inserting text on Windows: {e}")
            
    def _insert_text_linux(self, text):
        """在Linux上插入文本"""
        try:
            pyautogui.write(text)
            self.logger.debug("Text inserted using pyautogui on Linux")
        except ImportError:
            self.logger.error("pyautogui not installed, cannot insert text")
        except Exception as e:
            self.logger.error(f"Error inserting text on Linux: {e}") 