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

def play_notification_sound():
    """播放提示音以提示转写完成"""
    try:
        # 使用PyAudio播放简短提示音
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
            
            # 生成提示音（440Hz和880Hz，各200ms）
            duration = 0.2  # 秒
            volume = 0.5   # 音量（0.0-1.0）
            fs = 16000     # 采样率
            
            # 第一个音（440Hz）
            samples1 = (np.sin(2*np.pi*np.arange(fs*duration)*440/fs)).astype(np.float32)
            samples1 = samples1 * volume
            
            # 短暂停顿
            pause = np.zeros(int(fs*0.1), dtype=np.float32)
            
            # 第二个音（880Hz）
            samples2 = (np.sin(2*np.pi*np.arange(fs*duration)*880/fs)).astype(np.float32)
            samples2 = samples2 * volume
            
            # 合并两个提示音
            samples = np.concatenate([samples1, pause, samples2])
            
            # 播放提示音
            beep_stream.write(samples.tobytes())
            
            # 关闭流
            beep_stream.stop_stream()
            beep_stream.close()
            pa.terminate()
            
            logger.debug("播放转写完成提示音")
            
        except Exception as e:
            logger.warning(f"播放提示音失败: {e}")
    except Exception as e:
        logger.error(f"播放通知声音过程中出错: {e}")

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

def run_recording_loop(window, engine, recorder):
    """录音和转写的主循环
    Args:
        window: 主窗口对象，用于更新UI
        engine: WhisperEngine对象
        recorder: AudioRecorder对象
    """
    logger = logging.getLogger(__name__)
    logger.debug("开始录音循环")
    
    # 获取当前设置的语言选项和模式
    selected_language = window.target_language if window.target_language != "auto" else "zh"
    is_realtime_mode = window.transcription_mode == "realtime"
    target_language = None if window.target_language == "auto" else window.target_language
    
    logger.info(f"录音设置 - 模式: {window.transcription_mode}, 语言: {selected_language}, 翻译目标: {target_language}")
    
    # 设置最大录音时间为5分钟
    timeout = time.time() + 300  # 5分钟超时
    
    try:
        # 开始录音
        recorder.start_recording(
            device_index=window.get_selected_device_id(), 
            realtime_mode=is_realtime_mode
        )
        
        # 设置录音状态
        window.update_recording_state(True)
        window.update_status("正在录音...")
        
        # 实时转写的累积文本
        realtime_text = ""
        last_transcribe_time = time.time()
        
        # 监听录音循环
        while window.is_recording:
            if time.time() > timeout:
                logger.info("录音超时，自动停止")
                window.update_status("录音超时，自动停止")
                break
                
            # 更新音频电平
            try:
                from PySide6.QtWidgets import QApplication
                level = recorder.current_audio_level
                window.update_audio_level(level)
                QApplication.processEvents()
                
                # 实时转写模式处理
                if is_realtime_mode and time.time() - last_transcribe_time > 2.0:  # 每2秒尝试一次实时转写
                    # 使用引擎进行实时转写
                    transcript = engine.get_realtime_transcription(
                        language=selected_language, 
                        target_language=target_language
                    )
                    
                    if transcript:
                        # 更新UI显示转写结果
                        window.update_result(transcript)
                        realtime_text = transcript
                        
                    last_transcribe_time = time.time()
            except Exception as e:
                logger.error(f"录音循环中出错: {e}")
                window.update_status(f"录音过程中出错: {str(e)}")
                
            time.sleep(0.05)  # 降低CPU使用率
            
        # 停止录音
        logger.info("停止录音")
        window.update_status("正在处理录音...")
        file_path = recorder.stop()
        
        # 如果是批量模式或实时模式没有得到结果，则进行完整转写
        if file_path and os.path.exists(file_path):
            if not is_realtime_mode or not realtime_text:
                logger.info(f"开始转写录音文件: {file_path}")
                window.update_status("正在转写...")
                
                # 进行完整转写
                result = engine.transcribe(
                    audio_file=file_path,
                    language=selected_language,
                    target_language=target_language
                )
                
                if result:
                    # 更新UI显示转写结果
                    window.update_result(result)
                    window.update_status("转写完成")
                    
                    # 播放提示音
                    play_notification_sound()
                else:
                    window.update_status("转写未能得到结果")
            else:
                # 实时模式已有结果
                window.update_status("实时转写完成")
                
                # 播放提示音
                play_notification_sound()
        else:
            logger.error("录音文件保存失败或不存在")
            window.update_status("录音保存失败，请重试")
            
    except Exception as e:
        logger.error(f"录音转写过程中出错: {e}")
        logger.exception(e)
        window.update_status(f"处理过程中出错: {str(e)}")
    finally:
        # 恢复UI状态
        window.update_recording_state(False)
        window.update_audio_level(0)
        logger.debug("录音循环结束")

