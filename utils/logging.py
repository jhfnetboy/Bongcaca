import logging
import os
from datetime import datetime

def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = os.path.join(os.path.expanduser("~"), ".voice_typer", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 生成日志文件名
    log_file = os.path.join(log_dir, f"voice_typer_{datetime.now().strftime('%Y%m%d')}.log")
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 移除所有现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加处理器
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 设置其他模块的日志级别
    logging.getLogger('PySide6').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return root_logger 