import sys
import os
import signal
from PySide6.QtWidgets import QApplication, QMessageBox, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
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
        self.setGeometry(100, 100, 400, 300)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 添加状态标签
        self.status_label = QLabel("正在初始化...")
        layout.addWidget(self.status_label)
        
        # 添加按钮
        self.start_button = QPushButton("开始录音")
        self.start_button.clicked.connect(self.start_recording)
        layout.addWidget(self.start_button)
        
        # 初始化应用组件
        self.config = Config()
        self.model_manager = ModelManager(self.config)
        self.engine = None
        self.recorder = None
        
        # 检查模型
        self.check_model()
        
    def check_model(self):
        """检查模型是否存在"""
        # 检查默认缓存路径
        default_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478")
        if os.path.exists(default_path):
            self.status_label.setText("找到已下载的模型，正在加载...")
            self.engine = WhisperEngine(default_path)
            self.recorder = AudioRecorder()
            self.status_label.setText("模型加载完成，可以开始录音")
            self.start_button.setEnabled(True)
            return
            
        # 如果默认路径不存在，尝试下载
        self.status_label.setText("未找到语音模型，正在下载...")
        recommended_model = self.model_manager.get_recommended_model()
        model_path = self.model_manager.download_model(recommended_model)
            
        if model_path:
            self.engine = WhisperEngine(model_path)
            self.recorder = AudioRecorder()
            self.status_label.setText("模型加载完成，可以开始录音")
            self.start_button.setEnabled(True)
        else:
            self.status_label.setText("模型加载失败，请检查网络连接")
            self.start_button.setEnabled(False)
            
    def start_recording(self):
        """开始录音"""
        if not self.engine or not self.recorder:
            return
            
        self.status_label.setText("正在录音...")
        self.start_button.setEnabled(False)
        
        # 录制5秒
        audio_file = self.recorder.record(5)
        
        self.status_label.setText("正在识别...")
        segments, info = self.engine.transcribe(audio_file, word_timestamps=True)
        
        # 显示识别结果
        result_text = f"检测到的语言: {info.language} (概率: {info.language_probability})\n"
        for segment in segments:
            result_text += f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}\n"
            if 'words' in segment:
                for word in segment['words']:
                    result_text += f"  [{word['start']:.2f}s -> {word['end']:.2f}s] {word['word']}\n"
                    
        self.status_label.setText(result_text)
        self.start_button.setEnabled(True)
        
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