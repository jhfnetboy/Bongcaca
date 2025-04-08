import sys
import os
import signal
from PySide6.QtWidgets import QApplication, QMessageBox, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QKeyEvent
from ui.floating_window import FloatingWindow
from core.engine import WhisperEngine
from core.recorder import AudioRecorder
from platform_specific.base import PlatformIntegration
from utils.config import Config
from utils.logging import setup_logging
from utils.model_manager import ModelManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("语音输入工具")
        self.setGeometry(100, 100, 600, 400)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 添加状态标签
        self.status_label = QLabel("正在初始化...")
        layout.addWidget(self.status_label)
        
        # 添加录音控制按钮
        self.record_button = QPushButton("▶️ 开始录音")
        self.record_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        # 添加结果显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        
        # 初始化应用组件
        self.config = Config()
        self.model_manager = ModelManager(self.config)
        self.engine = None
        self.recorder = None
        self.is_recording = False
        
        # 检查模型
        self.check_model()
        
    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if event.key() == Qt.Key_Space:
            self.toggle_recording()
            
    def toggle_recording(self):
        """切换录音状态"""
        if not self.engine or not self.recorder:
            return
            
        if not self.is_recording:
            # 开始录音
            self.is_recording = True
            self.record_button.setText("⏹ 停止录音")
            self.record_button.setStyleSheet("background-color: #f44336; color: white; font-size: 16px; padding: 10px;")
            self.status_label.setText("正在录音...")
            
            # 开始录音
            self.audio_file = self.recorder.record(5)  # 录制5秒
            
            # 停止录音
            self.is_recording = False
            self.record_button.setText("▶️ 开始录音")
            self.record_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")
            self.status_label.setText("正在识别...")
            
            # 识别语音
            segments, info = self.engine.transcribe(self.audio_file, word_timestamps=True)
            
            # 显示识别结果
            result_text = f"检测到的语言: {info.language} (概率: {info.language_probability})\n\n"
            for segment in segments:
                result_text += f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}\n"
                if 'words' in segment:
                    for word in segment['words']:
                        result_text += f"  [{word['start']:.2f}s -> {word['end']:.2f}s] {word['word']}\n"
                result_text += "\n"
                
            self.result_text.setText(result_text)
            self.status_label.setText("识别完成")
            
    def check_model(self):
        """检查模型是否存在"""
        # 检查默认缓存路径
        default_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478")
        if os.path.exists(default_path):
            self.status_label.setText("找到已下载的模型，正在加载...")
            self.engine = WhisperEngine(default_path)
            self.recorder = AudioRecorder()
            self.status_label.setText("模型加载完成，可以开始录音")
            self.record_button.setEnabled(True)
            return
            
        self.status_label.setText("未找到语音模型，请先下载模型")
        self.record_button.setEnabled(False)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.recorder:
            self.recorder.stop()
        event.accept()

def signal_handler(signum, frame):
    """处理 Ctrl+C 信号"""
    print("\n正在退出程序...")
    if QApplication.instance():
        QApplication.instance().quit()
    sys.exit(0)

def main():
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    main() 