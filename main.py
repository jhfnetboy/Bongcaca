import argparse
import logging
import os
import sys
import threading
import time
import platform
import glob
from datetime import datetime, timedelta
from pathlib import Path

from utils.logging import setup_logging
from utils.config import Config

logger = logging.getLogger("voice_typer")

# 设置配置和日志
config = Config()
setup_logging(config)

def cleanup_old_recordings(keep_recent=3):
    """清理旧的录音文件，只保留最近的几个文件"""
    temp_dir = os.path.join(os.path.expanduser("~"), ".voice_typer", "temp")
    if not os.path.exists(temp_dir):
        return
        
    logger.info(f"清理录音文件，仅保留最近{keep_recent}个文件...")
    
    # 查找所有录音文件
    recording_files = []
    for file_path in glob.glob(os.path.join(temp_dir, "recording_*.wav")):
        try:
            # 从文件名中获取时间戳
            filename = os.path.basename(file_path)
            if not filename.startswith("recording_"):
                continue
                
            timestamp_str = filename.replace("recording_", "").replace(".wav", "")
            if not timestamp_str.isdigit():
                continue
                
            timestamp = int(timestamp_str)
            recording_files.append((timestamp, file_path))
        except Exception as e:
            logger.error(f"处理录音文件时出错: {e}")
    
    # 按时间戳排序（最新的在前面）
    recording_files.sort(reverse=True)
    
    # 保留最近的几个文件，删除其余的
    count = 0
    for i, (timestamp, file_path) in enumerate(recording_files):
        if i >= keep_recent:
            try:
                os.remove(file_path)
                count += 1
                logger.debug(f"已删除旧录音文件: {file_path}")
            except Exception as e:
                logger.error(f"删除录音文件时出错: {e}")
    
    if count > 0:
        logger.info(f"已清理 {count} 个旧录音文件，保留了最近的 {min(keep_recent, len(recording_files))} 个")
    else:
        logger.info(f"没有需要清理的旧录音文件，当前共有 {len(recording_files)} 个")

def parse_args():
    parser = argparse.ArgumentParser(description='Voice Typer')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--test-input', action='store_true', help='Test text input functionality')
    return parser.parse_args()

def test_text_input():
    """测试文本输入功能"""
    logger.info("开始文本输入测试...")
    from platform_specific.input import TextInput
    
    text_input = TextInput()
    test_text = "macOS啊啊MacOS啊啊啊啊啊啊啊啊啊MacOS"
    
    # 获取当前焦点窗口
    window = text_input.get_focused_window()
    logger.info(f"当前焦点窗口: {window}")
    
    # 等待用户准备
    logger.info("请在3秒内将光标放在您希望输入文本的位置...")
    for i in range(3, 0, -1):
        logger.info(f"{i}...")
        time.sleep(1)
    
    # 测试输入文本
    logger.info(f"尝试输入文本: {test_text}")
    
    # 方法1: 直接使用input_text
    success = text_input.input_text(test_text)
    logger.info(f"方法1 (input_text) 结果: {'成功' if success else '失败'}")
    
    time.sleep(1)
    
    # 方法2: 使用insert_text
    success = text_input.insert_text(test_text)
    logger.info(f"方法2 (insert_text) 结果: {'成功' if success else '失败'}")
    
    logger.info("文本输入测试完成")

def play_start_beep():
    """播放开始录音提示音（单声嘟）"""
    try:
        import pyaudio
        import numpy as np
        
        pa = pyaudio.PyAudio()
        beep_stream = pa.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=16000,
            output=True
        )
        
        # 生成提示音（440Hz，200ms）
        duration = 0.2  # 秒
        volume = 0.3   # 音量（0.0-1.0）
        fs = 16000     # 采样率
        samples = (np.sin(2*np.pi*np.arange(fs*duration)*440/fs)).astype(np.float32)
        samples = samples * volume
        
        # 播放提示音
        beep_stream.write(samples.tobytes())
        
        # 关闭流
        beep_stream.stop_stream()
        beep_stream.close()
        pa.terminate()
        
    except Exception as e:
        logger.warning(f"播放提示音失败: {e}")

def play_complete_beep():
    """播放转写完成提示音（两声滴）"""
    try:
        import pyaudio
        import numpy as np
        
        pa = pyaudio.PyAudio()
        beep_stream = pa.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=16000,
            output=True
        )
        
        # 生成两声提示音（880Hz，各200ms）
        duration = 0.2  # 秒
        volume = 0.3   # 音量（0.0-1.0）
        fs = 16000     # 采样率
        pause = np.zeros(int(fs*0.1), dtype=np.float32)  # 100ms的间隔
        
        # 生成两个音调
        beep1 = (np.sin(2*np.pi*np.arange(fs*duration)*880/fs)).astype(np.float32) * volume
        beep2 = (np.sin(2*np.pi*np.arange(fs*duration)*880/fs)).astype(np.float32) * volume
        
        # 合并音频
        samples = np.concatenate([beep1, pause, beep2])
        
        # 播放提示音
        beep_stream.write(samples.tobytes())
        
        # 关闭流
        beep_stream.stop_stream()
        beep_stream.close()
        pa.terminate()
        
    except Exception as e:
        logger.warning(f"播放提示音失败: {e}")

