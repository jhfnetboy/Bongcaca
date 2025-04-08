import pyaudio
import wave
import os
import tempfile
import time
from datetime import datetime

class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.temp_dir = tempfile.gettempdir()
        self.input_device_index = None
        
    def set_input_device(self, device_index):
        """设置输入设备"""
        self.input_device_index = device_index
        
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
            print(f"Error getting devices: {e}")
            
        return devices
        
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return
            
        self.frames = []
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=1024
        )
        self.is_recording = True
        
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
        
        return temp_file
        
    def get_audio_level(self):
        """获取当前音量级别，用于UI显示"""
        if not self.is_recording or not self.stream:
            return 0
            
        try:
            data = self.stream.read(1024, exception_on_overflow=False)
            self.frames.append(data)
            rms = max(abs(int.from_bytes(data[i:i+2], 'little', signed=True)) 
                     for i in range(0, len(data), 2))
            return min(100, int(rms / 32767 * 100))
        except:
            return 0
            
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
        print("Recording started...")
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
        
        return temp_file
        
    def stop(self):
        """停止录音"""
        if self.is_recording:
            self.is_recording = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            print("Recording stopped")
            
    def __del__(self):
        """清理资源"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate() 