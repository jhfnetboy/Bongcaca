import argparse
import logging
import os
import sys
import threading
import time
import platform
import glob
from datetime import datetime, timedelta
from pathlib import Path
import uuid
import tempfile

from utils.logging import setup_logging
from utils.config import Config
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu, QStyle
from PySide6.QtCore import Qt, QObject, Signal, Slot, QThread, QTimer
from PySide6.QtGui import QIcon, QAction

from core.engine import WhisperEngine, TranscriptionEngine
from core.recorder import AudioRecorder
from ui.floating_window import FloatingWindow, WindowSignals

logger = logging.getLogger("voice_typer")

# 设置配置和日志
config = Config()
setup_logging(config)

def cleanup_old_recordings(keep_recent=3):
    """清理旧的录音文件，只保留最近的几个文件"""
    temp_dir = os.path.join(os.path.expanduser("~"), ".voice_typer", "temp")
    if not os.path.exists(temp_dir):
        return
        
    logger.info(f"清理录音文件，仅保留最近{keep_recent}个文件...")
    
    # 查找所有录音文件
    recording_files = []
    for file_path in glob.glob(os.path.join(temp_dir, "recording_*.wav")):
        try:
            # 从文件名中获取时间戳
            filename = os.path.basename(file_path)
            if not filename.startswith("recording_"):
                continue
                
            timestamp_str = filename.replace("recording_", "").replace(".wav", "")
            if not timestamp_str.isdigit():
                continue
                
            timestamp = int(timestamp_str)
            recording_files.append((timestamp, file_path))
        except Exception as e:
            logger.error(f"处理录音文件时出错: {e}")
    
    # 按时间戳排序（最新的在前面）
    recording_files.sort(reverse=True)
    
    # 保留最近的几个文件，删除其余的
    count = 0
    for i, (timestamp, file_path) in enumerate(recording_files):
        if i >= keep_recent:
            try:
                os.remove(file_path)
                count += 1
                logger.debug(f"已删除旧录音文件: {file_path}")
            except Exception as e:
                logger.error(f"删除录音文件时出错: {e}")
    
    if count > 0:
        logger.info(f"已清理 {count} 个旧录音文件，保留了最近的 {min(keep_recent, len(recording_files))} 个")
    else:
        logger.info(f"没有需要清理的旧录音文件，当前共有 {len(recording_files)} 个")

def parse_args():
    parser = argparse.ArgumentParser(description='Voice Typer')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--test-input', action='store_true', help='Test text input functionality')
    return parser.parse_args()

def test_text_input():
    """测试文本输入功能"""
    logger.info("开始文本输入测试...")
    from platform_specific.input import TextInput
    
    text_input = TextInput()
    test_text = "macOS啊啊MacOS啊啊啊啊啊啊啊啊啊MacOS"
    
    # 获取当前焦点窗口
    window = text_input.get_focused_window()
    logger.info(f"当前焦点窗口: {window}")
    
    # 等待用户准备
    logger.info("请在3秒内将光标放在您希望输入文本的位置...")
    for i in range(3, 0, -1):
        logger.info(f"{i}...")
        time.sleep(1)
    
    # 测试输入文本
    logger.info(f"尝试输入文本: {test_text}")
    
    # 方法1: 直接使用input_text
    success = text_input.input_text(test_text)
    logger.info(f"方法1 (input_text) 结果: {'成功' if success else '失败'}")
    
    time.sleep(1)
    
    # 方法2: 使用insert_text
    success = text_input.insert_text(test_text)
    logger.info(f"方法2 (insert_text) 结果: {'成功' if success else '失败'}")
    
    logger.info("文本输入测试完成")

