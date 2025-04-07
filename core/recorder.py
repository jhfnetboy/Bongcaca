import pyaudio
import wave
import os
import tempfile
from datetime import datetime

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        """初始化录音器"""
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.temp_dir = tempfile.gettempdir()
        
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return
            
        self.frames = []
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk
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
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        return temp_file
        
    def get_audio_level(self):
        """获取当前音量级别，用于UI显示"""
        if not self.is_recording or not self.stream:
            return 0
            
        try:
            data = self.stream.read(self.chunk, exception_on_overflow=False)
            self.frames.append(data)
            rms = max(abs(int.from_bytes(data[i:i+2], 'little', signed=True)) 
                     for i in range(0, len(data), 2))
            return min(100, int(rms / 32767 * 100))
        except:
            return 0
            
    def __del__(self):
        """清理资源"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate() 