from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QComboBox, QMessageBox, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

class FloatingWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建标题栏
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加标题
        title_label = QLabel("Voice Typer")
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)
        
        # 添加最小化按钮
        minimize_btn = QPushButton("_")
        minimize_btn.setFixedSize(20, 20)
        minimize_btn.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_btn)
        
        # 添加关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.close)
        title_layout.addWidget(close_btn)
        
        layout.addWidget(title_bar)
        
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
        
        # 创建状态标签
        self.status_label = QLabel("Select an input device")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # 创建开始/停止按钮
        self.toggle_button = QPushButton("Start Recording")
        self.toggle_button.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_recording)
        self.toggle_button.setEnabled(False)  # 初始禁用
        layout.addWidget(self.toggle_button)
        
        # 创建结果显示区域
        self.result_text = QLabel("")
        self.result_text.setWordWrap(True)
        self.result_text.setAlignment(Qt.AlignLeft)
        self.result_text.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 100px;
            }
        """)
        layout.addWidget(self.result_text)
        
        # 设置窗口大小
        self.setFixedSize(400, 300)
        
        # 初始化设备列表
        self.init_device_list()
        
    def init_device_list(self):
        """初始化音频设备列表"""
        import pyaudio
        try:
            p = pyaudio.PyAudio()
            
            # 清空现有设备列表
            self.device_combo.clear()
            
            # 获取所有音频设备
            info = p.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            
            has_input_device = False
            for i in range(num_devices):
                device_info = p.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels') > 0:
                    device_name = device_info.get('name')
                    self.device_combo.addItem(f"{device_name} (Device {i})", i)
                    has_input_device = True
                    
            p.terminate()
            
            if not has_input_device:
                self.device_combo.addItem("No input devices found")
                self.device_combo.setEnabled(False)
                self.status_label.setText("No input devices found. Please connect a microphone.")
                self.toggle_button.setEnabled(False)
                QMessageBox.warning(self, "No Input Device", 
                    "No microphone was found. Please connect a microphone and restart the application.")
        except Exception as e:
            self.device_combo.addItem("Error loading devices")
            self.device_combo.setEnabled(False)
            self.status_label.setText("Error loading audio devices")
            self.toggle_button.setEnabled(False)
            QMessageBox.critical(self, "Error", 
                f"Failed to load audio devices: {str(e)}\nPlease check your audio settings.")
            
    def on_device_changed(self, index):
        """设备选择改变时的处理"""
        if self.device_combo.currentData() is not None:
            self.status_label.setText("Ready to record")
            self.toggle_button.setEnabled(True)
        else:
            self.status_label.setText("No input devices found")
            self.toggle_button.setEnabled(False)
            
    def toggle_recording(self):
        if self.toggle_button.text() == "Start Recording":
            self.toggle_button.setText("Stop Recording")
            self.status_label.setText("Recording...")
        else:
            self.toggle_button.setText("Start Recording")
            self.status_label.setText("Ready")
            
    def update_result(self, text):
        """更新识别结果"""
        self.result_text.setText(text)
        
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
        
    def show_processing(self):
        """显示处理状态"""
        self.status_label.setText("Processing...")
        
    def show_result(self, text):
        """显示识别结果"""
        self.status_label.setText(f"Result: {text}")
        
    def update_audio_level(self, level):
        """更新音量显示"""
        self.status_label.setText(f"Volume: {level}%") 