import logging
import os
from pathlib import Path

def setup_logging(config=None):
    """设置日志系统"""
    # 创建日志目录
    log_dir = os.path.join(os.path.expanduser("~"), ".voice_typer", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 移除所有现有的处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                                 datefmt='%Y-%m-%d %H:%M:%S')
    
    # 添加文件处理器
    log_file = os.path.join(log_dir, f"voice_typer.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 设置特定模块的日志级别
    logging.getLogger("PySide6").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # 设置应用程序日志器
    app_logger = logging.getLogger("voice_typer")
    app_logger.setLevel(logging.DEBUG)
    
    # 记录初始信息
    app_logger.info("日志系统初始化完成")
    app_logger.debug(f"日志保存路径: {log_file}")
    
    return app_logger 