def play_notification_sound():
    """播放提示音以提示转写完成"""
    try:
        # 使用PyAudio播放简短提示音
        try:
            import pyaudio
            import numpy as np
            
            pa = pyaudio.PyAudio()
            beep_stream = pa.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=16000,
                output=True
            )
            
            # 生成提示音（440Hz和880Hz，各200ms）
            duration = 0.2  # 秒
            volume = 0.5   # 音量（0.0-1.0）
            fs = 16000     # 采样率
            
            # 第一个音（440Hz）
            samples1 = (np.sin(2*np.pi*np.arange(fs*duration)*440/fs)).astype(np.float32)
            samples1 = samples1 * volume
            
            # 短暂停顿
            pause = np.zeros(int(fs*0.1), dtype=np.float32)
            
            # 第二个音（880Hz）
            samples2 = (np.sin(2*np.pi*np.arange(fs*duration)*880/fs)).astype(np.float32)
            samples2 = samples2 * volume
            
            # 合并两个提示音
            samples = np.concatenate([samples1, pause, samples2])
            
            # 播放提示音
            beep_stream.write(samples.tobytes())
            
            # 关闭流
            beep_stream.stop_stream()
            beep_stream.close()
            pa.terminate()
            
            logger.debug("播放转写完成提示音")
            
        except Exception as e:
            logger.warning(f"播放提示音失败: {e}")
    except Exception as e:
        logger.error(f"播放通知声音过程中出错: {e}")

def run_recording_loop(window, engine, recorder, language="auto", max_duration=300):
    """录音循环，处理音频录制和转写"""
    logger.debug(f"开始录音循环，语言设置为: {language}")
    
    try:
        # 根据选择的模式启动录音
        if window.transcription_mode == "realtime":
            # 实时模式 - 使用回调函数
            logger.debug("使用实时转写模式")
            last_transcription = ""  # 保存上次的转写结果
            last_update_time = time.time()  # 上次更新UI的时间
            
            def realtime_callback(audio_chunk, level):
                nonlocal last_transcription, last_update_time
                # 添加音频块到引擎缓冲区
                engine.add_audio_chunk(audio_chunk)
                
                # 更新UI音频电平
                window.update_audio_level(level)
                
                # 获取实时转写结果
                current_time = time.time()
                # 确保至少每1秒尝试一次转写，避免过于频繁
                if current_time - last_update_time >= 1.0:
                    # 获取当前选择的语言
                    result = engine.get_realtime_transcription(language=language)
                    if result and result != last_transcription:
                        window.update_result(result)
                        window.update_status(f"实时转写中...")
                        last_transcription = result
                        last_update_time = current_time
                        # 清除过旧的缓冲区数据，只保留最近的数据，减轻处理负担
                        if len(engine.buffer) > 20:  # 保留约10秒的音频
                            engine.buffer = engine.buffer[-20:]
                            engine.buffer_size = sum(len(chunk) for chunk in engine.buffer)
                            logger.debug(f"裁剪音频缓冲区至 {engine.buffer_size} 字节")
            
            logger.debug("启动音频录制器(实时模式)")
            recorder.start_recording(
                device_index=recorder.device_index, 
                realtime_mode=True, 
                realtime_callback=realtime_callback
            )
        else:
            # 批量模式 - 标准录音
            logger.debug("使用批量转写模式")
            logger.debug("启动音频录制器(批量模式)")
            recorder.start_recording(device_index=recorder.device_index)
        
        start_time = time.time()
        window.update_status("正在录音...")
        
        # 录音循环
        while window.is_recording and (time.time() - start_time) < max_duration:
            try:
                # 更新音频电平 (仅批量模式需要，实时模式在回调中处理)
                if window.transcription_mode == "batch":
                    level = recorder.get_audio_level()
                    window.update_audio_level(level)
                    
                    # 每0.5秒记录一次音频电平(从原来的5秒改为0.5秒)
                    current_time = time.time()
                    if current_time - start_time - int(current_time - start_time) < 0.05:
                        logger.debug(f"当前音频电平: {level:.2f}")
                
                # 短暂休眠
                time.sleep(0.05)
            except Exception as e:
                logger.error(f"录音循环中发生错误: {e}")
                window.update_status(f"录音错误: {str(e)}")
                break
        
        # 检查是否因超时而停止
        if (time.time() - start_time) >= max_duration:
            logger.info("录音达到最大时间限制，自动停止")
            window.update_status("录音时间达到限制，已停止")
            window.toggle_recording()  # 更新UI状态
            return
        
        # 停止录音并获取文件
        logger.debug("停止音频录制器")
        audio_file = recorder.stop()
        
        # 在批量模式下进行文件转写
        if window.transcription_mode == "batch" and audio_file and os.path.exists(audio_file):
            # 记录录音文件信息
            file_size = os.path.getsize(audio_file)
            file_size_mb = file_size / (1024 * 1024)
            recording_duration = time.time() - start_time
            
            logger.info(f"录音文件保存到: {audio_file} (大小: {file_size_mb:.2f}MB, 时长: {recording_duration:.2f}秒)")
            window.update_status("转写中...")
            
            # 开始计时转写过程
            transcribe_start_time = time.time()
            
            # 转写音频
            try:
                logger.debug(f"开始转写音频文件: {audio_file}，语言设置为: {language}")
                result = engine.transcribe(audio_file, language)
                
                # 计算转写时间
                transcribe_time = time.time() - transcribe_start_time
                
                if not result or not result.strip():
                    logger.warning("转写结果为空")
                    window.update_status("转写完成，但结果为空")
                    return
                
                # 计算字符数和中文字数
                char_count = len(result)
                chinese_char_count = sum(1 for char in result if '\u4e00' <= char <= '\u9fff')
                
                # 记录详细统计信息
                stats_msg = (
                    f"录音统计: 文件大小={file_size_mb:.2f}MB, 录音时长={recording_duration:.2f}秒, "
                    f"转写时间={transcribe_time:.2f}秒, 字符数={char_count}, 中文字数={chinese_char_count}, "
                    f"使用模型={engine.whisper_engine.model_name}, 语言={language}"
                )
                logger.info(stats_msg)
                window.result_text.append(f"\n--- {stats_msg} ---\n")
                
                logger.info(f"转写结果: {result}")
                window.update_result(result)
                window.update_status("转写完成")
                
                # 转写完成后播放提示音
                play_notification_sound()
                
            except Exception as e:
                logger.error(f"转写音频失败: {e}")
                window.update_status(f"转写失败: {str(e)}")
    except Exception as e:
        logger.error(f"录音过程中发生错误: {e}")
        window.update_status(f"录音失败: {str(e)}")
    finally:
        # 确保录音已停止
        try:
            if hasattr(recorder, 'stop') and recorder.is_recording:
                recorder.stop()
        except Exception as e:
            logger.error(f"停止录音时发生错误: {e}")

