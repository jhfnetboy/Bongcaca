import pyaudio
import wave
import os
import tempfile
import time
from datetime import datetime
import logging
import numpy as np
import threading

class AudioRecorder:
    def __init__(self, temp_dir=None):
        self.logger = logging.getLogger(__name__)
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.temp_dir = temp_dir if temp_dir else os.path.join(os.path.expanduser("~"), ".voice_typer", "temp")
        self.current_filename = None
        self.recording_thread = None
        self.lock = threading.Lock()
        self.current_audio_level = 0
        self.device_index = None
        self.realtime_callback = None  # 实时转写回调函数
        self.realtime_mode = False     # 实时转写模式标志
        
        # 初始化设备
        self._ensure_temp_dir()
        self._log_available_devices()
        
    def _ensure_temp_dir(self):
        """确保临时目录存在"""
        if not os.path.exists(self.temp_dir):
            try:
                os.makedirs(self.temp_dir)
                self.logger.info(f"创建临时录音目录: {self.temp_dir}")
            except Exception as e:
                self.logger.error(f"创建临时录音目录失败: {e}")
                
    def _log_available_devices(self):
        """记录可用设备信息"""
        self.logger.info("------可用音频输入设备------")
        devices = self.get_input_devices()
        if not devices:
            self.logger.warning("未检测到音频输入设备")
        else:
            for device_id, device_name in devices:
                self.logger.info(f"ID: {device_id} - 名称: {device_name}")
        self.logger.info("---------------------------")
            
    def get_input_devices(self):
        """获取可用的音频输入设备列表"""
        try:
            devices = []
            for i in range(self.pyaudio.get_device_count()):
                try:
                    device_info = self.pyaudio.get_device_info_by_index(i)
                    if device_info and device_info.get('maxInputChannels') > 0:
                        devices.append((i, device_info.get('name')))
                except Exception as e:
                    self.logger.error(f"获取设备 {i} 信息失败: {e}")
            return devices
        except Exception as e:
            self.logger.error(f"获取输入设备列表失败: {e}")
            return []
        
    def start_recording(self, device_index=None, realtime_mode=False, realtime_callback=None):
        """开始录音
        
        Args:
            device_index: 设备索引
            realtime_mode: 是否使用实时转写模式
            realtime_callback: 实时回调函数，接收音频数据块和级别
        """
        if self.is_recording:
            self.logger.warning("Already recording")
            return False
            
        timestamp = int(time.time())
        self.current_filename = os.path.join(self.temp_dir, f"recording_{timestamp}.wav")
        self.logger.debug(f"Starting recording to {self.current_filename}")
        
        # 设置实时模式
        self.realtime_mode = realtime_mode
        self.realtime_callback = realtime_callback
        
        # 使用设备索引
        if device_index is not None:
            self.device_index = device_index
            
        # 检查设备
        if self.device_index is None:
            self.logger.error("未指定录音设备")
            return False
            
        # 验证设备是否存在
        try:
            device_info = self.pyaudio.get_device_info_by_index(self.device_index)
            if not device_info:
                self.logger.error(f"设备ID {self.device_index} 不存在")
                return False
                
            self.logger.info(f"使用录音设备: {device_info.get('name')} (ID: {self.device_index})")
        except Exception as e:
            self.logger.error(f"验证设备ID {self.device_index} 失败: {e}")
            return False
        
        try:
            self.logger.debug(f"Using device index: {self.device_index}")
            
            # 播放短提示音表示开始录音
            try:
                self._play_beep()
            except Exception as e:
                self.logger.warning(f"播放提示音失败: {e}")
            
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=1024
            )
            
            self.frames = []
            self.is_recording = True
            
            self.recording_thread = threading.Thread(target=self._record)
            self.recording_thread.daemon = True  # 设置为守护线程
            self.recording_thread.start()
            
            # 确保线程已成功启动
            time.sleep(0.1)
            if not self.recording_thread.is_alive():
                self.logger.error("Recording thread failed to start")
                self.is_recording = False
                return False
                
            self.logger.info("Recording started successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error starting recording: {str(e)}")
            if self.stream:
                self.stream.close()
                self.stream = None
            self.is_recording = False
            return False
            
    def _play_beep(self):
        """播放简短的提示音表示开始录音"""
        try:
            # 使用PyAudio播放简短提示音
            beep_stream = self.pyaudio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=16000,
                output=True
            )
            
            # 生成简短的提示音（440Hz，200ms）
            duration = 0.2  # 秒
            volume = 0.5   # 音量（0.0-1.0）
            fs = 16000     # 采样率
            samples = (np.sin(2*np.pi*np.arange(fs*duration)*440/fs)).astype(np.float32)
            samples = samples * volume
            
            # 播放提示音
            beep_stream.write(samples.tobytes())
            
            # 关闭流
            beep_stream.stop_stream()
            beep_stream.close()
            
        except Exception as e:
            self.logger.warning(f"播放提示音失败: {e}")
    
    def stop(self):
        if not self.is_recording:
            self.logger.warning("Not recording")
            return None
            
        self.is_recording = False
        
        # 使用临时变量保存当前文件名
        current_file = self.current_filename
        
        # 确保停止录音线程
        if self.recording_thread:
            try:
                self.recording_thread.join(timeout=2.0)  # 设置超时时间
                if self.recording_thread.is_alive():
                    self.logger.warning("Recording thread did not terminate properly")
            except Exception as e:
                self.logger.error(f"Error joining recording thread: {e}")
            finally:
                self.recording_thread = None
            
        # 安全关闭音频流
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                self.logger.error(f"Error closing audio stream: {e}")
            finally:
                self.stream = None
        
        # 使用锁保护帧操作并保存录音
        try:
            with self.lock:
                if len(self.frames) > 0:
                    frames_copy = list(self.frames)  # 创建帧数据的副本
                    self.frames = []  # 清空原始帧列表
                    self._save_recording_from_frames(frames_copy, current_file)
                    return current_file
                else:
                    self.logger.warning("No frames recorded")
                    return None
        except Exception as e:
            self.logger.error(f"Error in stop method: {e}")
            return None
            
    def _save_recording_from_frames(self, frames, filename):
        """从帧列表保存录音到指定文件"""
        try:
            if not frames or len(frames) == 0:
                self.logger.warning("No frames to save")
                return False
                
            wf = wave.open(filename, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(frames))
            wf.close()
            self.logger.info(f"Recording saved to {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving recording: {str(e)}")
            return False
    
    def _save_recording(self):
        """保存当前录音帧到文件"""
        try:
            return self._save_recording_from_frames(self.frames, self.current_filename)
        except Exception as e:
            self.logger.error(f"Error saving recording: {str(e)}")
            return False
    
    def _record(self):
        try:
            last_realtime_update = time.time()
            realtime_frames = []  # 实时模式的帧缓冲
            
            self.logger.debug("Recording thread started")
            time_since_last_level_log = 0
            
            while self.is_recording:
                try:
                    start_time = time.time()
                    data = self.stream.read(1024, exception_on_overflow=False)
                    with self.lock:
                        self.frames.append(data)
                    
                    # 计算音频电平
                    audio_array = np.frombuffer(data, dtype=np.int16)
                    abs_data = np.abs(audio_array)
                    level = 0
                    
                    if len(abs_data) > 0:
                        # 计算更准确的音频电平
                        # 1. 计算RMS (root mean square)
                        mean_squared = np.mean(abs_data**2)
                        # 确保值有效并避免无效值错误
                        if mean_squared > 0:
                            rms = np.sqrt(mean_squared)
                            # 2. 归一化到0-100的范围，使用对数比例
                            # 增强音频电平显示，使其对低音量更敏感
                            normalized_level = np.log10(max(1, rms)) / np.log10(32768) * 100
                            # 提高低音量显示的灵敏度
                            level = min(100, max(0, int(normalized_level * 1.5)))
                    
                    self.current_audio_level = level
                    
                    # 每秒记录一次音频电平
                    time_since_last_level_log += time.time() - start_time
                    if time_since_last_level_log >= 0.5:  # 改为每0.5秒记录一次
                        self.logger.debug(f"Current audio level: {self.current_audio_level}")
                        time_since_last_level_log = 0
                    
                    # 实时转写模式处理
                    if self.realtime_mode and self.realtime_callback:
                        # 将数据添加到实时帧缓冲区
                        realtime_frames.append(data)
                        
                        # 更频繁地发送更新，每300毫秒一次
                        current_time = time.time()
                        if current_time - last_realtime_update >= 0.3:  # 从0.5秒减少到0.3秒
                            if realtime_frames:
                                # 回调处理音频数据块，并传递当前音频电平
                                self.realtime_callback(b''.join(realtime_frames), self.current_audio_level)
                                
                                # 清空实时帧缓冲区，保持较小的延迟
                                realtime_frames = []
                                
                                # 更新时间戳
                                last_realtime_update = current_time
                                
                                # 记录调试信息
                                self.logger.debug(f"发送实时音频数据块，音频电平: {self.current_audio_level}")
                except IOError as e:
                    # 捕获常见的音频流错误并记录
                    self.logger.error(f"Audio stream error: {e}")
                    if "Input overflowed" in str(e):
                        # 输入溢出通常不是严重问题，可以继续
                        continue
                    else:
                        # 其他IO错误可能需要停止录音
                        self.is_recording = False
                        break
                except Exception as e:
                    self.logger.error(f"Error reading from audio stream: {e}")
                    self.is_recording = False
                    break
                    
        except Exception as e:
            self.logger.error(f"Error during recording: {str(e)}")
            self.is_recording = False
    
    def get_audio_level(self):
        # 在未录音状态下生成一些随机的低电平值，确保波形显示可见
        if not self.is_recording:
            return np.random.uniform(5, 15)
        return self.current_audio_level
        
    def __del__(self):
        try:
            if self.is_recording:
                self.stop()
            if hasattr(self, 'pyaudio') and self.pyaudio:
                self.pyaudio.terminate()
        except Exception as e:
            logging.error(f"Error in AudioRecorder.__del__: {e}")

    def set_device(self, device_index):
        """设置录音设备"""
        self.logger.info(f"设置录音设备: {device_index}")
        
        # 检查设备是否有效
        try:
            device_info = self.pyaudio.get_device_info_by_index(device_index)
            if device_info and device_info.get('maxInputChannels') > 0:
                self.logger.info(f"录音设备设置成功: {device_info.get('name')} (ID: {device_index})")
                self.device_index = device_index
                return True
            else:
                self.logger.error(f"无效的录音设备 ID: {device_index}")
                return False
        except Exception as e:
            self.logger.error(f"设置录音设备失败: {e}")
            return False 