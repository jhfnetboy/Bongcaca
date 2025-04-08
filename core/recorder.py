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
        
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
    def get_input_devices(self):
        devices = []
        for i in range(self.pyaudio.get_device_count()):
            device_info = self.pyaudio.get_device_info_by_index(i)
            if device_info.get('maxInputChannels') > 0:
                devices.append((i, device_info.get('name')))
        return devices
        
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
        
        try:
            if device_index is not None:
                self.logger.debug(f"Using device index: {device_index}")
            
            self.stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            
            self.frames = []
            self.is_recording = True
            
            self.recording_thread = threading.Thread(target=self._record)
            self.recording_thread.start()
            
            return True
        except Exception as e:
            self.logger.error(f"Error starting recording: {str(e)}")
            if self.stream:
                self.stream.close()
                self.stream = None
            self.is_recording = False
            return False
    
    def stop(self):
        if not self.is_recording:
            self.logger.warning("Not recording")
            return None
            
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join()
            self.recording_thread = None
            
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        with self.lock:
            if len(self.frames) > 0:
                self._save_recording()
                return self.current_filename
            else:
                self.logger.warning("No frames recorded")
                return None
    
    def _record(self):
        try:
            last_realtime_update = time.time()
            realtime_frames = []  # 实时模式的帧缓冲
            
            while self.is_recording:
                data = self.stream.read(1024, exception_on_overflow=False)
                with self.lock:
                    self.frames.append(data)
                
                # 计算音频电平
                audio_array = np.frombuffer(data, dtype=np.int16)
                self.current_audio_level = min(100, int(np.abs(audio_array).mean() / 100))
                
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
        except Exception as e:
            self.logger.error(f"Error during recording: {str(e)}")
            self.is_recording = False
    
    def _save_recording(self):
        try:
            wf = wave.open(self.current_filename, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            self.logger.debug(f"Recording saved to {self.current_filename}")
        except Exception as e:
            self.logger.error(f"Error saving recording: {str(e)}")
    
    def get_audio_level(self):
        return self.current_audio_level
        
    def __del__(self):
        if self.is_recording:
            self.stop()
        if self.pyaudio:
            self.pyaudio.terminate()

    def set_device(self, device_index):
        """设置录音设备"""
        self.logger.debug(f"设置录音设备: {device_index}")
        self.device_index = device_index
        return True 