def transcribe_audio(audio_file, model_type="large-v3", language="zh", initial_prompt=None, target_language=None):
    """从音频文件转写文本
    Args:
        audio_file: 音频文件路径
        model_type: 要使用的模型类型
        language: 音频的语言，可以是auto或特定语言代码
        initial_prompt: 初始提示，用于引导转写
        target_language: 目标语言代码，用于翻译
    """
    logger = logging.getLogger(__name__)
    logger.info(f"使用模型 {model_type} 转写音频 {audio_file}, 语言: {language}, 目标语言: {target_language}")
    
    # 初始化引擎
    from core.engine import WhisperEngine
    engine = WhisperEngine(config)
    engine.ensure_model_loaded()
    
    # 转写
    result = engine.transcribe(
        audio_file=audio_file, 
        language=language, 
        initial_prompt=initial_prompt, 
        target_language=target_language
    )
    logger.info(f"转写结果: {result}")
    
    return result

def run_recording_loop(window, recorder, engine, config):
    """运行录音循环"""
    try:
        while True:
            # 等待录音信号
            window.toggle_recording_signal.wait()
            
            # 获取当前选择的设备ID
            device_id = window.get_selected_device_id()
            if device_id is None:
                window.logger.error("未选择录音设备")
                continue
                
            # 获取当前选择的语言
            language = window.get_selected_language()
            if language is None:
                language = "auto"  # 默认使用中文
                
            # 确保模型已加载
            if not engine.model:
                try:
                    window.logger.info("正在加载模型...")
                    engine.ensure_model_loaded()
                except Exception as e:
                    window.logger.error(f"加载模型失败: {e}")
                    continue
            
            # 开始录音
            window.logger.info("开始录音")
            if not recorder.start_recording(device_id):
                window.logger.error("启动录音失败")
                continue
                
            # 播放开始录音提示音
            play_start_beep()
            
            # 更新UI状态
            window.update_recording_state(True)
            
            # 等待录音结束
            window.toggle_recording_signal.wait()
            
            # 停止录音
            window.logger.info("停止录音")
            audio_file = recorder.stop()
            if not audio_file:
                window.logger.error("停止录音失败")
                continue
                
            # 更新UI状态
            window.update_recording_state(False)
            
            # 转写录音
            window.logger.info(f"开始转写录音文件: {audio_file}")
            try:
                result = engine.transcribe(
                    audio_file,
                    language=language
                )
                if result:
                    window.update_result(result)
                    # 播放转写完成提示音
                    play_complete_beep()
                else:
                    window.logger.error("转写失败")
            except Exception as e:
                window.logger.error(f"录音转写过程中出错: {str(e)}")
                window.logger.error(str(e))
                import traceback
                window.logger.error(traceback.format_exc())
                
    except Exception as e:
        window.logger.error(f"录音循环出错: {str(e)}")
        import traceback
        window.logger.error(traceback.format_exc())
    finally:
        # 清理资源
        if recorder:
            recorder.stop()
        window.update_recording_state(False)

def main():
    """主函数"""
    args = parse_args()
    
    # 如果是测试文本输入模式
    if args.test_input:
        test_text_input()
        return
    
    # 设置调试模式
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")
    
    # 系统信息
    logger.info(f"操作系统: {platform.system()} {platform.release()}")
    logger.info(f"Python版本: {platform.python_version()}")
    
    # 检查配置
    logger.debug(f"配置目录: {config._get_config_dir()}")
    logger.debug(f"模型目录: {config.models_dir}")
    
    # 清理旧录音文件，仅保留最近3个
    cleanup_old_recordings(keep_recent=3)
    
    try:
        # 导入必要的组件
        from core.engine import WhisperEngine
        from core.recorder import AudioRecorder
        from PySide6.QtWidgets import QApplication
        from ui.floating_window import FloatingWindow
        
        # 初始化语音引擎
        engine = WhisperEngine(config)
        
        # 初始化录音器
        recorder = AudioRecorder()
        
        # 创建QApplication实例
        app = QApplication([])
        
        # 设置MacOS Dock图标
        if sys.platform == "darwin":
            try:
                from ui.macos_app_icon import register_dock_icon
                register_dock_icon(app)
            except Exception as e:
                logger.error(f"设置MacOS Dock图标失败: {e}")
        
        # 创建主窗口
        window = FloatingWindow(config)
        
        # 设置回调函数
        def setup_callbacks():
            # 录音控制回调
            window.toggle_recording_signal.connect(lambda: run_recording_loop(window, recorder, engine, config))
            # 连接设备变更信号
            window.device_changed.connect(recorder.set_device)
            # 连接模式切换信号
            window.transcription_mode_changed.connect(lambda mode: logger.info(f"转写模式已切换为: {mode}"))
            # 连接模型变更信号
            window.model_changed.connect(lambda model: on_model_change(window, engine, model))
        
        # 设置回调
        setup_callbacks()
        
        # 显示窗口
        window.show()
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except ImportError as e:
        logger.critical(f"无法导入必要的模块: {e}")
        print(f"缺少必要的依赖: {e}")
        print("请确保已安装所有必要的依赖项")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"程序启动失败: {e}")
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()