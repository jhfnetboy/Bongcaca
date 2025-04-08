from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QComboBox, QMessageBox, QTextEdit, QHBoxLayout, QRadioButton, QButtonGroup, QFrame
from PySide6.QtCore import Qt, QTimer, QPointF, Signal, QObject, Slot
from PySide6.QtGui import QIcon, QPainter, QColor, QPolygonF, QPalette, QLinearGradient, QBrush, QPen, QFont
import numpy as np
import logging
import time
import os
from ui.logo import create_app_icon

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
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建设备选择标签
        device_label = QLabel("Select Input Device:")
        device_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(device_label)
        
        # 创建设备选择下拉框
        self.device_combo = QComboBox()
        self.device_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:disabled {
                background-color: #f0f0f0;
            }
        """)
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        layout.addWidget(self.device_combo)
        
        # 添加模型选择框
        model_label = QLabel("Select Model:")
        model_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:disabled {
                background-color: #f0f0f0;
            }
        """)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        layout.addWidget(self.model_combo)
        
        # 添加模型下载按钮
        self.download_button = QPushButton("Download Model")
        self.download_button.setStyleSheet("""
            QPushButton {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f0f0f0;
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
        layout.addWidget(self.download_button)
        
        # 添加模式选择框
        mode_frame = QFrame()
        mode_frame.setFrameShape(QFrame.StyledPanel)
        mode_frame.setStyleSheet("QFrame { background-color: #f0f0f0; border-radius: 4px; padding: 5px; }")
        mode_layout = QVBoxLayout(mode_frame)
        
        mode_label = QLabel("Transcription Mode:")
        mode_label.setAlignment(Qt.AlignCenter)
        mode_layout.addWidget(mode_label)
        
        mode_group = QButtonGroup(self)
        
        mode_buttons_layout = QHBoxLayout()
        self.batch_mode_radio = QRadioButton("Batch")
        self.batch_mode_radio.setChecked(True)  # 默认选中批量模式
        self.realtime_mode_radio = QRadioButton("Realtime")
        
        mode_group.addButton(self.batch_mode_radio)
        mode_group.addButton(self.realtime_mode_radio)
        
        mode_buttons_layout.addWidget(self.batch_mode_radio)
        mode_buttons_layout.addWidget(self.realtime_mode_radio)
        mode_layout.addLayout(mode_buttons_layout)
        
        # 连接模式切换信号
        self.batch_mode_radio.toggled.connect(self.on_mode_changed)
        
        layout.addWidget(mode_frame)
        
        # 创建录音按钮
        self.toggle_button = ToggleButton()
        self.toggle_button.clicked.connect(self.toggle_recording)
        self.toggle_button.setEnabled(False)  # 初始禁用
        layout.addWidget(self.toggle_button, alignment=Qt.AlignCenter)
        
        # 创建音频可视化器
        self.visualizer = AudioVisualizer()
        layout.addWidget(self.visualizer)
        
        # 创建状态标签
        self.status_label = QLabel("初始化设备中...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 创建文本显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 100px;
            }
        """)
        layout.addWidget(self.result_text)
        
        # 设置日志处理器
        self.logger.addHandler(self.LogHandler(self))
        
        # 设置窗口大小
        self.setFixedSize(400, 600)
        
        # 初始化设备列表
        self.init_device_list()
        
        # 初始化模型列表
        self.init_model_list()
        
        # 创建定时器用于在非录音状态下更新波形
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.update_idle_visualization)
        self.idle_timer.start(100)  # 100毫秒更新一次
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.device_initialized:  # 仅当设备初始化完成时才允许空格控制
                self.toggle_recording_signal.emit()  # 发射信号,不直接调用toggle_recording
            else:
                self.status_label.setText("初始化设备中,请稍候...")
        else:
            super().keyPressEvent(event)
            
    def toggle_recording(self):
        """切换录音状态 - 只发射信号,不改变状态"""
        if not self.device_initialized:
            self.logger.warning("设备未初始化,禁止录音")
            self.status_label.setText("初始化设备中,请稍候...")
            return
            
        self.logger.debug(f"切换录音状态,当前状态: {self.is_recording}")
        # 发射信号,让main.py处理实际逻辑
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
        """更新结果文本"""
        self.result_text.append(text)
        self.logger.info(f"转写结果: {text}")
        
        # 将文本输出到当前光标位置
        try:
            from platform_specific.input import TextInput
            text_input = TextInput()
            
            # 获取当前窗口
            current_window = text_input.get_focused_window()
            self.logger.debug(f"当前焦点窗口: {current_window}")
            
            # 尝试所有可用方法输入文本
            result = text_input.insert_text(text)
            if result:
                self.logger.debug("文本插入成功")
            else:
                self.logger.error("无法插入文本到当前窗口")
                
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
            
            # 检查模型目录
            model_paths = [
                ("large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")),
                ("medium", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-medium")),
                ("small", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-small")),
                ("base", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-base")),
                ("distil-large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-large-v3"))
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
                    found_models.append((model_name, model_path))
                    self.available_models.append(model_name)
                    self.model_combo.addItem(f"{model_name} (已下载)", model_name)
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
                available_to_download = ["large-v3", "medium", "small", "base", "distil-large-v3"]
                for model in available_to_download:
                    if model not in self.available_models:
                        self.model_combo.addItem(f"{model} (点击下载按钮下载)", model)
                
                # 设置第一个模型为默认选择
                self.model_combo.setCurrentIndex(0)
                
                self.result_text.append(f"已找到 {len(found_models)} 个已下载模型，默认使用: {found_models[0][0]}")
            
            self.logger.info(f"模型列表初始化完成，找到 {len(found_models)} 个已下载模型")
        except Exception as e:
            self.logger.error(f"初始化模型列表失败: {e}")
            self.status_label.setText(f"初始化模型列表失败: {str(e)}")
    
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
                self.logger.info(f"已选择模型: {model_name}")
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
                    ("base", "74MB - 较低质量", "https://huggingface.co/Systran/faster-whisper-base"),
                    ("small", "244MB - 平衡质量", "https://huggingface.co/Systran/faster-whisper-small"),
                    ("medium", "769MB - 高质量", "https://huggingface.co/Systran/faster-whisper-medium"),
                    ("large-v3", "2.9GB - 最高质量", "https://huggingface.co/Systran/faster-whisper-large-v3"),
                    ("distil-large-v3", "2.3GB - 较高质量", "https://huggingface.co/Systran/faster-distil-whisper-large-v3")
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
                
                for idx, (name, info, _) in enumerate(models_to_download):
                    dialog.addButton(f"{name} ({info})", QMessageBox.ButtonRole.ActionRole)
                
                dialog.addButton("取消", QMessageBox.ButtonRole.RejectRole)
                
                # 显示对话框并获取用户选择
                result = dialog.exec()
                
                # 修复：如果用户点击取消按钮，直接返回
                cancel_idx = len(models_to_download)  # 取消按钮的索引
                if result == cancel_idx or result < 0:
                    self.logger.info("用户取消了模型下载")
                    return
                
                # 修复：确保selected_index在有效范围内
                if result < len(models_to_download):
                    model_name = models_to_download[result][0]
                else:
                    self.logger.warning(f"无效的选择索引: {result}, 可用选项数: {len(models_to_download)}")
                    return
            
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
            
            # 构建下载命令
            import subprocess
            
            model_repo = f"Systran/faster-whisper-{model_name}"
            if model_name == "distil-large-v3":
                model_repo = "Systran/faster-distil-whisper-large-v3"
                
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
            
            # 先添加所有已下载的模型
            for model in ["large-v3", "medium", "small", "base", "distil-large-v3"]:
                if model in self.available_models:
                    self.model_combo.addItem(f"{model} (已下载)", model)
            
            # 添加分隔线
            self.model_combo.addItem("---可下载模型---", None)
            
            # 添加未下载的模型
            for model in ["large-v3", "medium", "small", "base", "distil-large-v3"]:
                if model not in self.available_models:
                    self.model_combo.addItem(f"{model} (点击下载按钮下载)", model)
            
            # 尝试恢复之前的选择
            if current_model:
                for i in range(self.model_combo.count()):
                    if self.model_combo.itemData(i) == current_model:
                        self.model_combo.setCurrentIndex(i)
                        break
            else:
                # 如果之前没有选择，选择第一个模型
                self.model_combo.setCurrentIndex(0)
                
            self.model_combo.blockSignals(False)  # 恢复信号
            
            # 显示成功消息
            QMessageBox.information(self, "下载成功", f"模型 {model_name} 下载成功！\n应用将在重启后使用新模型。")
            
        else:
            self.status_label.setText(f"模型下载失败: {message}")
            QMessageBox.warning(self, "下载失败", f"模型下载失败: {message}")
        
        # 重新启用UI
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

    class LogHandler(logging.Handler):
        def __init__(self, window):
            super().__init__()
            self.window = window
            
        def emit(self, record):
            msg = self.format(record)
            self.window.result_text.append(msg) 