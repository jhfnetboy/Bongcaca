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
                    
                    # 获取更多窗口细节
                    try:
                        active_app_cmd = '''osascript -e 'tell application "System Events" to get name of application processes whose frontmost is true' '''
                        active_app = subprocess.run(active_app_cmd, shell=True, capture_output=True, text=True).stdout.strip()
                        self.logger.debug(f"活动应用: {active_app}")
                    except Exception as e:
                        self.logger.debug(f"获取活动应用详情失败: {e}")
                    
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
        
        # 在开始前激活目标窗口
        try:
            # 获取当前焦点窗口
            window_name = self.get_focused_window()
            self.logger.debug(f"准备向窗口插入文本: {window_name}")
            
            # 确保目标窗口处于活动状态
            if window_name != "python" and window_name != "Unknown":
                activate_cmd = f'''osascript -e 'tell application "{window_name}" to activate' '''
                subprocess.run(activate_cmd, shell=True)
                self.logger.debug(f"已尝试激活窗口: {window_name}")
                # 等待窗口激活
                time.sleep(0.5)
        except Exception as e:
            self.logger.warning(f"激活窗口失败: {e}")
        
        # 优先使用剪贴板方法（对输入法兼容性最好）
        try:
            # 保存原剪贴板内容
            save_clipboard = subprocess.run('pbpaste', shell=True, capture_output=True, text=True).stdout
            
            # 设置新内容到剪贴板
            set_clip_cmd = ["pbcopy"]
            process = subprocess.Popen(set_clip_cmd, stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            
            # 模拟Command+V
            subprocess.run('osascript -e \'tell application "System Events" to keystroke "v" using command down\'', shell=True)
            
            # 恢复原剪贴板内容
            time.sleep(0.3)
            restore_process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            restore_process.communicate(save_clipboard.encode('utf-8'))
            
            self.logger.debug(f"使用剪贴板方法插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"剪贴板方法失败: {e}")
        
        # 方法1: PyAutoGUI
        try:
            import pyautogui
            # 先确保焦点在正确位置
            pyautogui.click()
            time.sleep(0.2)
            # 模拟击键，一个字符一个字符地输入以提高准确性
            for char in text:
                pyautogui.write(char)
                time.sleep(0.01)  # 添加少量延迟
            self.logger.debug(f"使用PyAutoGUI插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"PyAutoGUI失败: {e}")
            
        # 方法2: AppleScript (增强版)
        try:
            # 使用单引号包围文本内容，避免双引号导致的命令解析错误
            safe_text = text.replace("'", "'\\''")
            
            # 使用System Events直接模拟键盘输入
            cmd = f'''osascript -e 'tell application "System Events" 
                delay 0.5
                keystroke "{safe_text}"
                end tell' '''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.warning(f"AppleScript执行返回非零状态: {result.stderr}")
            
            self.logger.debug(f"使用AppleScript插入文本成功: {text}")
            return True
        except Exception as e:
            methods_tried.append(f"AppleScript失败: {e}")
        
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