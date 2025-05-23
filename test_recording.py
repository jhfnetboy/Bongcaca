#!/usr/bin/env python3
"""
简单的录音测试脚本
用于验证修复后的录音和转写功能
"""

import logging
import time
import os
from core.recorder import AudioRecorder
from core.engine import WhisperEngine
from utils.config import Config
from utils.logging import setup_logging

def test_recording_and_transcription():
    """测试录音和转写功能"""
    
    # 设置日志
    config = Config()
    setup_logging(config)
    logger = logging.getLogger("test")
    
    logger.info("开始测试录音和转写功能...")
    
    # 初始化录音器和引擎
    recorder = AudioRecorder()
    engine = WhisperEngine(config)
    
    # 获取可用设备
    devices = recorder.get_input_devices()
    if not devices:
        logger.error("未找到可用的录音设备")
        return False
        
    device_id = devices[0][0]
    logger.info(f"使用设备: {devices[0][1]} (ID: {device_id})")
    
    try:
        # 开始录音
        logger.info("开始录音，请说话... (5秒后自动停止)")
        success = recorder.start_recording(device_index=device_id)
        
        if not success:
            logger.error("录音启动失败")
            return False
            
        # 录音5秒
        start_time = time.time()
        while time.time() - start_time < 5.0:
            level = recorder.get_audio_level()
            if level > 0:
                logger.info(f"音频电平: {level}%")
            time.sleep(0.5)
            
        # 停止录音
        logger.info("停止录音...")
        audio_file = recorder.stop()
        
        if not audio_file or not os.path.exists(audio_file):
            logger.error("录音文件未生成")
            return False
            
        logger.info(f"录音文件已保存: {audio_file}")
        file_size = os.path.getsize(audio_file)
        logger.info(f"文件大小: {file_size} bytes")
        
        # 转写音频
        logger.info("开始转写音频...")
        transcript = engine.transcribe(audio_file, language="zh")
        
        logger.info(f"转写结果: {transcript}")
        
        # 清理测试文件
        try:
            os.remove(audio_file)
            logger.info("已清理测试文件")
        except:
            pass
            
        return True
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        return False

if __name__ == "__main__":
    success = test_recording_and_transcription()
    if success:
        print("✅ 录音和转写功能测试成功！")
    else:
        print("❌ 录音和转写功能测试失败！") 