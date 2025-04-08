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
    """主程序入口"""
    # 应用程序初始化
    app = QApplication(sys.argv)
    
    # 初始化日志
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Voice Typer")
    
    # 创建配置
    config = Config()
    
    # 初始化引擎和录音器
    engine = WhisperEngine(config)
    recorder = AudioRecorder()
    
    # 创建窗口
    window = FloatingWindow()
    window.show()
    
    # 全局变量
    is_recording = False
    recording_thread = None
    
    # 录音循环
    def recording_loop():
        nonlocal is_recording
        logger.debug("Recording loop started")
        
        try:
            # 检查设备
            if recorder.input_device_index is None:
                logger.error("No input device selected")
                window.status_label.setText("Error: No input device selected")
                return
                
            # 开始录音
            recorder.start_recording()
            logger.debug(f"Audio recorder started with device: {recorder.input_device_index}")
            window.status_label.setText("Recording...")
            
            # 设置5分钟超时
            start_time = time.time()
            timeout = 5 * 60  # 5分钟
            last_transcribe_time = 0  # 上次转写时间
            
            # 创建临时文件用于实时转写
            temp_file = "temp_recording.wav"
            transcription_interval = 1.0  # 每1秒转写一次
            
            # 连续语音检测变量
            continuous_audio_count = 0
            min_audio_level_threshold = 5  # 最小音频电平阈值
            continuous_audio_threshold = 3  # 连续检测到声音的次数阈值
            
            while is_recording and (time.time() - start_time) < timeout:
                try:
                    # 获取音频电平
                    level = recorder.get_audio_level()
                    window.update_audio_level(level)
                    
                    # 检测连续语音
                    if level > min_audio_level_threshold:
                        continuous_audio_count += 1
                        logger.debug(f"Audio level: {level}, continuous count: {continuous_audio_count}")
                    else:
                        continuous_audio_count = max(0, continuous_audio_count - 1)  # 逐渐减少计数
                    
                    # 判断是否需要进行转写
                    current_time = time.time()
                    should_transcribe = False
                    
                    # 固定间隔转写
                    if current_time - last_transcribe_time >= transcription_interval:
                        should_transcribe = True
                        
                    # 连续语音触发转写
                    if continuous_audio_count >= continuous_audio_threshold:
                        should_transcribe = True
                        continuous_audio_count = 0  # 重置计数
                        
                    if should_transcribe:
                        last_transcribe_time = current_time
                        
                        # 保存当前录音片段
                        if recorder.save_recording(temp_file):
                            # 转写当前片段
                            window.status_label.setText("转写中...")
                            try:
                                logger.debug("Starting transcription")
                                text = engine.transcribe(temp_file)
                                if text.strip() and text != "请说话...":
                                    logger.debug(f"Transcription result: {text}")
                                    window.update_result(text)
                                    window.status_label.setText("Recording...")
                            except Exception as e:
                                logger.error(f"Transcription failed: {e}")
                        else:
                            logger.warning("Failed to save recording for transcription")
                    
                    # 等待一小段时间
                    time.sleep(0.05)  # 保持波形流畅
                    
                except Exception as e:
                    logger.error(f"Error in recording loop: {e}")
                    window.status_label.setText(f"Error: {str(e)}")
                    break
                    
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            window.status_label.setText(f"Error: {str(e)}")
        finally:
            # 停止录音
            recorder.stop()
            logger.debug("Recording loop stopped")
            window.status_label.setText("Ready")
            
    # 连接录音按钮
    def on_toggle_recording():
        nonlocal is_recording, recording_thread
        
        logger.debug(f"Toggle recording button clicked, current state: {window.toggle_button.is_recording}")
        
        # 录音开始
        if not is_recording:
            # 检查设备
            if recorder.input_device_index is None:
                logger.error("No input device selected")
                window.status_label.setText("请先选择输入设备")
                return
                
            logger.debug("Starting recording")
            # 更新UI状态
            window.toggle_button.set_recording(True)
            window.status_label.setText("Recording...")
            
            # 启动录音线程
            is_recording = True
            recording_thread = threading.Thread(target=recording_loop)
            recording_thread.daemon = True
            recording_thread.start()
            
        # 录音停止
        else:
            logger.debug("Stopping recording")
            # 更新UI状态
            window.toggle_button.set_recording(False)
            window.status_label.setText("停止录音中...")
            
            # 停止录音线程
            is_recording = False
            if recording_thread and recording_thread.is_alive():
                recording_thread.join(timeout=1.0)
                
            # 确保录音器停止
            recorder.stop()
            window.status_label.setText("就绪")
            
    # 连接设备变更信号
    def on_device_changed(device_id):
        logger.info(f"Setting input device to: {device_id}")
        recorder.set_input_device(device_id)
            
    # 连接信号
    window.toggle_recording_signal.connect(on_toggle_recording)
    window.device_changed.connect(on_device_changed)
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 