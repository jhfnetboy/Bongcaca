from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QComboBox, QMessageBox, QTextEdit, QHBoxLayout, QRadioButton, QButtonGroup, QFrame, QFormLayout, QLineEdit, QSplitter
from PySide6.QtCore import Qt, QTimer, QPointF, Signal, QObject, Slot, QSize, QUrl, QThread, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QPainter, QColor, QPolygonF, QPalette, QLinearGradient, QBrush, QPen, QFont, QPixmap, QPainterPath, QFontMetrics, QDesktopServices
import numpy as np
import logging
import time
import os
import platform
import subprocess
from ui.logo import create_app_icon, create_logo_pixmap
from version import get_version
import tempfile
import json
import datetime
import pyaudio
import re
import threading
from typing import List, Dict, Any
from pathlib import Path

class AudioVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(50)
        self.audio_level = 0
        self.levels = []
        self.max_levels = 50
        self.is_recording = False
        
        # 初始化波形
        for _ in range(self.max_levels):
            self.levels.append(10)  # 初始显示浅粉色波形
            
    def update_level(self, level):
        self.audio_level = level
        self.levels.append(level)
        if len(self.levels) > self.max_levels:
            self.levels.pop(0)
        self.update()
        
    def set_recording(self, is_recording):
        self.is_recording = is_recording
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        # 绘制波形
        width = self.width()
        height = self.height()
        bar_width = width / self.max_levels
        x = 0
        
        for level in self.levels:
            bar_height = (level / 100) * height
            y = (height - bar_height) / 2
            
            # 根据音量大小设置颜色
            if level > 50:
                color = QColor(255, 0, 128)  # 深粉色
            elif level > 20:
                color = QColor(255, 105, 180)  # 粉色
            else:
                color = QColor(255, 182, 193)  # 浅粉色
                
            painter.fillRect(x, y, bar_width, bar_height, color)
            x += bar_width

class ToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_recording = False
        self.setFixedSize(40, 40)
        self.setStyleSheet("""
            QPushButton {
                border-radius: 20px;
                background-color: white;
                border: 1px solid #ccc;
            }
        """)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.is_recording:
            # 绘制绿色三角形(开始)
            painter.setBrush(QColor(0, 200, 0))  # 绿色三角形
            painter.setPen(Qt.NoPen)
            points = [
                QPointF(15, 10),
                QPointF(15, 30),
                QPointF(30, 20)
            ]
            painter.drawPolygon(points)
        else:
            # 绘制红色方块(停止)
            painter.setBrush(QColor(255, 0, 0))  # 红色方块
            painter.setPen(Qt.NoPen)
            painter.drawRect(12, 12, 16, 16)
            
    def set_recording(self, is_recording):
        self.is_recording = is_recording
        self.update()

# 创建一个信号类
class DeviceSignals(QObject):
    device_changed = Signal(int)