def on_toggle_recording(window, engine, recorder):
    """处理录音按钮点击事件"""
    # 如果当前正在录音，则停止录音
    if window.is_recording:
        logger.debug("停止录音")
        window.update_status("正在停止录音...")
        window.is_recording = False
        window.update_recording_state(False)
        
        # 如果有正在运行的录音线程，等待其结束
        if hasattr(window, "_recording_thread") and window._recording_thread and window._recording_thread.is_alive():
            # 这里不需要做什么，线程会自行检测录音状态并退出
            pass
            
        return
        
    # 开始新的录音
    device_id = window.get_selected_device_id()
    if device_id is None:
        logger.error("没有选择输入设备")
        window.update_status("错误: 没有选择输入设备")
        return
        
    # 获取语言设置
    language = window.get_selected_language()
    target_language = window.get_target_language()
    mode = window.transcription_mode
    
    logger.debug(f"开始录音，使用设备ID: {device_id}, 语言: {language}, 目标语言: {target_language}, 模式: {mode}")
    
    # 确保模型已加载
    try:
        # 先检查模型是否已加载
        if engine.model is None:
            logger.info("模型尚未加载，正在加载...")
            window.update_status("正在加载模型...")
            
        engine.ensure_model_loaded()
        logger.info(f"使用模型: {engine.model_name}")
    except Exception as e:
        logger.error(f"加载模型失败: {e}")
        window.update_status(f"加载模型失败: {str(e)}")
        return
        
    # 显式设置录音设备
    try:
        # 确保设备初始化
        if recorder.device_index != device_id:
            logger.info(f"设置录音设备: {device_id}")
            
        recorder.set_device(device_id)
        logger.info(f"已设置录音设备: {device_id}")
    except Exception as e:
        logger.error(f"设置录音设备失败: {e}")
        window.update_status(f"设置录音设备失败: {str(e)}")
        return
        
    # 设置录音状态
    window.is_recording = True
    window.update_recording_state(True)
    window.update_status("录音中...")
    
    # 使用线程进行录音和转写
    window._recording_thread = threading.Thread(
        target=run_recording_loop, 
        args=(window, engine, recorder)
    )
    window._recording_thread.daemon = True
    window._recording_thread.start()
    
    # 确保线程成功启动
    time.sleep(0.1)
    if not window._recording_thread.is_alive():
        logger.error("录音线程启动失败")
        window.is_recording = False
        window.update_recording_state(False)
        window.update_status("录音线程启动失败")
        return
        
    logger.info("录音线程启动成功")

def on_model_change(window, engine, model_name):
    """处理模型变更事件"""
    # 检查是否正在录音
    if window.is_recording:
        logger.warning("无法在录音过程中更改模型")
        window.update_status("请先停止录音，然后再更改模型")
        return
        
    logger.info(f"切换到模型: {model_name}")
    window.update_status(f"正在切换到模型: {model_name}...")
    
    # 重置引擎状态
    engine.model = None
    engine.initialized = False
    
    # 强制设置模型名称
    engine.settings = {
        "model_name": model_name,
        "device": "cpu",
        "compute_type": "int8",
        "beam_size": 5,
        "threads": min(os.cpu_count(), 8)  # 使用多线程
    }
    
    try:
        # 显示正在加载的提示
        window.update_status(f"正在加载模型 {model_name}...")
        logger.info(f"开始加载模型: {model_name}")
        
        # 重新加载模型
        engine.ensure_model_loaded()
        
        window.update_status(f"已切换到模型: {model_name}")
        logger.info(f"模型切换成功: {model_name}")
    except Exception as e:
        logger.error(f"切换模型失败: {e}")
        window.update_status(f"切换模型失败: {str(e)}")

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
    
    # 导入组件
    try:
        from core.engine import WhisperEngine
        from core.recorder import AudioRecorder
        
        # 初始化语音引擎
        engine = WhisperEngine(config)
        
        # 初始化录音器
        recorder = AudioRecorder()
        
        # 设置回调
        def setup_callbacks(window):
            window.on_toggle_recording = lambda: on_toggle_recording(window, engine, recorder)
            # 连接信号到回调函数
            window.toggle_recording_signal.connect(lambda: on_toggle_recording(window, engine, recorder))
            # 连接设备变更信号
            window.device_changed.connect(recorder.set_device)
            # 连接模式切换信号
            window.transcription_mode_changed.connect(lambda mode: logger.info(f"转写模式已切换为: {mode}"))
            # 连接模型变更信号
            window.model_changed.connect(lambda model: on_model_change(window, engine, model))
        
        # 运行GUI应用
        from PySide6.QtWidgets import QApplication
        from ui.floating_window import FloatingWindow
        
        app = QApplication([])
        
        # 设置MacOS Dock图标
        if sys.platform == "darwin":
            try:
                from ui.macos_app_icon import register_dock_icon
                register_dock_icon(app)
            except Exception as e:
                logger.error(f"设置MacOS Dock图标失败: {e}")
        
        window = FloatingWindow(config)
        setup_callbacks(window)
        window.show()
        
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