def on_toggle_recording(window, engine, recorder, device_id, language):
    """处理录音按钮点击事件"""
    # 如果当前正在录音，则停止录音
    if window.is_recording:
        logger.debug("停止录音")
        window.update_status("正在停止录音...")
        window.is_recording = False
        window.update_recording_state(False)
        
        # 如果有正在运行的录音线程，等待其结束
        if hasattr(window, "_recording_thread") and window._recording_thread and window._recording_thread.is_alive():
            # 这里不需要做什么，线程会自行检测录音状态并退出
            pass
            
        return
        
    # 开始新的录音
    if device_id is None:
        logger.error("没有选择输入设备")
        window.update_status("错误: 没有选择输入设备")
        return
        
    logger.debug(f"开始录音，使用设备ID: {device_id}")
    
    # 确保模型已加载
    try:
        # 先检查模型是否已加载
        if not engine.whisper_engine.initialized:
            logger.info("模型尚未加载，正在加载...")
            window.update_status("正在加载模型...")
            
        engine.whisper_engine.ensure_model_loaded()
        logger.info(f"使用模型: {engine.whisper_engine.model_name}")
    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        window.update_status(f"加载模型失败: {str(e)}")
        return
        
    # 显式设置录音设备
    try:
        # 确保设备初始化
        if recorder.device_index != device_id:
            logger.info(f"设置录音设备: {device_id}")
            
        recorder.set_device(device_id)
        logger.info(f"已设置录音设备: {device_id}")
    except Exception as e:
        logger.error(f"设置录音设备失败: {e}")
        window.update_status(f"设置录音设备失败: {str(e)}")
        return
        
    # 设置录音状态
    window.is_recording = True
    window.update_recording_state(True)
    window.update_status("录音中...")
    
    # 使用线程进行录音和转写
    window._recording_thread = threading.Thread(
        target=run_recording_loop, 
        args=(window, engine, recorder, language)
    )
    window._recording_thread.daemon = True
    window._recording_thread.start()
    
    # 确保线程成功启动
    time.sleep(0.1)
    if not window._recording_thread.is_alive():
        logger.error("录音线程启动失败")
        window.is_recording = False
        window.update_recording_state(False)
        window.update_status("录音线程启动失败")
        return
        
    logger.info("录音线程启动成功")

