import pyaudio
import wave
import os
import tempfile
import time
from datetime import datetime
import logging
import numpy as np

class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.temp_dir = tempfile.gettempdir()
        self.input_device_index = None
        self.logger = logging.getLogger(__name__)
        self.chunk_size = 1024
        self.audio_levels = []
        
    def set_input_device(self, device_index):
        """设置输入设备"""
        self.logger.info(f"设置输入设备: {device_index}")
        self.input_device_index = device_index
        
        # 如果正在录音,需要先停止再重新启动
        if self.stream and self.stream.is_active():
            self.logger.info("重新启动录音以应用新设备")
            self.stop()
            self.start_recording()
            
        return True
        
    def get_available_devices(self):
        """获取所有可用的输入设备"""
        devices = []
        try:
            info = self.audio.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            
            for i in range(num_devices):
                device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels') > 0:
                    devices.append({
                        'index': i,
                        'name': device_info.get('name'),
                        'channels': device_info.get('maxInputChannels'),
                        'rate': device_info.get('defaultSampleRate')
                    })
        except Exception as e:
            self.logger.error(f"Error getting devices: {e}")
            
        return devices
        
    def start_recording(self):
        """开始录音"""
        if self.input_device_index is None:
            self.logger.error("没有选择输入设备,无法开始录音")
            return False
            
        try:
            # 重置录音数据
            self.frames = []
            self.audio_levels = []
            
            # 创建音频流
            self.logger.debug(f"开始录音,使用设备: {self.input_device_index}")
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._callback
            )
            
            self.stream.start_stream()
            self.logger.debug("录音已开始")
            return True
            
        except Exception as e:
            self.logger.error(f"开始录音失败: {e}")
            return False
        
    def stop_recording(self):
        """停止录音并返回录音文件路径"""
        if not self.is_recording:
            return None
            
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        
        # 生成临时文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = os.path.join(self.temp_dir, f"recording_{timestamp}.wav")
        
        # 保存录音
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        self.logger.debug(f"Recording saved to: {temp_file}")
        return temp_file
        
    def get_audio_level(self):
        """获取当前音频电平(0-100)"""
        if not self.audio_levels:
            return 0
            
        # 返回最近电平的平均值
        return int(sum(self.audio_levels) / len(self.audio_levels))
            
    def record(self, duration):
        """录制指定时长的音频"""
        if self.input_device_index is None:
            raise Exception("No input device selected")
            
        self.frames = []
        self.is_recording = True
        
        # 设置录音参数
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        # 打开音频流
        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=CHUNK
        )
        
        # 开始录音
        self.logger.debug("Recording started...")
        for i in range(0, int(RATE / CHUNK * duration)):
            if not self.is_recording:
                break
            data = self.stream.read(CHUNK)
            self.frames.append(data)
        
        # 停止录音
        self.stop()
        
        # 保存录音文件
        temp_file = os.path.join(self.temp_dir, "temp_recording.wav")
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        self.logger.debug(f"Recording saved to: {temp_file}")
        return temp_file
        
    def stop(self):
        """停止录音"""
        if not self.stream:
            self.logger.debug("没有活动的录音流")
            return False
            
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.logger.debug("录音已停止")
            return True
        except Exception as e:
            self.logger.error(f"停止录音失败: {e}")
            return False
            
    def __del__(self):
        """清理资源"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

    def save_recording(self, filename):
        """保存录音到文件"""
        if self.frames:
            # 将录音数据写入文件
            wf = wave.open(filename, 'wb')
            wf.setnchannels(1)  # 单声道
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)  # 采样率
            wf.writeframes(b''.join(self.frames))
            wf.close()
            self.logger.debug(f"Recording saved to {filename}")
            return True
        return False

    def _callback(self, in_data, frame_count, time_info, status):
        """音频流回调函数"""
        # 保存音频帧
        self.frames.append(in_data)
        
        # 计算音频电平
        data = np.frombuffer(in_data, dtype=np.int16)
        rms = np.sqrt(np.mean(np.square(data)))
        db = 20 * np.log10(rms) if rms > 0 else -100
        normalized_level = min(100, max(0, int((db + 100) / 80 * 100)))
        self.audio_levels.append(normalized_level)
        
        # 保持最多10个电平值以计算平均值
        if len(self.audio_levels) > 10:
            self.audio_levels.pop(0)
            
        return (None, pyaudio.paContinue) 