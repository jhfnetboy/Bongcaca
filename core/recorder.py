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
                        device_name = device_info.get('name')
                        sample_rate = device_info.get('defaultSampleRate', 44100)
                        self.logger.debug(f"Found input device: ID={i}, Name={device_name}, "
                                        f"Channels={device_info.get('maxInputChannels')}, "
                                        f"SampleRate={sample_rate}")
                        devices.append((i, device_name))
                except Exception as e:
                    self.logger.error(f"获取设备 {i} 信息失败: {e}")
            
            if not devices:
                self.logger.warning("未检测到任何音频输入设备，这可能是由于：")
                self.logger.warning("1. 没有连接麦克风或音频输入设备")
                self.logger.warning("2. macOS隐私设置阻止了麦克风访问")
                self.logger.warning("3. 音频驱动问题")
                
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
            # 如果没有指定设备，尝试使用第一个可用设备
            devices = self.get_input_devices()
            if devices:
                self.device_index = devices[0][0]
                self.logger.info(f"自动选择第一个可用设备: {devices[0][1]} (ID: {self.device_index})")
            else:
                self.logger.error("未找到可用的录音设备")
                return False
            
        # 验证设备是否存在
        try:
            device_info = self.pyaudio.get_device_info_by_index(self.device_index)
            if not device_info:
                self.logger.error(f"设备ID {self.device_index} 不存在")
                return False
                
            device_name = device_info.get('name')
            max_channels = device_info.get('maxInputChannels', 0)
            default_rate = device_info.get('defaultSampleRate', 44100)
            
            self.logger.info(f"使用录音设备: {device_name} (ID: {self.device_index})")
            self.logger.info(f"设备参数: 最大输入通道={max_channels}, 默认采样率={default_rate}")
            
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
            
            # 尝试不同的音频参数配置
            audio_configs = [
                # 配置1: 标准16kHz单声道
                {'format': pyaudio.paInt16, 'channels': 1, 'rate': 16000, 'frames_per_buffer': 1024},
                # 配置2: 设备默认采样率，然后重采样
                {'format': pyaudio.paInt16, 'channels': 1, 'rate': int(default_rate), 'frames_per_buffer': 1024},
                # 配置3: 更大的缓冲区
                {'format': pyaudio.paInt16, 'channels': 1, 'rate': 16000, 'frames_per_buffer': 2048},
            ]
            
            stream_created = False
            for i, config in enumerate(audio_configs):
                try:
                    self.logger.info(f"尝试音频配置 {i+1}: {config}")
                    self.stream = self.pyaudio.open(
                        format=config['format'],
                        channels=config['channels'],
                        rate=config['rate'],
                        input=True,
                        input_device_index=self.device_index,
                        frames_per_buffer=config['frames_per_buffer']
                    )
                    
                    # 测试读取一小段数据
                    test_data = self.stream.read(config['frames_per_buffer'], exception_on_overflow=False)
                    if test_data:
                        self.logger.info(f"音频配置 {i+1} 测试成功")
                        stream_created = True
                        # 保存采样率信息以备后用
                        self._recording_sample_rate = config['rate']
                        break
                    
                except Exception as e:
                    self.logger.warning(f"音频配置 {i+1} 失败: {e}")
                    if self.stream:
                        try:
                            self.stream.close()
                        except:
                            pass
                        self.stream = None
            
            if not stream_created:
                self.logger.error("所有音频配置都失败")
                return False
            
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
                try:
                    self.stream.close()
                except:
                    pass
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
                    frames_copy = None  # 显式释放副本
                    return current_file
                else:
                    self.logger.warning("No frames recorded")
                    return None
        except Exception as e:
            self.logger.error(f"Error in stop method: {e}")
            return None
        finally:
            # 确保清理所有资源
            self.current_filename = None
            self.current_audio_level = 0
            self.realtime_callback = None
            self.realtime_mode = False
    
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
            
            # 获取录音参数
            sample_rate = getattr(self, '_recording_sample_rate', 16000)
            self.logger.info(f"录音参数: 采样率={sample_rate}Hz")
            
            # 性能优化：预分配音频处理变量
            chunk_size = 1024
            level_log_interval = 1.0  # 改为每1秒记录一次
            realtime_interval = 0.3   # 实时转写间隔
            
            # 预分配numpy数组避免重复分配
            audio_buffer = np.zeros(chunk_size, dtype=np.int16)
            
            while self.is_recording:
                try:
                    loop_start = time.time()
                    data = self.stream.read(chunk_size, exception_on_overflow=False)
                    
                    # 如果采样率不是16kHz，需要重采样到16kHz保存
                    if sample_rate != 16000:
                        # 简单的重采样（实际项目中可能需要更复杂的重采样算法）
                        # 这里暂时保存原始数据，在保存文件时处理
                        pass
                    
                    with self.lock:
                        self.frames.append(data)
                    
                    # 性能优化：改进音频电平计算
                    try:
                        # 重用预分配的buffer避免重复内存分配
                        data_len = len(data) // 2  # int16是2字节
                        if data_len <= chunk_size:
                            audio_buffer[:data_len] = np.frombuffer(data[:data_len*2], dtype=np.int16)
                            audio_array = audio_buffer[:data_len]
                        else:
                            audio_array = np.frombuffer(data, dtype=np.int16)
                        
                        if len(audio_array) > 0:
                            # 使用更高效的电平计算
                            abs_data = np.abs(audio_array, dtype=np.float32)  # 使用float32减少内存
                            mean_squared = np.mean(abs_data**2)
                            rms = 0  # 初始化rms变量
                            
                            if mean_squared > 0:
                                rms = np.sqrt(mean_squared)
                                # 归一化到0-100的范围
                                max_value = 32768.0  # int16的最大值
                                normalized_level = (rms / max_value) * 100
                                
                                # 应用对数缩放以提高低音量的可见性
                                if normalized_level > 0:
                                    log_level = np.log10(max(0.01, normalized_level)) * 25 + 25  # 调整缩放参数
                                    level = min(100, max(0, int(log_level)))
                                else:
                                    level = 0
                                    
                                # 对于低输入信号，提供基础电平显示
                                if level < 3 and rms > 0:
                                    level = max(5, min(30, int(rms * 10)))  # 增强微弱信号的可见性
                                    
                            else:
                                level = 0
                        else:
                            level = 0
                            rms = 0  # 确保rms变量始终有定义
                            
                        # 平滑处理，避免电平跳动过于剧烈
                        if hasattr(self, '_last_level'):
                            alpha = 0.3  # 平滑系数
                            level = int(alpha * level + (1 - alpha) * self._last_level)
                        self._last_level = level
                        
                        self.current_audio_level = level
                        
                    except Exception as e:
                        self.logger.warning(f"计算音频电平时出错: {e}")
                        self.current_audio_level = 0
                    
                    # 减少日志记录频率
                    time_since_last_level_log += time.time() - loop_start
                    if time_since_last_level_log >= level_log_interval:
                        self.logger.debug(f"当前音频电平: {self.current_audio_level}%, 数据长度: {len(data)}, RMS: {rms:.2f}")
                        time_since_last_level_log = 0
                    
                    # 回调处理（用于电平更新和实时转写）
                    current_time = time.time()
                    
                    # 总是调用回调来更新电平（不论是否实时模式）
                    if self.realtime_callback:
                        # 实时模式下需要传递数据，非实时模式只需要传递电平
                        if self.realtime_mode:
                            # 将数据添加到实时帧缓冲区
                            realtime_frames.append(data)
                            
                            # 更频繁地发送更新，每300毫秒一次
                            if current_time - last_realtime_update >= realtime_interval:
                                if realtime_frames:
                                    # 回调处理音频数据块，并传递当前音频电平
                                    self.realtime_callback(b''.join(realtime_frames), self.current_audio_level)
                                    
                                    # 清空实时帧缓冲区，保持较小的延迟
                                    realtime_frames = []
                                    
                                    # 更新时间戳
                                    last_realtime_update = current_time
                                    
                                    # 记录调试信息
                                    self.logger.debug(f"发送实时音频数据块，音频电平: {self.current_audio_level}")
                        else:
                            # 非实时模式，只更新电平，每100ms一次
                            if current_time - last_realtime_update >= 0.1:  # 每100ms更新一次电平
                                self.realtime_callback(b'', self.current_audio_level)
                                last_realtime_update = current_time
                                
                except IOError as e:
                    # 捕获常见的音频流错误并记录
                    if "Input overflowed" in str(e):
                        # 输入溢出通常不是严重问题，可以继续
                        self.logger.debug("音频输入溢出（这通常是正常的）")
                        continue
                    else:
                        # 其他IO错误可能需要停止录音
                        self.logger.error(f"Audio stream error: {e}")
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