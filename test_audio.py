#!/usr/bin/env python3
"""
音频测试脚本 - 生成测试音频并验证转写功能
"""

import numpy as np
import wave
import tempfile
import os
import sys
sys.path.append('.')
from core.engine import WhisperEngine
from utils.config import Config

def generate_test_audio(duration=3, frequency=440, sample_rate=16000):
    """生成测试音频文件"""
    # 生成正弦波音频
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * frequency * t) * 0.3  # 降低音量
    
    # 转换为16位整数
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # 保存为WAV文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
        temp_path = f.name
        
    with wave.open(temp_path, 'wb') as wf:
        wf.setnchannels(1)  # 单声道
        wf.setsampwidth(2)  # 16位
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    
    return temp_path

def test_transcription():
    """测试转写功能"""
    print("=== 音频转写测试 ===")
    
    # 创建配置和引擎
    config = Config()
    engine = WhisperEngine(config)
    
    # 生成测试音频
    print("生成测试音频...")
    test_audio_path = generate_test_audio(duration=2, frequency=440)
    
    try:
        print(f"测试音频文件: {test_audio_path}")
        print(f"文件大小: {os.path.getsize(test_audio_path)} bytes")
        
        # 测试转写
        print("开始转写...")
        result = engine.transcribe(test_audio_path, language="zh")
        
        print(f"转写结果: '{result}'")
        
        if result and "错误" not in result:
            print("✅ 转写功能正常")
        else:
            print("❌ 转写功能异常")
            
    finally:
        # 清理测试文件
        if os.path.exists(test_audio_path):
            os.unlink(test_audio_path)
            print(f"已清理测试文件: {test_audio_path}")

if __name__ == "__main__":
    test_transcription() 