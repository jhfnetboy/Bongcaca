import sys
import os
import threading
import time
from PySide6.QtWidgets import QApplication
from ui.floating_window import FloatingWindow
from core.recorder import AudioRecorder
from core.engine import WhisperEngine
from utils.config import Config
from utils.logging import setup_logging
from platform_specific.input import TextInput
import logging

def main():
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 初始化配置
    config = Config()
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建录音器
    recorder = AudioRecorder()
    
    # 创建语音识别引擎
    engine = WhisperEngine(config)
    
    # 创建文本输入器
    text_input = TextInput()
    
    # 创建浮动窗口
    window = FloatingWindow()
    
    # 连接设备选择
    def on_device_changed(index):
        device_index = window.device_combo.currentData()
        if device_index is not None:
            recorder.set_input_device(device_index)
            window.toggle_button.setEnabled(True)
        else:
            window.toggle_button.setEnabled(False)
            
    window.device_combo.currentIndexChanged.connect(on_device_changed)
    
    # 录音线程
    recording_thread = None
    is_recording = False
    
    def recording_loop():
        nonlocal is_recording
        while is_recording:
            try:
                # 录制5秒音频
                audio_file = recorder.record(5)
                
                # 识别语音
                result = engine.transcribe(audio_file)
                
                # 更新界面
                window.update_result(result)
                
                # 如果光标在文本输入区域，则输入文本
                if result.strip():
                    # 获取当前焦点窗口
                    focused_window = text_input.get_focused_window()
                    if focused_window and focused_window != "Unknown":
                        text_input.input_text(result)
                        
            except Exception as e:
                logger.error(f"Recording error: {e}")
                window.status_label.setText(f"Error: {str(e)}")
                break
                
    # 连接录音按钮
    def on_toggle_recording():
        nonlocal is_recording, recording_thread
        
        if window.toggle_button.text() == "Start Recording":
            if recorder.input_device_index is None:
                window.status_label.setText("Please select an input device first")
                return
                
            window.toggle_button.setText("Stop Recording")
            window.status_label.setText("Recording...")
            
            # 开始录音线程
            is_recording = True
            recording_thread = threading.Thread(target=recording_loop)
            recording_thread.start()
            
        else:
            window.toggle_button.setText("Start Recording")
            window.status_label.setText("Ready")
            
            # 停止录音线程
            is_recording = False
            if recording_thread:
                recording_thread.join()
            recorder.stop()
            
    window.toggle_button.clicked.connect(on_toggle_recording)
    
    # 显示窗口
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 