import logging
import os
from pathlib import Path

def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = os.path.expanduser("~/.local/share/voicetyper/logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "voicetyper.log")),
            logging.StreamHandler()
        ]
    )
    
    # 设置 faster-whisper 的日志级别
    logging.getLogger("faster_whisper").setLevel(logging.INFO) 