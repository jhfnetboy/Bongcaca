from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

class FloatingWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 添加标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        # 添加按钮
        self.record_button = QPushButton("开始录音")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        self.setLayout(layout)
        
    def toggle_recording(self):
        """切换录音状态"""
        if self.record_button.text() == "开始录音":
            self.record_button.setText("停止录音")
            self.status_label.setText("正在录音...")
        else:
            self.record_button.setText("开始录音")
            self.status_label.setText("准备就绪")
            
    def show_recording(self):
        """显示录音状态"""
        self.status_label.setText("正在录音...")
        
    def show_processing(self):
        """显示处理状态"""
        self.status_label.setText("正在处理...")
        
    def show_result(self, text):
        """显示识别结果"""
        self.status_label.setText(f"识别结果: {text}")
        
    def update_audio_level(self, level):
        """更新音量显示"""
        self.status_label.setText(f"音量: {level}%") 