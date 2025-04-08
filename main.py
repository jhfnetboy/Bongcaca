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

def run_recording_loop(window, engine, recorder, max_duration=300):
    """录音循环，处理音频录制和转写"""
    logger.debug("开始录音循环")
    
    try:
        # 根据选择的模式启动录音
        if window.transcription_mode == "realtime":
            # 实时模式 - 使用回调函数
            logger.debug("使用实时转写模式")
            last_transcription = ""  # 保存上次的转写结果
            last_update_time = time.time()  # 上次更新UI的时间
            
            def realtime_callback(audio_chunk, level):
                nonlocal last_transcription, last_update_time
                # 添加音频块到引擎缓冲区
                engine.add_audio_chunk(audio_chunk)
                
                # 更新UI音频电平
                window.update_audio_level(level)
                
                # 获取实时转写结果
                current_time = time.time()
                # 确保至少每1秒尝试一次转写，避免过于频繁
                if current_time - last_update_time >= 1.0:
                    result = engine.get_realtime_transcription()
                    if result and result != last_transcription:
                        window.update_result(result)
                        window.update_status(f"实时转写中... ({len(engine.buffer)} 个块)")
                        last_transcription = result
                        last_update_time = current_time
                        # 清除过旧的缓冲区数据，只保留最近的数据，减轻处理负担
                        if len(engine.buffer) > 20:  # 保留约10秒的音频
                            engine.buffer = engine.buffer[-20:]
                            engine.buffer_size = sum(len(chunk) for chunk in engine.buffer)
                            logger.debug(f"裁剪音频缓冲区至 {engine.buffer_size} 字节")
            
            logger.debug("启动音频录制器(实时模式)")
            recorder.start_recording(
                device_index=recorder.device_index, 
                realtime_mode=True, 
                realtime_callback=realtime_callback
            )
        else:
            # 批量模式 - 标准录音
            logger.debug("使用批量转写模式")
            logger.debug("启动音频录制器(批量模式)")
            recorder.start_recording(device_index=recorder.device_index)
        
        start_time = time.time()
        window.update_status("正在录音...")
        
        # 录音循环
        while window.is_recording and (time.time() - start_time) < max_duration:
            try:
                # 更新音频电平 (仅批量模式需要，实时模式在回调中处理)
                if window.transcription_mode == "batch":
                    level = recorder.get_audio_level()
                    window.update_audio_level(level)
                    
                    # 记录日志（降低频率以避免日志过多）
                    if int(time.time()) % 5 == 0:
                        logger.debug(f"当前音频电平: {level:.2f}")
                
                # 短暂休眠
                time.sleep(0.05)
            except Exception as e:
                logger.error(f"录音循环中发生错误: {e}")
                window.update_status(f"录音错误: {str(e)}")
                break
        
        # 检查是否因超时而停止
        if (time.time() - start_time) >= max_duration:
            logger.info("录音达到最大时间限制，自动停止")
            window.update_status("录音时间达到限制，已停止")
            window.toggle_recording()  # 更新UI状态
            return
        
        # 停止录音并获取文件
        logger.debug("停止音频录制器")
        audio_file = recorder.stop()
        
        # 在批量模式下进行文件转写
        if window.transcription_mode == "batch" and audio_file and os.path.exists(audio_file):
            logger.info(f"录音文件保存到: {audio_file}")
            window.update_status("转写中...")
            
            # 转写音频
            try:
                logger.debug(f"开始转写音频文件: {audio_file}")
                result = engine.transcribe(audio_file)
                
                if not result or not result.strip():
                    logger.warning("转写结果为空")
                    window.update_status("转写完成，但结果为空")
                    return
                
                logger.info(f"转写结果: {result}")
                window.update_result(result)
                window.update_status("转写完成")
            except Exception as e:
                logger.error(f"转写音频失败: {e}")
                window.update_status(f"转写失败: {str(e)}")
    except Exception as e:
        logger.error(f"录音过程中发生错误: {e}")
        window.update_status(f"录音失败: {str(e)}")
    finally:
        # 确保录音已停止
        try:
            if hasattr(recorder, 'stop') and recorder.is_recording:
                recorder.stop()
        except Exception as e:
            logger.error(f"停止录音时发生错误: {e}")

def on_toggle_recording(window, engine, recorder):
    """处理开始/停止录音按钮事件"""
    if window.is_recording:
        logger.debug("停止录音")
        window.is_recording = False
        window.update_recording_state(False)  # 更新UI状态为停止
        window.update_status("停止中...")
        # 录音线程会自行结束
    else:
        # 检查是否有输入设备
        device_id = window.get_selected_device_id()
        if device_id is None:
            logger.error("没有选择输入设备")
            window.update_status("错误: 没有选择输入设备")
            return
        
        logger.debug(f"开始录音，使用设备ID: {device_id}")
        
        # 确保录音前引擎已加载
        try:
            engine.ensure_model_loaded()
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            window.update_status(f"错误: 无法加载模型 - {str(e)}")
            return
        
        # 设置录音设备
        try:
            recorder.set_device(device_id)
        except Exception as e:
            logger.error(f"设置录音设备失败: {e}")
            window.update_status(f"错误: 无法设置录音设备 - {str(e)}")
            return
        
        # 清空实时转写缓冲区
        if window.transcription_mode == "realtime":
            engine.clear_buffer()
        
        # 更新UI状态
        window.is_recording = True
        window.update_recording_state(True)  # 更新UI状态为录音
        window.update_status("准备录音...")
        
        # 在单独的线程中运行录音过程
        threading.Thread(
            target=run_recording_loop, 
            args=(window, engine, recorder),
            daemon=True
        ).start()

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