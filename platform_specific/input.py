import logging
import platform
import time
import subprocess

class TextInput:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        self.logger.debug(f"初始化TextInput,平台: {self.system}")
        
    def input_text(self, text):
        """输入文本到当前焦点位置"""
        self.logger.debug(f"使用input_text输入文本: {text}")
        try:
            # 导入pyautogui
            import pyautogui
            # 模拟键盘输入
            pyautogui.write(text)
            # 添加一个空格
            pyautogui.press('space')
            self.logger.debug("使用pyautogui成功输入文本")
            return True
        except Exception as e:
            self.logger.error(f"使用pyautogui输入文本失败: {e}")
            
            # 备用方法
            return self.insert_text(text)
            
    def get_focused_window(self):
        """获取当前焦点窗口信息"""
        try:
            if self.system == "Darwin":  # macOS
                try:
                    result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of first process whose frontmost is true'], 
                                         capture_output=True, text=True)
                    window_name = result.stdout.strip()
                    self.logger.debug(f"当前焦点窗口: {window_name}")
                    return window_name
                except Exception as e:
                    self.logger.error(f"获取macOS焦点窗口失败: {e}")
                    return "Unknown"
            elif self.system == "Windows":
                try:
                    import win32gui
                    window_name = win32gui.GetWindowText(win32gui.GetForegroundWindow())
                    self.logger.debug(f"当前焦点窗口: {window_name}")
                    return window_name
                except Exception as e:
                    self.logger.error(f"获取Windows焦点窗口失败: {e}")
                    return "Unknown"
            else:
                return "Unknown"
        except Exception as e:
            self.logger.error(f"获取焦点窗口失败: {e}")
            return "Unknown"

    def insert_text(self, text):
        """将文本插入到当前光标位置"""
        self.logger.debug(f"尝试插入文本: {text}")
        
        try:
            if self.system == "Darwin":  # macOS
                return self._insert_text_macos(text)
            elif self.system == "Windows":
                return self._insert_text_windows(text)
            elif self.system == "Linux":
                return self._insert_text_linux(text)
            else:
                self.logger.error(f"不支持的平台: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"插入文本失败: {e}")
            return False
            
    def _insert_text_macos(self, text):
        """在macOS上插入文本"""
        methods_tried = []
        
        # 方法1: PyAutoGUI
        try:
            import pyautogui
            pyautogui.write(text)
            self.logger.debug(f"使用PyAutoGUI插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"PyAutoGUI失败: {e}")
            
        # 方法2: AppleScript
        try:
            cmd = f'''osascript -e 'tell application "System Events" to keystroke "{text}"' '''
            subprocess.run(cmd, shell=True)
            self.logger.debug(f"使用AppleScript插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"AppleScript失败: {e}")
            
        # 方法3: pbpaste/pbcopy
        try:
            # 保存原剪贴板内容
            save_clipboard = subprocess.run('pbpaste', shell=True, capture_output=True, text=True).stdout
            
            # 设置新内容到剪贴板
            subprocess.run(f'echo "{text}" | pbcopy', shell=True)
            
            # 模拟Command+V
            subprocess.run('osascript -e \'tell application "System Events" to keystroke "v" using command down\'', shell=True)
            
            # 恢复原剪贴板内容
            time.sleep(0.5)
            subprocess.run(f'echo "{save_clipboard}" | pbcopy', shell=True)
            
            self.logger.debug(f"使用剪贴板方法插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"剪贴板方法失败: {e}")
        
        # 所有方法都失败了
        error_msg = ", ".join(methods_tried)
        self.logger.error(f"所有macOS文本插入方法都失败了: {error_msg}")
        return False
            
    def _insert_text_windows(self, text):
        """在Windows上插入文本"""
        methods_tried = []
        
        # 方法1: PyAutoGUI
        try:
            import pyautogui
            pyautogui.write(text)
            self.logger.debug(f"使用PyAutoGUI插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"PyAutoGUI失败: {e}")
            
        # 方法2: 剪贴板
        try:
            import win32clipboard
            import win32con
            import win32api
            
            # 保存原剪贴板内容
            win32clipboard.OpenClipboard()
            try:
                save_clipboard = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            except:
                save_clipboard = ""
            win32clipboard.CloseClipboard()
            
            # 设置新内容到剪贴板
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            
            # 模拟Ctrl+V
            win32api.keybd_event(0x11, 0, 0, 0)  # Ctrl down
            win32api.keybd_event(0x56, 0, 0, 0)  # V down
            win32api.keybd_event(0x56, 0, 2, 0)  # V up
            win32api.keybd_event(0x11, 0, 2, 0)  # Ctrl up
            
            # 恢复原剪贴板内容
            time.sleep(0.5)
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(save_clipboard, win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            
            self.logger.debug(f"使用剪贴板方法插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"剪贴板方法失败: {e}")
            
        # 所有方法都失败了
        error_msg = ", ".join(methods_tried)
        self.logger.error(f"所有Windows文本插入方法都失败了: {error_msg}")
        return False
            
    def _insert_text_linux(self, text):
        """在Linux上插入文本"""
        methods_tried = []
        
        # 方法1: PyAutoGUI
        try:
            import pyautogui
            pyautogui.write(text)
            self.logger.debug(f"使用PyAutoGUI插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"PyAutoGUI失败: {e}")
            
        # 方法2: xdotool
        try:
            subprocess.run(f'xdotool type "{text}"', shell=True)
            self.logger.debug(f"使用xdotool插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"xdotool失败: {e}")
            
        # 方法3: 剪贴板
        try:
            # 保存原剪贴板内容
            save_clipboard = subprocess.run('xclip -o -selection clipboard', shell=True, capture_output=True, text=True).stdout
            
            # 设置新内容到剪贴板
            subprocess.run(f'echo "{text}" | xclip -i -selection clipboard', shell=True)
            
            # 模拟Ctrl+V
            subprocess.run('xdotool key ctrl+v', shell=True)
            
            # 恢复原剪贴板内容
            time.sleep(0.5)
            subprocess.run(f'echo "{save_clipboard}" | xclip -i -selection clipboard', shell=True)
            
            self.logger.debug(f"使用剪贴板方法插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"剪贴板方法失败: {e}")
            
        # 所有方法都失败了
        error_msg = ", ".join(methods_tried)
        self.logger.error(f"所有Linux文本插入方法都失败了: {error_msg}")
        return False 