class AboutDialog(QMessageBox):
    """关于对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 Voice Typer")
        
        # 使用HTML格式，支持链接
        about_text = f"""
        <h2>Voice Typer v{get_version()}</h2>
        <p>一个开源的本地语音输入工具，支持中英文语音识别</p>
        <p>支持平台: macOS, Windows</p>
        <p>作者: <a href="https://blog.jlab.tech/about">JLab</a></p>
        <p>GitHub: <a href="https://github.com/jhfnetboy/Bongcaca">@jhfnetboy/Bongcaca</a></p>
        <p>使用技术: faster-whisper, PySide6, PyAudio</p>
        """
        
        self.setText(about_text)
        self.setTextFormat(Qt.RichText)  # 使用富文本格式以支持链接
        
        # 添加Logo
        self.setIconPixmap(create_logo_pixmap(128))
        
        # 添加链接点击处理
        self.setStandardButtons(QMessageBox.Ok)
        
    def mousePressEvent(self, event):
        # 获取文本内容，处理链接点击
        text = self.text()
        if "href" in text:
            import re
            links = re.findall(r'href="([^"]+)"', text)
            for link in links:
                QDesktopServices.openUrl(QUrl(link))
        super().mousePressEvent(event)

class FloatingWindow(QMainWindow):
    # 定义自定义信号
    toggle_recording_signal = Signal()
    transcription_mode_changed = Signal(str)  # 新增模式切换信号
    model_changed = Signal(str)  # 新增模型切换信号
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Voice Typer")
        
        # 设置应用图标
        self.setWindowIcon(create_app_icon())
        
        # 配置对象
        self.config = config
        
        # 初始化logger
        self.logger = logging.getLogger(__name__)
        
        # 创建信号对象
        self.signals = DeviceSignals()
        self.device_changed = self.signals.device_changed
        
        # 设备初始化状态
        self.device_initialized = False
        self.is_recording = False
        self.transcription_mode = "batch"  # 默认是批量模式
        self.available_models = []  # 可用模型列表
        self.last_transcription = ""  # 最近的转写结果
        self.target_language = "auto"  # 默认不翻译，自动检测语言
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局 - 改为水平布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 减少边距
        main_layout.setSpacing(0)  # 减少组件间间距
        
        # 创建拆分器
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧面板
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setSpacing(10)  # 设置组件间距
        left_layout.setContentsMargins(10, 10, 10, 10)  # 设置内边距
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        # 版本标签
        version_label = QLabel(f"v{get_version()}")
        version_label.setStyleSheet("color: #888; font-size: 10px;")
        toolbar_layout.addWidget(version_label)
        
        # 添加弹簧
        toolbar_layout.addStretch()
        
        # 关于按钮
        about_button = QPushButton("关于")
        about_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: #3778b7;
                font-size: 12px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        about_button.setCursor(Qt.PointingHandCursor)
        about_button.clicked.connect(self.show_about_dialog)
        toolbar_layout.addWidget(about_button)
        
        left_layout.addLayout(toolbar_layout)
        
        # 创建设备选择标签
        device_label = QLabel("Select Input Device:")
        device_label.setAlignment(Qt.AlignCenter)
        device_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(device_label)
        
        # 创建设备选择下拉框
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                min-height: 30px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
            }
            QComboBox:disabled {
                background-color: #f0f0f0;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ccc;
                background-color: white;
                selection-background-color: #3778b7;
                selection-color: white;
                color: black;
                font-size: 14px;
            }
        """)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        left_layout.addWidget(self.device_combo)
        
        # 添加模型选择框
        model_label = QLabel("Select Model:")
        model_label.setAlignment(Qt.AlignCenter)
        model_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                min-height: 30px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
            }
            QComboBox:disabled {
                background-color: #f0f0f0;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ccc;
                background-color: white;
                selection-background-color: #3778b7;
                selection-color: white;
                color: black;
                font-size: 14px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left: 1px solid #ccc;
            }
        """)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        left_layout.addWidget(self.model_combo)
        
        # 添加模型下载按钮
        self.download_button = QPushButton("Download Model")
        self.download_button.setStyleSheet("""
            QPushButton {
                padding: 8px;
                min-height: 30px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f0f0f0;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #a0a0a0;
            }
        """)
        self.download_button.clicked.connect(self.on_download_model)
        left_layout.addWidget(self.download_button)
        
        # 添加模式选择框
        mode_frame = QFrame()
        mode_frame.setFrameShape(QFrame.StyledPanel)
        mode_frame.setStyleSheet("QFrame { background-color: #f0f0f0; border-radius: 4px; padding: 5px; }")
        mode_layout = QVBoxLayout(mode_frame)
        
        mode_group = QButtonGroup(self)
        
        mode_buttons_layout = QHBoxLayout()
        self.batch_mode_radio = QRadioButton("Batch")
        self.batch_mode_radio.setChecked(True)  # 默认选中批量模式
        self.batch_mode_radio.setStyleSheet("QRadioButton { font-size: 14px; min-height: 25px; }")
        self.realtime_mode_radio = QRadioButton("Realtime")
        self.realtime_mode_radio.setStyleSheet("QRadioButton { font-size: 14px; min-height: 25px; }")
        
        mode_group.addButton(self.batch_mode_radio)
        mode_group.addButton(self.realtime_mode_radio)
        
        mode_buttons_layout.addWidget(self.batch_mode_radio)
        mode_buttons_layout.addWidget(self.realtime_mode_radio)
        mode_layout.addLayout(mode_buttons_layout)
        
        # 连接模式切换信号
        self.batch_mode_radio.toggled.connect(self.on_mode_changed)
        
        left_layout.addWidget(mode_frame)
        
        # 添加语言翻译选择框
        lang_frame = QFrame()
        lang_frame.setFrameShape(QFrame.StyledPanel)
        lang_frame.setStyleSheet("QFrame { background-color: #f0f0f0; border-radius: 4px; padding: 5px; }")
        lang_layout = QVBoxLayout(lang_frame)
        
        self.lang_combo = QComboBox()
        self.lang_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                min-height: 30px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                font-size: 14px;
            }
            QComboBox:disabled {
                background-color: #f0f0f0;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ccc;
                background-color: white;
                selection-background-color: #3778b7;
                selection-color: white;
                color: black;
                font-size: 14px;
            }
        """)
        
        # 添加支持的语言选项
        languages = [
            ("auto", "Auto Detect (不翻译)"),
            ("zh", "中文"),
            ("en", "English (英文)"),
            ("th", "ภาษาไทย (泰文)"),
            ("ur", "اردو (乌尔都语)"),
            ("ja", "日本語 (日文)"),
            ("ko", "한국어 (韩文)"),
            ("de", "Deutsch (德文)"),
            ("fr", "Français (法文)"),
            ("es", "Español (西班牙文)")
        ]
        
        for code, name in languages:
            self.lang_combo.addItem(name, code)
            
        self.lang_combo.currentIndexChanged.connect(self.on_target_language_changed)
        lang_layout.addWidget(self.lang_combo)
        
        left_layout.addWidget(lang_frame)
        
        # 创建录音按钮
        self.toggle_button = ToggleButton()
        self.toggle_button.clicked.connect(self.on_toggle_recording)
        self.toggle_button.setEnabled(False)  # 初始禁用
        left_layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        
        # 创建音频可视化器
        self.visualizer = AudioVisualizer()
        left_layout.addWidget(self.visualizer)
        
        # 创建状态标签
        self.status_label = QLabel("初始化设备中...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 13px;
            }
        """)
        left_layout.addWidget(self.status_label)
        
        # 创建右侧面板，放置文本显示区域
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建文本显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        right_layout.addWidget(self.result_text)
        
        # 将左右面板添加到拆分器
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        
        # 设置拆分器初始尺寸比例(左:右)
        self.splitter.setSizes([325, 406])
        
        # 设置拆分器处理样式
        self.splitter.setHandleWidth(1)  # 设置分隔线宽度
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #ccc;
            }
            QSplitter::handle:hover {
                background-color: #999;
            }
        """)
        
        # 创建折叠按钮
        self.toggle_panel_btn = QPushButton("◀")
        self.toggle_panel_btn.setFixedSize(20, 60)
        self.toggle_panel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.toggle_panel_btn.clicked.connect(self.toggle_right_panel)
        
        # 添加组件到主布局
        main_layout.addWidget(self.splitter)
        main_layout.addWidget(self.toggle_panel_btn)
        
        # 设置日志处理器
        self.logger.addHandler(self.LogHandler(self))
        
        # 设置窗口大小
        self.setFixedSize(650, 650)
        
        # 初始化设备列表
        self.init_device_list()
        
        # 初始化模型列表
        self.init_model_list()
        
        # 创建定时器用于在非录音状态下更新波形
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.update_idle_visualization)
        self.idle_timer.start(100)  # 100毫秒更新一次
        
    def toggle_right_panel(self):
        """折叠/展开右侧面板"""
        if self.right_panel.isVisible():
            self.right_panel.hide()
            self.toggle_panel_btn.setText("▶")
            # 保存拆分器状态
            self.splitter_state = self.splitter.saveState()
            # 调整窗口大小
            self.setFixedSize(400, 650)
            # 调整左侧面板边距，给更多空间
            self.left_panel.layout().setContentsMargins(15, 15, 15, 15)
        else:
            self.right_panel.show()
            self.toggle_panel_btn.setText("◀")
            # 恢复左侧面板原有边距
            self.left_panel.layout().setContentsMargins(10, 10, 10, 10)
            # 如果有保存的状态则恢复
            if hasattr(self, 'splitter_state'):
                self.splitter.restoreState(self.splitter_state)
            # 恢复窗口大小
            self.setFixedSize(650, 650)
        
    def keyPressEvent(self, event):
        """处理键盘事件"""
        # 处理空格键触发录音
        if event.key() == Qt.Key_Space:
            self.toggle_button.click()
            event.accept()
            return
            
        # 添加Ctrl+T快捷键切换右侧面板
        if event.key() == Qt.Key_T and event.modifiers() == Qt.ControlModifier:
            self.toggle_panel_btn.click()
            event.accept()
            return
            
        # 添加Shift+V快捷键直接输入最后的转写结果
        if event.key() == Qt.Key_V and event.modifiers() == Qt.ShiftModifier:
            if hasattr(self, 'last_transcription') and self.last_transcription:
                try:
                    from platform_specific.input import TextInput
                    text_input = TextInput()
                    
                    # 尝试直接插入最近的转写文本
                    result = text_input.insert_text(self.last_transcription)
                    if result:
                        self.logger.info("已使用快捷键插入最近的转写文本")
                        self.status_label.setText("已插入最近的转写文本")
                    else:
                        self.logger.error("使用快捷键插入文本失败")
                except Exception as e:
                    self.logger.error(f"快捷键插入文本失败: {e}")
            else:
                self.logger.warning("没有可用的转写结果可插入")
                self.status_label.setText("没有可用的转写结果可插入")
            event.accept()
            return
            
        # 添加双击Shift功能 - 需要在类中跟踪状态
        if event.key() == Qt.Key_Shift:
            current_time = time.time()
            if hasattr(self, 'last_shift_press') and (current_time - self.last_shift_press) < 0.5:
                # 双击Shift检测到
                if hasattr(self, 'last_transcription') and self.last_transcription:
                    try:
                        from platform_specific.input import TextInput
                        text_input = TextInput()
                        
                        # 尝试直接插入最近的转写文本
                        result = text_input.insert_text(self.last_transcription)
                        if result:
                            self.logger.info("已使用双击Shift插入最近的转写文本")
                            self.status_label.setText("已插入最近的转写文本")
                        else:
                            self.logger.error("使用双击Shift插入文本失败")
                    except Exception as e:
                        self.logger.error(f"双击Shift插入文本失败: {e}")
                else:
                    self.logger.warning("没有可用的转写结果可插入")
                    self.status_label.setText("没有可用的转写结果可插入")
                self.last_shift_press = 0  # 重置，避免连续触发
            else:
                self.last_shift_press = current_time
            event.accept()
            return
            
        # 调用父类方法处理其他键盘事件
        super().keyPressEvent(event)
            
    def on_toggle_recording(self):
        """切换录音状态"""
        if not self.device_initialized:
            self.logger.warning("设备未初始化，请先选择输入设备")
            return
            
        if not self.model_initialized:
            self.logger.warning("模型未初始化，请等待模型加载完成")
            return
            
        if not self.is_recording:
            # 开始录音
            self.is_recording = True
            self.toggle_button.set_recording(True)
            self.status_label.setText("正在录音...")
            self.toggle_recording_signal.emit()
            # 发出开始提示音
            os.system('afplay /System/Library/Sounds/Ping.aiff')
        else:
            # 停止录音
            self.is_recording = False
            self.toggle_button.set_recording(False)
            self.status_label.setText("正在处理...")
            self.toggle_recording_signal.emit()
        
    def init_device_list(self):
        """初始化设备列表"""
        import pyaudio
        
        try:
            self.logger.debug("开始初始化设备列表...")
            p = pyaudio.PyAudio()
            info = p.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            
            # 清空下拉框
            self.device_combo.clear()
            
            # 记录输入设备
            input_devices = []
            
            for i in range(num_devices):
                try:
                    device_info = p.get_device_info_by_index(i)
                    if device_info and device_info.get('maxInputChannels') > 0:
                        device_name = device_info.get('name')
                        input_devices.append((i, device_name))
                        self.device_combo.addItem(device_name, i)
                        self.logger.debug(f"添加输入设备: {device_name} (ID: {i})")
                except Exception as e:
                    self.logger.error(f"获取设备信息失败: {e}")
                    
            p.terminate()
            
            # 如果有输入设备,默认选择第一个
            if len(input_devices) > 0:
                self.device_combo.setCurrentIndex(0)
                device_id = self.device_combo.currentData()
                self.logger.info(f"默认选择输入设备: {self.device_combo.currentText()} (ID: {device_id})")
                self.device_initialized = True  # 标记设备已初始化
                self.toggle_button.setEnabled(True)
                self.status_label.setText("就绪,点击开始录音")
                
                # 延迟发出设备变更信号,确保窗口完全初始化
                QTimer.singleShot(100, lambda: self.device_changed.emit(device_id))
            else:
                self.toggle_button.setEnabled(False)
                self.status_label.setText("未找到输入设备")
                self.device_initialized = False
                
        except Exception as e:
            self.logger.error(f"初始化设备列表失败: {e}")
            self.status_label.setText(f"初始化设备失败: {str(e)}")
            self.device_initialized = False
            
    def on_device_changed(self, index):
        """设备切换事件"""
        if index >= 0:
            device_id = self.device_combo.currentData()
            self.logger.info(f"已选择设备: {self.device_combo.currentText()} (ID: {device_id})")
            # 发出设备改变信号
            self.device_changed.emit(device_id)
            
    def update_result(self, text):
        """更新转写结果"""
        self.result_text.append(text)
        self.status_label.setText("转写完成")
        # 发出完成提示音（两声）
        os.system('afplay /System/Library/Sounds/Ping.aiff')
        time.sleep(0.2)
        os.system('afplay /System/Library/Sounds/Ping.aiff')
        
        # 确保文本区域滚动到最新内容
        scrollbar = self.result_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 保存最新的转写结果到应用剪贴板
        self.last_transcription = text
        
        # 自动将文本复制到系统剪贴板
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                self.logger.info("转写结果已复制到剪贴板，可使用Command+V粘贴")
                self.status_label.setText("转写结果已复制到剪贴板 (Command+V 粘贴)")
            elif system == "Windows":
                # Windows剪贴板操作
                import win32clipboard
                import win32con
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                self.logger.info("转写结果已复制到剪贴板，可使用Ctrl+V粘贴")
                self.status_label.setText("转写结果已复制到剪贴板 (Ctrl+V 粘贴)")
            else:  # Linux
                subprocess.run(f'echo "{text}" | xclip -i -selection clipboard', shell=True)
                self.logger.info("转写结果已复制到剪贴板，可使用Ctrl+V粘贴")
                self.status_label.setText("转写结果已复制到剪贴板 (Ctrl+V 粘贴)")
        except Exception as e:
            self.logger.error(f"复制到剪贴板失败: {e}")
            
        # 将文本输出到当前光标位置
        try:
            # 这里保留原有的自动插入文本功能，但不再默认执行
            # 现在我们只保存文本到剪贴板，用户可以通过快捷键粘贴
            pass
                
        except Exception as e:
            self.logger.error(f"插入文本过程中出错: {e}")
        
    def update_audio_level(self, level):
        """更新音频电平"""
        self.visualizer.update_level(level)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
        
    def show_recording(self):
        """显示录音状态"""
        self.status_label.setText("Recording...")
        self.logger.info("Recording started")
        
    def show_processing(self):
        """显示处理状态"""
        self.status_label.setText("Processing...")
        self.logger.info("Processing audio...")
        
    def show_result(self, text):
        """显示识别结果"""
        self.status_label.setText(f"Result: {text}")
        self.logger.info(f"Recognition result: {text}")
        
    def update_audio_level(self, level):
        """更新音量显示"""
        self.visualizer.update_level(level)
        self.logger.debug(f"Audio level: {level}%")

    def get_selected_device_id(self):
        """获取当前选择的设备ID"""
        if self.device_combo.count() == 0:
            return None
        return self.device_combo.currentData()
        
    def get_selected_language(self):
        """获取当前选择的语言，如果是auto则返回中文(zh)"""
        lang = self.target_language
        if lang == "auto":
            return "zh"  # 默认使用中文
        return lang
        
    def get_target_language(self):
        """获取目标翻译语言，如果是auto则返回None表示不翻译"""
        if self.target_language == "auto":
            return None
        return self.target_language
        
    def update_status(self, status_text):
        """更新状态文本"""
        self.status_label.setText(status_text)
        
    def update_recording_state(self, is_recording):
        """更新录音状态"""
        self.is_recording = is_recording  # 更新窗口的录音状态标记
        self.toggle_button.set_recording(is_recording)
        self.visualizer.set_recording(is_recording)
        self.logger.debug(f"更新录音按钮状态: {'录音中(红色方块)' if is_recording else '未录音(绿色三角)'}")

    def on_mode_changed(self, checked):
        """模式切换事件"""
        if checked:  # 只在选中时触发
            self.transcription_mode = "batch" if self.batch_mode_radio.isChecked() else "realtime"
            self.logger.info(f"转写模式已切换为: {self.transcription_mode}")
            self.transcription_mode_changed.emit(self.transcription_mode)
            
            # 根据模式更新状态提示
            if self.transcription_mode == "batch":
                mode_desc = "批量模式 - 停止录音后进行转写"
            else:
                mode_desc = "实时模式 - 录音时实时转写"
                
            self.status_label.setText(f"模式: {mode_desc}")

    def init_model_list(self):
        """初始化模型列表"""
        try:
            self.logger.info("正在检测已下载的模型...")
            self.model_combo.clear()
            self.available_models = []
            
            # 从配置中获取上次选择的模型
            last_model = None
            try:
                if self.config:
                    last_model = self.config.get("last_model")
                    if last_model:
                        self.logger.info(f"找到上次使用的模型: {last_model}")
            except Exception as e:
                self.logger.error(f"读取上次模型设置失败: {e}")
            
            # 检查模型目录
            model_paths = [
                ("large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")),
                ("medium", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-medium")),
                ("small", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-small")),
                ("base", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-base")),
                ("tiny", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-tiny")),
                ("distil-large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-large-v3")),
                ("distil-small.en", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-small.en")),
                ("distil-medium.en", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-medium.en"))
            ]
            
            # 打印所有模型路径信息
            self.logger.info("----- 模型检测开始 -----")
            for model_name, model_path in model_paths:
                if os.path.exists(model_path):
                    model_size = self._get_directory_size(model_path)
                    self.logger.info(f"✓ 找到模型: {model_name} (路径: {model_path}, 大小: {self._format_size(model_size)})")
                else:
                    self.logger.info(f"✗ 未找到模型: {model_name} (预期路径: {model_path})")
            self.logger.info("----- 模型检测结束 -----")
            
            # 更新结果文本区域
            self.result_text.append("----- 模型检测结果 -----")
            
            found_models = []
            for model_name, model_path in model_paths:
                if os.path.exists(model_path):
                    model_size = self._get_directory_size(model_path)
                    found_models.append((model_name, model_path, model_size))
                    self.available_models.append(model_name)
                    self.model_combo.addItem(f"{model_name} (已下载，{self._format_size(model_size)})", model_name)
                    self.result_text.append(f"✓ 找到模型: {model_name} (大小: {self._format_size(model_size)})")
            
            # 如果没有找到已下载的模型，添加可下载选项
            if not found_models:
                self.logger.warning("未找到已下载的模型，请下载模型")
                self.model_combo.addItem("请下载模型", None)
                self.download_button.setEnabled(True)
                self.result_text.append("未找到已下载的模型，请使用'Download Model'按钮下载")
            else:
                # 添加可下载的其他模型
                self.model_combo.addItem("---可下载模型---", None)
                available_to_download = ["large-v3", "medium", "small", "base", "tiny", "distil-large-v3", "distil-small.en", "distil-medium.en"]
                for model in available_to_download:
                    if model not in self.available_models:
                        self.model_combo.addItem(f"{model} (点击下载按钮下载)", model)
                
                # 添加删除模型选项
                self.model_combo.addItem("---删除模型---", None)
                for model_name, model_path, model_size in found_models:
                    self.model_combo.addItem(f"删除 {model_name} ({self._format_size(model_size)})", f"del_{model_name}")
                
                # 首先尝试设置上次使用的模型
                selected_index = 0  # 默认使用第一个
                if last_model and last_model in self.available_models:
                    # 查找上次使用的模型的索引
                    for i in range(self.model_combo.count()):
                        if self.model_combo.itemData(i) == last_model:
                            selected_index = i
                            break
                    self.logger.info(f"使用上次选择的模型: {last_model}")
                else:
                    self.logger.info(f"未找到上次模型或首次使用，使用默认模型: {found_models[0][0]}")
                
                # 设置选中的模型
                self.model_combo.setCurrentIndex(selected_index)
                selected_model = self.model_combo.currentData()
                
                self.result_text.append(f"已找到 {len(found_models)} 个已下载模型，使用: {selected_model}")
            
        except Exception as e:
            self.logger.error(f"初始化模型列表失败: {e}")
            self.result_text.append(f"初始化模型列表失败: {str(e)}")
            
    def _get_directory_size(self, path):
        """获取目录大小（字节）"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
        except Exception as e:
            self.logger.error(f"计算目录大小出错: {e}")
        return total_size
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.2f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.2f} GB"
    
    def on_model_changed(self, index):
        """模型切换事件"""
        if index >= 0:
            model_name = self.model_combo.currentData()
            if model_name:
                if model_name.startswith("del_"):
                    # 处理删除模型请求
                    real_model_name = model_name[4:]  # 去掉"del_"前缀
                    # 显示确认对话框
                    reply = QMessageBox.question(
                        self, 
                        "确认删除模型", 
                        f"确定要删除模型 {real_model_name} 吗？\n删除后将无法使用该模型，需要重新下载。",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        # 确认删除模型
                        model_path = ""
                        for name, path in [
                            ("large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")),
                            ("medium", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-medium")),
                            ("small", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-small")),
                            ("base", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-base")),
                            ("tiny", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-tiny")),
                            ("distil-large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-large-v3")),
                            ("distil-small.en", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-small.en")),
                            ("distil-medium.en", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-medium.en"))
                        ]:
                            if name == real_model_name:
                                model_path = path
                                break
                        
                        if model_path and os.path.exists(model_path):
                            try:
                                # 删除模型目录
                                import shutil
                                shutil.rmtree(model_path)
                                self.logger.info(f"已删除模型: {real_model_name}")
                                self.status_label.setText(f"已删除模型: {real_model_name}")
                                
                                # 从已下载列表中移除
                                if real_model_name in self.available_models:
                                    self.available_models.remove(real_model_name)
                                
                                # 重新刷新模型列表
                                self.init_model_list()
                            except Exception as e:
                                self.logger.error(f"删除模型失败: {e}")
                                QMessageBox.warning(self, "删除失败", f"删除模型 {real_model_name} 失败: {str(e)}")
                        else:
                            self.logger.error(f"找不到模型路径: {real_model_name}")
                            QMessageBox.warning(self, "删除失败", f"找不到模型 {real_model_name} 的路径")
                    
                    # 重置下拉框到第一个有效模型
                    for i in range(self.model_combo.count()):
                        item_data = self.model_combo.itemData(i)
                        if item_data and not item_data.startswith("del_") and item_data != None:
                            self.model_combo.setCurrentIndex(i)
                            break
                    
                    return
                
                self.logger.info(f"已选择模型: {model_name}")
                
                # 将当前选择的模型保存到配置
                try:
                    if self.config:
                        self.config.set("last_model", model_name)
                        self.logger.debug(f"已保存当前模型选择: {model_name}")
                except Exception as e:
                    self.logger.error(f"保存模型选择失败: {e}")
                
                # 发出模型改变信号
                self.model_changed.emit(model_name)
            else:
                # 分隔符或未下载模型
                self.download_button.setEnabled(True)

    def on_download_model(self):
        """下载模型按钮事件"""
        try:
            # 获取当前选择的模型
            current_index = self.model_combo.currentIndex()
            model_name = self.model_combo.currentData()
            
            if not model_name or model_name in self.available_models:
                # 如果未选择或已下载，则显示选择对话框
                models_to_download = []
                models_info = [
                    ("tiny", "39MB - 最小质量(英文)", "https://huggingface.co/Systran/faster-whisper-tiny"),
                    ("base", "74MB - 较低质量", "https://huggingface.co/Systran/faster-whisper-base"),
                    ("small", "244MB - 平衡质量", "https://huggingface.co/Systran/faster-whisper-small"),
                    ("medium", "769MB - 高质量", "https://huggingface.co/Systran/faster-whisper-medium"),
                    ("large-v3", "2.9GB - 最高质量", "https://huggingface.co/Systran/faster-whisper-large-v3"),
                    ("distil-large-v3", "2.3GB - 较高质量", "https://huggingface.co/Systran/faster-distil-whisper-large-v3"),
                    ("distil-small.en", "240MB - 仅英文优化", "https://huggingface.co/Systran/faster-distil-whisper-small.en"),
                    ("distil-medium.en", "763MB - 仅英文高质量", "https://huggingface.co/Systran/faster-distil-whisper-medium.en")
                ]
                
                for name, info, url in models_info:
                    if name not in self.available_models:
                        models_to_download.append((name, info, url))
                
                if not models_to_download:
                    QMessageBox.information(self, "已下载全部模型", "已下载所有可用模型！")
                    return
                
                # 创建选择对话框
                dialog = QMessageBox(self)
                dialog.setWindowTitle("选择要下载的模型")
                dialog.setText("请选择要下载的模型：\n(下载过程中程序可能会暂时无响应)")
                
                # 添加模型选择按钮
                button_model_map = {}  # 使用字典存储按钮和模型的映射关系
                for name, info, _ in models_to_download:
                    button = dialog.addButton(f"{name} ({info})", QMessageBox.ButtonRole.ActionRole)
                    button_model_map[button] = name  # 将按钮对象和模型名称关联
                
                cancel_button = dialog.addButton("取消", QMessageBox.ButtonRole.RejectRole)
                
                # 显示对话框并获取用户选择
                dialog.exec()
                clicked_button = dialog.clickedButton()
                
                # 如果点击取消或关闭对话框，直接返回
                if clicked_button == cancel_button or clicked_button is None:
                    self.logger.info("用户取消了模型下载")
                    return
                
                # 从字典中直接获取点击按钮对应的模型名称
                model_name = button_model_map.get(clicked_button)
                
                # 如果没有找到对应的模型名称，返回
                if not model_name:
                    self.logger.warning("无法确定选择的模型名称")
                    return
                
                self.logger.info(f"用户选择下载模型: {model_name}")
            
            # 检查是否正在录音
            if self.is_recording:
                QMessageBox.warning(self, "操作不允许", "请先停止录音，然后再下载模型！")
                return
            
            # 禁用用户界面
            self.toggle_button.setEnabled(False)
            self.model_combo.setEnabled(False)
            self.download_button.setEnabled(False)
            self.status_label.setText(f"正在下载模型 {model_name}，请稍候...")
            
            # 模型下载是耗时操作，使用线程
            import threading
            download_thread = threading.Thread(target=self._download_model, args=(model_name,))
            download_thread.daemon = True
            download_thread.start()
            
        except Exception as e:
            self.logger.error(f"下载模型过程中出错: {e}")
            self.status_label.setText(f"下载模型失败: {str(e)}")
            self.toggle_button.setEnabled(True)
            self.model_combo.setEnabled(True)
            self.download_button.setEnabled(True)
    
    def _download_model(self, model_name):
        """在后台线程中下载模型"""
        try:
            self.logger.info(f"开始下载模型: {model_name}")
            
            # 确保model_name有效
            if not model_name:
                raise ValueError("无效的模型名称")
            
            # 构建下载命令
            import subprocess
            
            # 根据模型名称选择正确的仓库
            model_repo = f"Systran/faster-whisper-{model_name}"
            if model_name == "distil-large-v3":
                model_repo = "Systran/faster-distil-whisper-large-v3"
            elif model_name == "distil-small.en":
                model_repo = "Systran/faster-distil-whisper-small.en"
            elif model_name == "distil-medium.en":
                model_repo = "Systran/faster-distil-whisper-medium.en"
                
            cmd = [
                "huggingface-cli",
                "download",
                "--resume-download",
                model_repo,
                "--local-dir-use-symlinks",
                "False"
            ]
            
            self.logger.debug(f"执行命令: {' '.join(cmd)}")
            
            # 执行下载命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 在主线程中更新UI
            from PySide6.QtCore import QMetaObject, Qt, Q_ARG
            
            if result.returncode == 0:
                self.logger.info(f"模型 {model_name} 下载成功")
                # 使用主线程更新UI
                QTimer.singleShot(0, lambda: self.download_completed(True, model_name))
            else:
                self.logger.error(f"模型下载失败: {result.stderr}")
                # 使用主线程更新UI
                QTimer.singleShot(0, lambda: self.download_completed(False, result.stderr))
                
        except Exception as e:
            self.logger.error(f"下载模型过程中出错: {e}")
            # 在主线程中更新UI
            # 确保QTimer导入正确
            QTimer.singleShot(0, lambda: self.download_completed(False, str(e)))
    
    @Slot(bool, str)
    def download_completed(self, success, message):
        """下载完成后的UI更新（在主线程中调用）"""
        if success:
            self.status_label.setText(f"模型下载成功！")
            model_name = message  # message参数包含模型名称
            
            # 将刚下载的模型添加到已下载列表
            if model_name not in self.available_models:
                self.available_models.append(model_name)
            
            # 重新组织下拉框内容
            current_index = self.model_combo.currentIndex()
            self.model_combo.blockSignals(True)  # 阻止信号触发避免重复刷新
            
            # 保存当前选择的模型
            current_model = self.model_combo.currentData()
            
            # 清空并重新填充下拉框
            self.model_combo.clear()
            
            # 获取所有模型和大小信息
            found_models = []
            for name, path in [
                ("large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")),
                ("medium", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-medium")),
                ("small", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-small")),
                ("base", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-base")),
                ("tiny", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-tiny")),
                ("distil-large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-large-v3")),
                ("distil-small.en", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-small.en")),
                ("distil-medium.en", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-medium.en"))
            ]:
                if os.path.exists(path):
                    model_size = self._get_directory_size(path)
                    found_models.append((name, path, model_size))
            
            # 先添加所有已下载的模型
            for model_name, model_path, model_size in found_models:
                self.model_combo.addItem(f"{model_name} (已下载，{self._format_size(model_size)})", model_name)
            
            # 添加分隔线
            self.model_combo.addItem("---可下载模型---", None)
            
            # 添加未下载的模型
            available_models = [item[0] for item in found_models]
            for model in ["large-v3", "medium", "small", "base", "tiny", "distil-large-v3", "distil-small.en", "distil-medium.en"]:
                if model not in available_models:
                    self.model_combo.addItem(f"{model} (点击下载按钮下载)", model)
            
            # 添加删除模型选项
            self.model_combo.addItem("---删除模型---", None)
            for model_name, model_path, model_size in found_models:
                self.model_combo.addItem(f"删除 {model_name} ({self._format_size(model_size)})", f"del_{model_name}")
            
            # 尝试选择当前模型或新下载的模型
            select_model = current_model if current_model != model_name else model_name
            for i in range(self.model_combo.count()):
                if self.model_combo.itemData(i) == select_model:
                    self.model_combo.setCurrentIndex(i)
                    break
            
            self.model_combo.blockSignals(False)  # 恢复信号
            
            # 更新UI状态
            self.toggle_button.setEnabled(True)
            self.model_combo.setEnabled(True)
            self.download_button.setEnabled(True)
        else:
            # 下载失败
            self.status_label.setText(f"模型下载失败: {message}")
            self.toggle_button.setEnabled(True)
            self.model_combo.setEnabled(True)
            self.download_button.setEnabled(True)

    def update_idle_visualization(self):
        """在非录音状态下更新波形显示"""
        if not self.is_recording and hasattr(self, 'visualizer'):
            # 使用AudioRecorder的get_audio_level方法获取随机值
            from core.recorder import AudioRecorder
            recorder = getattr(self, '_temp_recorder', None)
            if recorder is None:
                recorder = AudioRecorder()
                self._temp_recorder = recorder
            
            level = recorder.get_audio_level()
            self.update_audio_level(level)

    def show_about_dialog(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec()

    def on_target_language_changed(self, index):
        """目标语言切换事件"""
        if index >= 0:
            lang_code = self.lang_combo.currentData()
            lang_name = self.lang_combo.currentText()
            self.target_language = lang_code
            self.logger.info(f"目标语言已切换为: {lang_name} (代码: {lang_code})")
            # 更新状态栏
            self.status_label.setText(f"目标语言: {lang_name}")

    class LogHandler(logging.Handler):
        def __init__(self, window):
            super().__init__()
            self.window = window
            
        def emit(self, record):
            msg = self.format(record)
            self.window.result_text.append(msg) 