def on_model_change(window, engine, model_name):
    """处理模型变更事件"""
    # 检查是否正在录音
    if window.is_recording:
        logger.warning("无法在录音过程中更改模型")
        window.update_status("请先停止录音，然后再更改模型")
        return
        
    logger.info(f"切换到模型: {model_name}")
    window.update_status(f"正在切换到模型: {model_name}...")
    
    # 重置引擎状态
    engine.whisper_engine.model = None
    engine.whisper_engine.initialized = False
    
    # 强制设置模型名称
    engine.whisper_engine.settings = {
        "model_name": model_name,
        "device": "cpu",
        "compute_type": "int8",
        "beam_size": 5,
        "threads": min(os.cpu_count(), 8)  # 使用多线程
    }
    
    try:
        # 显示正在加载的提示
        window.update_status(f"正在加载模型 {model_name}...")
        logger.info(f"开始加载模型: {model_name}")
        
        # 重新加载模型
        engine.whisper_engine.ensure_model_loaded()
        
        window.update_status(f"已切换到模型: {model_name}")
        logger.info(f"模型切换成功: {model_name}")
    except Exception as e:
        logger.error(f"切换模型失败: {e}")
        window.update_status(f"切换模型失败: {str(e)}")

class VoiceTyper(QObject):
    def __init__(self):
        super().__init__()
        self.version = "0.23.41"
        logger.info(f"启动 Voice Typer v{self.version}")
        
        # 初始化临时目录
        self.temp_dir = os.path.join(tempfile.gettempdir(), "voice_typer")
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info(f"使用临时目录: {self.temp_dir}")
        
        # 初始化音频录制器
        self.recorder = AudioRecorder(self.temp_dir)
        self.input_devices = self.recorder.get_input_devices()
        logger.info(f"找到 {len(self.input_devices)} 个输入设备")
        
        # 初始化转录引擎
        self.engine = TranscriptionEngine()
        
        # 初始化UI
        self.init_ui()
        
        # 录音相关变量
        self.recording = False
        self.recording_thread = None
        self.audio_file = None
        self.max_recording_time = 5 * 60  # 5分钟的最大录音时间

    def init_ui(self):
        """初始化用户界面"""
        logger.info("初始化用户界面")
        
        # 创建悬浮窗口
        self.window = FloatingWindow()
        self.window.window_signals = WindowSignals()
        
        # 连接信号
        self.window.toggle_recording_signal.connect(lambda device_id, language: on_toggle_recording(self.window, self.engine, self.recorder, device_id, language))
        self.window.window_signals.start_recording.connect(self.on_start_recording)
        self.window.window_signals.stop_recording.connect(self.on_stop_recording)
        self.window.window_signals.download_model.connect(self.on_download_model)
        
        # 设置设备列表
        self.window.set_input_devices(self.input_devices)
        self.window.show()
        
    @Slot(int, str)  # 更新参数列表，添加language参数
    def on_start_recording(self, device_index, language="auto"):
        """开始录音"""
        if self.recording:
            logger.warning("已经在录音中，忽略此请求")
            return
            
        logger.info(f"开始录音，设备索引: {device_index}, 语言: {language}")
        
        # 检查设备
        if device_index < 0 or device_index >= len(self.input_devices):
            logger.error(f"无效的设备索引: {device_index}")
            self.window.status_label.setText("无效的设备索引")
            return
            
        # 生成唯一的音频文件名
        self.audio_file = os.path.join(self.temp_dir, f"recording_{uuid.uuid4()}.wav")
        
        # 标记录音状态
        self.recording = True
        
        # 创建并启动录音线程
        self.recording_thread = threading.Thread(
            target=self._recording_loop,
            args=(device_index, language),  # 传递语言参数
            daemon=True
        )
        self.recording_thread.start()
        
    def _recording_loop(self, device_index, language="auto"):
        """录音循环"""
        try:
            logger.debug("开始录音循环")
            
            # 开始录音
            logger.debug(f"启动音频录制器，设备：{device_index}")
            self.recorder.start_recording(device_index, self.audio_file)
            
            start_time = time.time()
            while self.recording and time.time() - start_time < self.max_recording_time:
                # 获取音频电平
                level = self.recorder.current_audio_level
                
                # 更新UI
                self.window.update_audio_level(level)
                
                # 简单的睡眠防止CPU占用过高
                time.sleep(0.05)
                
            # 如果是因为超时而停止
            if self.recording and time.time() - start_time >= self.max_recording_time:
                logger.info("录音达到最大时间限制，自动停止")
                self.recording = False
                self.window.update_recording_state(False)
                
            # 停止录音
            if hasattr(self.recorder, 'stop'):
                self.recorder.stop()
            
            # 处理录音结果
            if os.path.exists(self.audio_file) and os.path.getsize(self.audio_file) > 0:
                self.window.status_label.setText("正在转录...")
                try:
                    logger.info(f"开始转录音频：{self.audio_file}, 语言设置: {language}")
                    transcript = self.engine.transcribe(self.audio_file, language)  # 传递语言参数
                    
                    if transcript:
                        logger.info(f"转录成功: {transcript[:50]}...")
                        self.window.set_transcript(transcript)
                        self.window.status_label.setText("转录完成")
                    else:
                        logger.warning("转录结果为空")
                        self.window.status_label.setText("转录结果为空")
                except Exception as e:
                    logger.error(f"转录过程出错: {str(e)}")
                    self.window.status_label.setText(f"转录出错: {str(e)}")
            else:
                logger.warning(f"录音文件无效: {self.audio_file}")
                self.window.status_label.setText("录音文件无效")
                
        except Exception as e:
            logger.error(f"录音循环出错: {str(e)}")
            self.window.status_label.setText(f"录音出错: {str(e)}")
        finally:
            # 确保录音状态被重置
            self.recording = False
    
    @Slot()
    def on_stop_recording(self):
        """停止录音"""
        if not self.recording:
            logger.warning("没有进行中的录音，忽略此请求")
            return
            
        logger.info("停止录音")
        self.recording = False
        
        # 等待录音线程结束
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(1.0)  # 等待最多1秒
        
    @Slot(str)
    def on_download_model(self, model_name):
        """下载指定的模型"""
        logger.info(f"开始下载模型: {model_name}")
        
        try:
            # 更新UI状态
            self.window.status_label.setText(f"正在下载模型 {model_name}...")
            
            # 调用引擎下载模型
            success = self.engine.download_model(model_name)
            
            if success:
                logger.info(f"模型 {model_name} 下载成功")
                self.window.status_label.setText(f"模型 {model_name} 下载成功！")
                # 刷新模型列表
                self.window.refresh_model_list()
            else:
                logger.error(f"模型 {model_name} 下载失败")
                self.window.status_label.setText(f"模型 {model_name} 下载失败！")
        except Exception as e:
            logger.error(f"下载模型过程中出错: {str(e)}")
            self.window.status_label.setText(f"下载模型出错: {str(e)}")

def main():
    # 创建应用实例
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # 创建主应用对象
    typer = VoiceTyper()
    
    # 进入应用主循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 