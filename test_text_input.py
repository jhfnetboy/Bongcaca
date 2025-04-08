import time
import logging
import sys
from platform_specific.input import TextInput
from utils.logging import setup_logging

def main():
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    logger.info("启动文本插入测试")
    
    # 创建文本输入器
    text_input = TextInput()
    
    # 获取当前焦点窗口
    focused_window = text_input.get_focused_window()
    logger.info(f"当前焦点窗口: {focused_window}")
    
    # 准备测试
    logger.info("准备测试文本插入,请将光标放置在目标位置...")
    for i in range(5, 0, -1):
        logger.info(f"{i}秒后开始插入文本...")
        time.sleep(1)
    
    # 测试文本
    test_text = "测试MacOS的应用界面输入文字"
    logger.info(f"开始插入文本: '{test_text}'")
    
    # 测试PyAutoGUI方法
    try:
        logger.info("使用PyAutoGUI方法")
        text_input._insert_text_macos(test_text)
        logger.info("PyAutoGUI方法完成")
    except Exception as e:
        logger.error(f"PyAutoGUI方法失败: {e}")
    
    time.sleep(1)
    
    # 测试AppleScript方法
    try:
        logger.info("使用AppleScript方法")
        import subprocess
        cmd = f'osascript -e \'tell application "System Events" to keystroke "{test_text}"\''
        subprocess.run(cmd, shell=True)
        logger.info("AppleScript方法完成")
    except Exception as e:
        logger.error(f"AppleScript方法失败: {e}")
    
    # 测试input_text方法
    try:
        logger.info("使用input_text方法")
        text_input.input_text(test_text)
        logger.info("input_text方法完成")
    except Exception as e:
        logger.error(f"input_text方法失败: {e}")
    
    logger.info("文本插入测试完成")

if __name__ == "__main__":
    main() 